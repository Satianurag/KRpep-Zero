# KRAS G12D target and observed pocket

The 1–169 construct matches author chain A of [PDB 5XCO](https://www.rcsb.org/structure/5XCO), a 1.25 Å GDP-state crystal complex. All 169 residues have coordinates. Relative to [UniProt P01116-2 (KRAS4B)](https://www.uniprot.org/uniprotkb/P01116/entry), the sole difference in this interval is G12D. Residues 13 and 61 are G and Q. The deposited expression sequence also contains an N-terminal GS tag; observed Ser0 is excluded from the target. GDP is retained in the reference coordinate file. A FASTA alone does not encode nucleotide state.

Isoform QC caught a real mismatch: the displayed P01116 sequence is KRAS4A and differs from 5XCO at 151,153,165,166,167,168 in addition to G12D. Both the mutant and WT counter-screen therefore use KRAS4B. The first failed comparison and corrected rerun are preserved in the logs; no target was silently substituted.

Accession correction: P01116 = KRAS, P01111 = NRAS, P01112 = HRAS. The original requested HRAS/NRAS ordering was reversed.

Contacts below are recalculated from the asymmetric unit, using minimum non-hydrogen atom distance from target A1–169 to peptide B0–20, including acetyl and amide caps. Alternate conformer A/blank and positive occupancy only; waters and symmetry mates are excluded. The 4 Å set is a geometric pocket definition, not an energy or binding-affinity calculation. The 5 Å shell is reported for cutoff sensitivity. Water-mediated interactions described in the paper need not occur in the 4 Å direct-contact set.

| Target residue | Minimum distance (Å) | Within 4 Å | Peptide author positions within 5 Å |
|---|---:|:---:|---|
| V9 | 4.027 | no | 7 |
| T58 | 3.992 | yes | 7 |
| Q61 | 2.756 | yes | 6, 7, 8 |
| E62 | 2.697 | yes | 1, 8 |
| E63 | 3.661 | yes | 8 |
| Y64 | 3.788 | yes | 8, 10 |
| R68 | 2.878 | yes | 7, 8, 9 |
| D69 | 2.561 | yes | 8, 9, 10, 11 |
| M72 | 3.239 | yes | 7, 9, 11 |
| R73 | 3.197 | yes | 10, 11 |
| H95 | 3.436 | yes | 3, 4, 6 |
| Y96 | 3.608 | yes | 6, 7 |
| Q99 | 2.846 | yes | 4, 5, 6, 7, 9, 12, 15 |
| R102 | 2.797 | yes | 4, 5, 12, 14 |
| V103 | 3.656 | yes | 9, 11, 12 |

The reference inhibitor is full-length KRpep-2d, 19 residues with a Cys5–Cys15 disulfide and acetylated/amidated termini. Position 12 in the peptide is Asp; it must not be confused with KRAS Asp12. Native 5XCO is the experimental reference, not a predicted design. Atom-pair distances are in `results/target/contacts.csv`; target checks and contact definitions are in `target-qc.json`.

Reference: Sogabe et al., PMID 28740607, DOI [10.1021/acsmedchemlett.7b00128](https://doi.org/10.1021/acsmedchemlett.7b00128). Source URLs, timestamps and SHA-256 hashes: `results/target/source-receipts.json`.
