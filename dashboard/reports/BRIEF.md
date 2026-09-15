# KRpep-Zero evidence brief

Evidence checked 14 September 2026. This campaign concerns computational peptide design around a GDP-state KRAS G12D reference, not a demonstrated therapeutic.

## Experimental reference and controls

KRpep-2d is **Ac-RRRRCPLYISYDPVCRRRR-NH2**, a 19-residue peptide with a **Cys5–Cys15 disulfide**, N-acetylation and C-terminal amidation. The 1.25 Å structure [5XCO](https://www.rcsb.org/structure/5XCO) places it in the shallow Switch-II/α3-adjacent cleft. These termini and disulfide must be preserved in a valid positive control; a generic head-to-tail cyclic sequence would represent a different molecule. [Sogabe et al., PMID 28740607; DOI 10.1021/acsmedchemlett.7b00128](https://doi.org/10.1021/acsmedchemlett.7b00128).

| Assay | G12D | WT | WT/G12D ratio |
|---|---:|---:|---:|
| SPR KD, GDP state | 8.9 nM | 58 nM | 6.52 |
| SPR KD, GTP state | 11 nM | 200 nM | 18.18 |

Ratios are arithmetic from the crystal paper's Table 1, not new experimental measurements. Its GDP-state G12C KD is 35 nM. Exchange-inhibition IC50 **1.6 nM** comes from a different assay and must not be relabeled as affinity. The precursor KRpep-2 has fewer terminal arginines and different values; its KD 51 nM/IC50 8.9 nM must not be assigned to KRpep-2d. [Original discovery, PMID 28153726; DOI 10.1016/j.bbrc.2017.01.147](https://doi.org/10.1016/j.bbrc.2017.01.147); [crystal SPR table](https://pmc.ncbi.nlm.nih.gov/articles/PMC5512123/table/tbl1/).

KS-58 is a chemically distinct bicyclic derivative with noncanonical residues and a thioether linker. Its stated sequence is `c[βAla-Pro-Nle-c(Cys-Anon-Ser-4fF-Asp-Pro-Trp-D-Cys)]`, with backbone closure and a propylene bridge between Cys4 and D-Cys11. Anon denotes (S)-2-aminononanoic acid. It is a useful design precedent but cannot be represented faithfully by an ordinary 20-letter FASTA or treated as the 5XCO crystallized ligand. [Sakamoto et al., PMID 33303890; DOI 10.1038/s41598-020-78712-5](https://doi.org/10.1038/s41598-020-78712-5).

Published cellular interpretations conflict. The original reports describe cellular effects, whereas a later study found no KRpep-2d cellular signaling effect under its conditions, investigated disulfide/proteolytic instability, and developed better-controlled analogues. It also questioned the depth of KS-58 cellular target-engagement evidence and reported a mast-cell degranulation liability in arginine-rich analogues. Those findings motivate cautious developability triage; they establish no activity or toxicity for our ungenerated candidates. [Lim et al., PMID 35024121; DOI 10.1039/d1sc05187c](https://doi.org/10.1039/d1sc05187c).

## Clinical context

| Program | Scope | Registry observation |
|---|---|---|
| Zoldonrasib / RMC-9805 | KRAS G12D RAS(ON)-selective | NCT06040541 Recruiting; updated 3 June 2026 |
| Daraxonrasib / RMC-6236 | RAS(ON) multi-selective | Phase 3 RASolute 302, NCT06625320 Active, not recruiting; updated 2 June 2026 |
| MRTX1133 | KRAS G12D program | NCT05737706 Terminated; updated 6 April 2025; formulation challenges, before Phase 2 |

These are registry states observed at retrieval, not forecasts. [NCT06040541](https://clinicaltrials.gov/study/NCT06040541), [NCT06625320](https://clinicaltrials.gov/study/NCT06625320), [NCT05737706](https://clinicaltrials.gov/study/NCT05737706). Detailed checks and sponsor sources are in [clinical-brief.md](results/clinical-brief.md). The different nucleotide-state/mechanistic contexts preclude assuming our GDP-pocket peptides reproduce a clinical inhibitor's behavior.

## Consequences for the campaign

- Use KRAS4B 1–169, matching 5XCO; the displayed UniProt KRAS4A sequence has additional differences within that interval. Exact coordinate checks and contact cutoff definitions are in [POCKET.md](POCKET.md).
- Preserve 19-residue KRpep-2d chemistry despite the 12–16-residue design range. Scrambling produces a proposed negative control, not an experimentally confirmed nonbinder.
- ESM is a sequence-model diagnostic. It does not measure this pocket's ligand affinity. Positions 12/13/61 are annotated and scored; no hotspot ranking will be forced to fit an expectation.
- Co-fold confidence and pose recovery support structural hypotheses only. Affinity, mutant selectivity, cellular activity and drug efficacy require appropriate experimental evidence.

Raw source captures and native PubMed outputs are in `results/sources/`; command receipts are in `results/logs/`. Expanded chemistry and contradictory evidence: [control-evidence.md](results/control-evidence.md). Schema and budget audit: [method-audit.md](results/method-audit.md).
