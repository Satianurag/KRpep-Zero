"""Render publication-style static figures from observed RAS campaign outputs."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='KRpep-Zero'
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from Bio import SeqIO


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results" / "target"
OUT = ROOT / "results" / "figures"
NAVY = "#102A43"
OFFWHITE = "#F7F4EE"
TEAL = "#1F9D8B"
MAGENTA = "#C4458A"
GOLD = "#D59B2A"
GRID = "#B8C7D1"


def save_figure(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=180, facecolor=OFFWHITE, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.svg", facecolor=OFFWHITE, bbox_inches="tight",metadata={'Date':None})
    plt.close(fig)


def contact_matrix() -> None:
    values: dict[tuple[int, int], float] = {}
    residues: dict[int, str] = {}
    peptide_names: dict[int, str] = {}
    with (TARGET / "contacts.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            target = int(row["target_residue"])
            peptide = int(row["peptide_residue"])
            distance = float(row["min_distance_A"])
            residues[target] = row["target_name"]
            peptide_names[peptide] = row["peptide_name"]
            values[(target, peptide)] = min(distance, values.get((target, peptide), distance))

    matrix = [[float("nan") for _ in range(19)] for _ in range(169)]
    for (target, peptide), distance in values.items():
        if 1 <= target <= 169 and 1 <= peptide <= 19:
            matrix[target - 1][peptide - 1] = distance

    fig, ax = plt.subplots(figsize=(16, 10), facecolor=OFFWHITE)
    ax.set_facecolor(OFFWHITE)
    image = ax.imshow(matrix, aspect="auto", origin="upper", cmap="magma_r", vmin=2.0, vmax=5.0, interpolation="none")
    image.cmap.set_bad(OFFWHITE)
    ax.set_xlabel("KRpep-2d peptide position (position 12 is peptide residue, distinct from KRAS G12)", color=NAVY, labelpad=12)
    ax.set_ylabel("5XCO target residue position", color=NAVY, labelpad=12)
    ax.set_xticks(range(19), [str(i) for i in range(1, 20)])
    ax.set_yticks(range(0, 169, 10), [str(i) for i in range(1, 170, 10)])
    ax.tick_params(colors=NAVY, length=0)
    ax.grid(color=GRID, linewidth=0.3, alpha=0.25)
    for position, label in ((12, "peptide 12"),):
        ax.axvline(position - 1, color=GOLD, linewidth=1.4, alpha=0.9)
        ax.annotate(label, xy=(position - 1, -1), xytext=(position - 1, -9), ha="center", va="bottom", color=GOLD, fontsize=9, fontweight="bold")
    for position in (12, 13, 61):
        ax.axhline(position - 1, color=MAGENTA, linewidth=0.9, alpha=0.65)
    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("minimum heavy atom distance (Å), observed pairs ≤5 Å", color=NAVY)
    cbar.ax.tick_params(colors=NAVY)
    ax.set_title("Observed KRpep-2d contacts in the 5XCO asymmetric unit", loc="left", color=NAVY, fontsize=16, fontweight="bold", pad=28)
    ax.text(0, 1.015, "Target A1–169 × peptide B1–19 · direct non-hydrogen atom distances", transform=ax.transAxes, color=TEAL, fontsize=10, va="bottom")
    ax.text(0, -0.12, "Source: PDB 5XCO observed crystal contacts; blank cells indicate no observed atom pair within 5 Å. Geometry is not an affinity score.", transform=ax.transAxes, color=NAVY, fontsize=9, va="top")
    for spine in ax.spines.values():
        spine.set_color(NAVY)
    save_figure(fig, "contacts")


def alignment_heatmap() -> None:
    records = list(SeqIO.parse(TARGET / "ras-aligned.fasta", "fasta"))
    names = [record.id.split("|")[0] for record in records]
    sequences = {name: str(record.seq) for name, record in zip(names, records)}
    reference = sequences["P01116-2"]
    source_to_column: dict[int, int] = {}
    position = 0
    for column, residue in enumerate(reference):
        if residue != "-":
            position += 1
            if position <= 169:
                source_to_column[position] = column
    positions = list(range(1, 170))
    matrix = []
    for name in names:
        row = []
        for source_position in positions:
            residue = sequences[name][source_to_column[source_position]]
            row.append(0 if residue == reference[source_to_column[source_position]] else (2 if residue == "-" else 1))
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(25, 4.8), facecolor=OFFWHITE)
    ax.set_facecolor(OFFWHITE)
    cmap = ListedColormap([OFFWHITE, MAGENTA, NAVY])
    ax.imshow(matrix, aspect="auto", interpolation="none", cmap=cmap, vmin=0, vmax=2)
    for row_index, name in enumerate(names):
        for column_index, source_position in enumerate(positions):
            residue = sequences[name][source_to_column[source_position]]
            if residue != reference[source_to_column[source_position]] or source_position in (12, 13, 61):
                ax.text(column_index, row_index, residue, ha="center", va="center", fontsize=6.2, color=NAVY if residue != "-" else MAGENTA, fontweight="bold")
    ax.set_yticks(range(len(names)), ["KRAS4A (P01116)", "NRAS (P01111)", "HRAS (P01112)", "KRAS4B (P01116-2)"])
    ax.set_xticks([i - 1 for i in range(10, 170, 10)], [str(i) for i in range(10, 170, 10)])
    ax.set_xlabel("Source position anchored to KRAS4B P01116-2", color=NAVY, labelpad=10)
    ax.tick_params(axis="both", colors=NAVY, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.3, alpha=0.45)
    for position, label in ((12, "G12"), (13, "G13"), (61, "Q61")):
        column = position - 1
        ax.axvspan(column - 0.48, column + 0.48, color=TEAL, alpha=0.22, zorder=0)
        ax.annotate(label, xy=(column, -0.52), xytext=(column, -1.2), ha="center", va="bottom", color=TEAL, fontsize=9, fontweight="bold", arrowprops={"arrowstyle": "-", "color": TEAL, "lw": 0.8})
    differences = [151, 153, 165, 166, 167, 168]
    for position in differences:
        column = position - 1
        ax.axvspan(column - 0.48, column + 0.48, color=MAGENTA, alpha=0.16, zorder=0)
    ax.annotate("KRAS4A differences within 5XCO 1–169", xy=(166, -0.04), xycoords=("data", "axes fraction"), xytext=(158, 1.32), textcoords=("data", "axes fraction"), ha="center", color=MAGENTA, fontsize=9, fontweight="bold", arrowprops={"arrowstyle": "-", "color": MAGENTA, "lw": 0.8})
    ax.set_title("Human RAS sequence alignment, positions 1–169", loc="left", color=NAVY, fontsize=16, fontweight="bold", pad=38)
    ax.text(0, 1.17, "Center-star global alignment · BLOSUM62 · affine gaps −10/−0.5 · hotspot annotations anchored to KRAS4B", transform=ax.transAxes, color=TEAL, fontsize=10, va="bottom")
    legend = [Patch(facecolor=OFFWHITE, edgecolor=NAVY, label="same as KRAS4B"), Patch(facecolor=MAGENTA, label="isoform residue difference"), Patch(facecolor=NAVY, label="gap / missing column")]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0, -0.24), ncol=3, frameon=False, labelcolor=NAVY)
    ax.text(0, -0.40, "Source: UniProt canonical P01116/P01111/P01112 JSON plus P01116-2 FASTA. 5XCO observed construct is KRAS4B 1–169 (GDP state).", transform=ax.transAxes, color=NAVY, fontsize=9, va="top")
    for spine in ax.spines.values():
        spine.set_color(NAVY)
    save_figure(fig, "alignment")


def main() -> None:
    contact_matrix()
    alignment_heatmap()
    print("wrote", OUT / "contacts.png", OUT / "contacts.svg", OUT / "alignment.png", OUT / "alignment.svg")


if __name__ == "__main__":
    main()
