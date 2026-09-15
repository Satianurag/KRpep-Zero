# KRpep-2d control evidence

This note is based only on the supplied offline captures: `results/sources/crystal-full.md`, `ks58-full.md`, `control-caveats-full.md`, and `pubmed-control-abstracts.xml`. Values below preserve the assay type reported by each source.

## KRpep-2d chemistry and crystal SPR

The crystal paper describes KRpep-2d as a **19-mer cyclic peptide**: `Ac-RRRR-CPLYISYDPVC-RRRR-NH2` (linear notation; the Cys5–Cys15 side chains form the intramolecular disulfide). Thus the N terminus is acetylated and the C terminus is amidated. The structure is GDP-bound KRAS G12D at 1.25 Å; the peptide binds an extended cleft near Switch II/α3. The paper separately reports cell-free enzyme inhibition **IC50 = 1.6 nM**.

The crystal paper’s SPR table reports **binding KD**, not IC50:

| KRAS state | ligand | KD (nM) | kon (M−1 s−1) | koff (s−1) | binding t1/2 (s) |
|---|---:|---:|---:|---:|---:|
| G12D | GDP | 8.9 | 1.3 × 10^6 | 1.1 × 10−2 | 61 |
| G12C | GDP | 35 | 1.0 × 10^6 | 3.5 × 10−2 | 20 |
| WT | GDP | 58 | 1.6 × 10^6 | 9.3 × 10−2 | 7.5 |
| G12D | GTP | 11 | 2.8 × 10^6 | 3.0 × 10−2 | 23 |
| G12C | GTP | 250 | 3.7 × 10^5 | 9.2 × 10−2 | 7.5 |
| WT | GTP | 200 | 6.1 × 10^5 | 1.2 × 10−1 | 5.8 |

Source: Sogabe et al., ACS Med Chem Lett 2017, DOI [10.1021/acsmedchemlett.7b00128](https://doi.org/10.1021/acsmedchemlett.7b00128), PMID [28740607](https://pubmed.ncbi.nlm.nih.gov/28740607/), PMC [5512123](https://pmc.ncbi.nlm.nih.gov/articles/PMC5512123/).

## KS-58 sequence, stereochemistry, and linker

The KS-58 paper gives the bicyclic structure as `c[βAla-Pro-Nle-c(Cys-Anon-Ser-4fF-Asp-Pro-Trp-D-Cys)]`, with main-chain amide cyclization and a thioether bridge joining Cys4 and D-Cys11 through **DIP**, i.e. 1,3-diiodopropane; the stated bridge is `Cα4–CH2–S–CH2–CH2–CH2–S–CH2–Cα11`. The paper’s glossary makes **Anon = (S)-2-aminononanoic acid**, Nle = L-norleucine, βAla = beta-alanine, D-Cys = D-cysteine, and 4fF = 4-fluoro-L-phenylalanine. Table 2 is a cell-activity table and does not itself establish additional stereochemistry beyond the sequence labels; no extra stereochemical assignments are inferred here.

At 30 µM, Table 2 reports KS-58 cell proliferation remaining 21.1 ± 5.5% (A427, KRAS G12D) and 50.1 ± 4.1% (PANC-1, KRAS G12D), with pERK 26.0 ± 6.0% and 57.6 ± 7.6%, respectively. Non-G12D lines were less affected: A549 G12S 81.3%, H1975 WT 92.7%, MIA PaCa-2 G12C 86.8%, Capan-1 G12V 94.9%.

Source: Sakamoto et al., Scientific Reports 2020, DOI [10.1038/s41598-020-78712-5](https://doi.org/10.1038/s41598-020-78712-5), PMID [33303890](https://pubmed.ncbi.nlm.nih.gov/33303890/), PMC [7730438](https://pmc.ncbi.nlm.nih.gov/articles/PMC7730438/).

## Conflicting cellular-activity evidence

The original KRpep-2d report and KS-58 report describe selective cellular effects, but the later Chemical Science study (PMC8672774) reports a key discrepancy: in its hands, KRpep-2d had no effect on cellular KRAS signaling and a very short cell-homogenate half-life, consistent with intracellular reduction of its disulfide. That study engineered redox-stable analogues; MP-3995 inhibited pERK/proliferation across KRAS G12D, G12V, and G12C lines, while a non-binding all-D control was minimally active, A375 (BRAF V600E, KRAS-independent) was inactive, and target engagement was supported by CETSA and reporter displacement. It also flags that KS-58 was tested for proliferation at only one relatively high concentration (30 µM), with no reported cell-permeability or cellular-target-engagement evidence and an in vivo control xenograft-growth pattern it considered difficult to interpret. This is a methodological conflict/context, not proof that the KS-58 findings are false.

The same study found arginine-rich analogues triggered rat mast-cell degranulation; reducing arginine count reduced this liability but also reduced permeability and cellular activity. Its conclusion supports retaining KS-58 as a useful template while treating its cellular and in vivo claims as less rigorously controlled than the later analog series.

Source: Lim et al., Chemical Science 2021, DOI [10.1039/d1sc05187c](https://doi.org/10.1039/d1sc05187c), PMC [8672774](https://pmc.ncbi.nlm.nih.gov/articles/PMC8672774/). The supplied PubMed XML independently identifies KRpep-2 as PMID [28153726](https://pubmed.ncbi.nlm.nih.gov/28153726/) (DOI [10.1016/j.bbrc.2017.01.147](https://doi.org/10.1016/j.bbrc.2017.01.147)) and the KRpep-2d cysteine-bridging study as PMID [28457754](https://pubmed.ncbi.nlm.nih.gov/28457754/) (DOI [10.1016/j.bmcl.2017.04.063](https://doi.org/10.1016/j.bmcl.2017.04.063)).

## Interpretation guardrail

Do not call the 8.9 nM crystal-paper value an IC50: it is the SPR KD for KRpep-2d binding to GDP-bound KRAS G12D. The 1.6 nM value is the separate cell-free enzyme IC50. Also, “subnanomolar KD” appears in later KS-58 background prose but conflicts with the crystal paper’s explicit SPR table; this note uses the table values and does not repeat the unsupported subnanomolar claim.
