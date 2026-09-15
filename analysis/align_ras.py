"""Reproducibly align the canonical human RAS sequences used by this project.

The alignment is a center-star global alignment.  Pairwise alignments use
Biopython's PairwiseAligner with BLOSUM62 and explicit affine gap penalties;
the center is selected by the largest sum of pairwise scores.  The script
does not infer or hand-place residue positions.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path

from Bio import Align, SeqIO, __version__ as biopython_version
from Bio.Align import substitution_matrices


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results" / "target"
ACCESSIONS = ("P01116", "P01111", "P01112", "P01116-2")
NAMES = {
    "P01116": "KRAS4A",
    "P01116-2": "KRAS4B",
    "P01111": "NRAS",
    "P01112": "HRAS",
}
HOTSPOTS = (12, 13, 61)


def read_sequences() -> dict[str, str]:
    sequences: dict[str, str] = {}
    for accession in ACCESSIONS[:3]:
        record = json.loads((TARGET / f"{accession}.json").read_text())
        sequence = record["sequence"]["value"].replace(" ", "").replace("\n", "")
        if not sequence or any(ch == "-" for ch in sequence):
            raise ValueError(f"invalid ungapped sequence in {accession}.json")
        sequences[accession] = sequence
    fasta = SeqIO.read(TARGET / "P01116-2.fasta", "fasta")
    sequence = str(fasta.seq).upper().replace(" ", "").replace("\n", "")
    if not sequence or "-" in sequence:
        raise ValueError("invalid ungapped sequence in P01116-2.fasta")
    sequences["P01116-2"] = sequence
    return sequences


def make_aligner() -> Align.PairwiseAligner:
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -10.0
    aligner.extend_gap_score = -0.5
    # Make all affine gap modes explicit, including terminal gaps.
    aligner.target_open_gap_score = -10.0
    aligner.target_extend_gap_score = -0.5
    aligner.query_open_gap_score = -10.0
    aligner.query_extend_gap_score = -0.5
    return aligner


def pairwise_strings(aligner: Align.PairwiseAligner, center: str, query: str) -> tuple[str, str, float]:
    alignment = aligner.align(center, query)[0]
    return str(alignment[0]), str(alignment[1]), float(alignment.score)


def center_star(sequences: dict[str, str], aligner: Align.PairwiseAligner) -> tuple[str, dict[str, str], dict[str, float]]:
    pairwise_scores: dict[str, dict[str, float]] = {key: {} for key in sequences}
    for left in sequences:
        for right in sequences:
            if right not in pairwise_scores[left]:
                pairwise_scores[left][right] = pairwise_strings(aligner, sequences[left], sequences[right])[2]
    center = max(sequences, key=lambda key: (sum(pairwise_scores[key].values()), key))

    # For every residue in the center, retain the query's insertion string
    # before it; the final insertion is stored under len(center).
    pieces: dict[str, tuple[list[str], list[str]]] = {}
    for key, sequence in sequences.items():
        if key == center:
            aligned_center, aligned_query = sequences[center], sequences[center]
        else:
            aligned_center, aligned_query, _ = pairwise_strings(aligner, sequences[center], sequence)
        before = [""] * (len(sequences[center]) + 1)
        residues = [""] * len(sequences[center])
        center_position = 0
        for center_char, query_char in zip(aligned_center, aligned_query):
            if center_char == "-":
                before[center_position] += query_char
            else:
                if center_position >= len(residues):
                    raise ValueError("pairwise alignment advanced beyond center sequence")
                residues[center_position] = query_char
                center_position += 1
        if center_position != len(residues) or any(not residue for residue in residues):
            raise ValueError("pairwise alignment did not cover center sequence")
        pieces[key] = (before, residues)

    columns: list[str] = []
    for slot in range(len(sequences[center]) + 1):
        width = max(len(pieces[key][0][slot]) for key in sequences)
        for offset in range(width):
            columns.append("".join(
                pieces[key][0][slot][offset] if offset < len(pieces[key][0][slot]) else "-"
                for key in sequences
            ))
        if slot < len(sequences[center]):
            columns.append("".join(pieces[key][1][slot] for key in sequences))

    aligned: dict[str, str] = {key: "" for key in sequences}
    for column in columns:
        for index, key in enumerate(sequences):
            aligned[key] += column[index]
    return center, aligned, {key: sum(pairwise_scores[key].values()) for key in sequences}


def residue_map(aligned: str, positions: tuple[int, ...]) -> dict[int, tuple[int, str]]:
    mapping: dict[int, tuple[int, str]] = {}
    ungapped_position = 0
    for alignment_column, residue in enumerate(aligned, start=1):
        if residue != "-":
            ungapped_position += 1
            if ungapped_position in positions:
                mapping[ungapped_position] = (alignment_column, residue)
    return mapping


def main() -> None:
    sequences = read_sequences()
    aligner = make_aligner()
    center, aligned, center_scores = center_star(sequences, aligner)
    lengths = {len(sequence) for sequence in aligned.values()}
    if len(lengths) != 1:
        raise ValueError("merged alignment has inconsistent lengths")
    for accession in ACCESSIONS:
        if aligned[accession].replace("-", "") != sequences[accession]:
            raise ValueError(f"alignment changed ungapped sequence for {accession}")

    alignment_path = TARGET / "ras-aligned.fasta"
    with alignment_path.open("w") as handle:
        for accession in ACCESSIONS:
            handle.write(f">{accession}|{NAMES[accession]}\n")
            sequence = aligned[accession]
            for start in range(0, len(sequence), 80):
                handle.write(sequence[start : start + 80] + "\n")

    mapping_path = TARGET / "alignment-mapping.csv"
    with mapping_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["accession", "protein", "source_position", "expected_residue", "observed_residue", "alignment_column"])
        writer.writeheader()
        for accession in ACCESSIONS:
            mapping = residue_map(aligned[accession], HOTSPOTS)
            for position in HOTSPOTS:
                column, residue = mapping[position]
                writer.writerow({
                    "accession": accession,
                    "protein": NAMES[accession],
                    "source_position": position,
                    "expected_residue": {12: "G", 13: "G", 61: "Q"}[position],
                    "observed_residue": residue,
                    "alignment_column": column,
                })

    summary = {
        "sequences": {
            accession: {
                "protein": NAMES[accession],
                "source": f"results/target/{accession}.json" if accession != "P01116-2" else "results/target/P01116-2.fasta",
                "length": len(sequences[accession]),
                "sha256": hashlib.sha256(sequences[accession].encode()).hexdigest(),
            }
            for accession in ACCESSIONS
        },
        "alignment": {
            "algorithm": "center-star global pairwise protein alignment",
            "center_accession": center,
            "alignment_length": len(next(iter(aligned.values()))),
            "pairwise_substitution_matrix": "BLOSUM62",
            "gap_open": -10.0,
            "gap_extend": -0.5,
            "center_score_sums": center_scores,
            "biopython_version": biopython_version,
            "python_version": platform.python_version(),
        },
        "accession_mapping": {
            "P01116": {"gene": "KRAS", "isoform": "KRAS4A", "canonical_json": True},
            "P01111": {"gene": "NRAS", "isoform": "NRAS", "canonical_json": True},
            "P01112": {"gene": "HRAS", "isoform": "HRAS", "canonical_json": True},
            "P01116-2": {"gene": "KRAS", "isoform": "KRAS4B", "canonical_json": False},
        },
        "construct_context": {
            "pdb": "5XCO",
            "construct": "KRAS4B 1-169 (P01116-2)",
            "state": "GDP",
            "variant_vs_P01116-2": "G12D at source position 12",
            "P01116_KRAS4A_differences_within_1_169_vs_KRAS4B": [151, 153, 165, 166, 167, 168],
        },
        "hotspots": {
            str(position): {
                accession: {
                    "protein": NAMES[accession],
                    "source_position": position,
                    "residue": residue_map(aligned[accession], HOTSPOTS)[position][1],
                    "alignment_column": residue_map(aligned[accession], HOTSPOTS)[position][0],
                }
                for accession in ACCESSIONS
            }
            for position in HOTSPOTS
        },
        "outputs": ["results/target/ras-aligned.fasta", "results/target/alignment-mapping.csv"],
    }
    summary_path = TARGET / "ras-alignment-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"alignment": str(alignment_path), "mapping": str(mapping_path), "summary": str(summary_path), "center": center, "alignment_length": len(next(iter(aligned.values())))}, indent=2))


if __name__ == "__main__":
    main()
