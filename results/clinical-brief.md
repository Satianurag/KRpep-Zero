# Clinical landscape brief (checked 2026-09-14 IST)

Scope: primary registry, sponsor, and primary-publication checks for the three named programs. Pages were retrieved with Firecrawl on 2026-09-14 (IST); registry status below is the status shown on the page at retrieval, with the registry's own “Last Update Posted” date.

## Zoldonrasib (RMC-9805)

- **Clinical status:** Active clinical development. ClinicalTrials.gov **NCT06040541** (“Study of RMC-9805 in Participants With KRAS G12D-Mutant Solid Tumors,” Phase 1/1b; monotherapy and RMC-9805 + RMC-6236) was **Recruiting**, last update posted **2026-06-03**. The registry describes RMC-9805 as a selective, orally bioavailable KRAS G12D(ON) inhibitor. URL: https://clinicaltrials.gov/study/NCT06040541
- **NSCLC platform:** **NCT06162221** (“Study of RAS(ON) Inhibitors in Patients With Advanced RAS-mutated NSCLC”) was **Recruiting**, last update posted **2026-06-30**. Its subprotocol D is Phase 2 zoldonrasib monotherapy in previously treated KRAS G12D-mutant NSCLC; subprotocol C evaluates RMC-9805 with/without RMC-6236 plus other therapy. URL: https://clinicaltrials.gov/study/NCT06162221
- **Sponsor primary clinical readout:** Revolution Medicines’ 2025 AACR release calls zoldonrasib a “RAS(ON) G12D-selective inhibitor”; it reports a 2024-12-02 cutoff, 18 efficacy-evaluable NSCLC patients at 1,200 mg QD, ORR 61% (confirmed or pending confirmation), and DCR 89%. These are sponsor-reported early data, not a registrational result. URL: https://ir.revmed.com/news-releases/news-release-details/revolution-medicines-presents-initial-data-zoldonrasib-rmc-9805

## Daraxonrasib (RMC-6236)

- **Mechanism/positioning:** Daraxonrasib is **not G12D-selective**. The sponsor describes it as a RAS(ON) **multi-selective** inhibitor targeting oncogenic G12X, G13X, and Q61X variants. A 2025 Journal of Medicinal Chemistry review in PMC describes activity across mutant and WT KRAS, HRAS, and NRAS isoforms. Sponsor URL: https://ir.revmed.com/news-releases/news-release-details/revolution-medicines-announces-fda-breakthrough-therapy ; primary-publication/review URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12507178/
- **Phase 3 PDAC:** **NCT06625320**, RASolute 302, was **Active, not recruiting** (“No longer looking for participants”), last update posted **2026-06-02**. The registry describes randomized Phase 3 RMC-6236 versus investigator-choice standard of care in previously treated metastatic PDAC. URL: https://clinicaltrials.gov/study/NCT06625320
- **NSCLC platform:** NCT06162221 above includes RMC-6236 in RAS-mutated NSCLC subprotocols and remained **Recruiting** at the 2026-06-30 registry update. The PMC review also points to Phase 3 RASolve 301 **NCT06881784**; that record was not independently scraped in this bounded check, so do not infer its current status here. URL: https://clinicaltrials.gov/study/NCT06881784

## MRTX1133

- **Clinical status independently verified:** **NCT05737706**, “Study of MRTX1133 in Patients With Advanced Solid Tumors Harboring a KRAS G12D Mutation,” sponsor Mirati Therapeutics, was **Terminated**, last update posted **2025-04-06**. The registry gives the reason as **“Formulation challenges”** and states the study was terminated before Phase 2; only Phase 1 was conducted. URL: https://clinicaltrials.gov/study/NCT05737706
- This confirms the supplied attachment’s termination statement at the registry level. Do not confuse this record with **NCT03785249**, which is an adagrasib/MRTX849 KRAS G12C study and is unrelated to MRTX1133.

## Uncertainty and provenance

Registry status is time-sensitive and sponsor-submitted; this brief reports the page state observed on **2026-09-14 IST**, not a forecast. NCT06162221 and NCT06040541 both show “Recruiting” despite last updates in June 2026, while NCT06625320 shows “Active, not recruiting.” The Firecrawl search used for the prior trial-search operation returned no results despite exit code 0; its raw stdout/stderr are at `results/logs/firecrawl-trial-search/` and were not used as evidence.

Raw Firecrawl captures and search outputs are in `results/sources/clinical/`, including the registry captures, sponsor pages, and PMC article. Command receipts are in `results/logs/` under operation names prefixed with the 20260914 date; all were run through `analysis/run_logged.py` with parser options placed before the unique operation name.
