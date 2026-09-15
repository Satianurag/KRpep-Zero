# KRpep-Zero provenance

Campaign record dated 14 September 2026 IST. Proto excluded; use Modal for cloud computation. New paid spend ceiling remains zero. Provider free allowances must be established before chargeable inference/deployment. Wet-lab outputs remain local drafts; do not submit experiments.

Scientific outputs are produced from installed tools, primary sources and recorded coordinate analyses. No affinity, selectivity, score or structure may be invented. Exploratory calculations are distinguished from experimental observations. The original pasted specification is preserved under prompts/.

`results/logs/` contains timestamped operation records, exact nonsecret inputs, exit status, and raw stdout/stderr or provider output. `results/sources/` contains immutable snapshots and source receipts. `results/manifest.json` records file hashes. Earlier setup evidence stays in `setup/` and `preflight/`; synthetic viewer fixtures are not campaign data.

The credential supplied in chat is stored only in the macOS Keychain. Do not export chat transcripts, credential values, account metadata, environment directories or caches to a public repository. Public artifacts require an explicit allowlist.

## Completed scientific operations

- Stage 1: native PubMed retrieval and Firecrawl paper/full-text/registry captures; synthesized in BRIEF.md. Clinical and method research used `gpt-5.6-luna` subagents, with primary-agent corrections before inference.
- Stage 2: official RCSB 5XCO and UniProt snapshots, recorded SHA-256 hashes; geometric contacts via Gemmi. A failed canonical-KRAS comparison identified KRAS4A versus KRAS4B; the resolved target uses P01116-2. Cropped mmCIF entity sequences and label numbering were normalized to remove the GS expression tag, and a binder-free GDP target was produced. Four-sequence global center-star alignment used Biopython 1.88 with BLOSUM62 and affine gap penalties −10/−0.5.
- Stage 3: `modal-esmc-001` completed on one L4, official ESMC300M with code/weights hashes and seed 17 recorded in `results/esm/metadata.json`. Both 169×64 arrays were finite; masked position 12 was identical (maximum raw-logit difference 0). Profile and all 6,422 nonnative substitution rows are retained. Remote function elapsed time was 32.99 s, excluding image preparation. The subsequent account billing snapshot showed $0.02 credits applied and zero billed cost; this is an account snapshot, not a precise per-operation invoice.
- Visualization preview: local 3Dmol.js 2.5.5, verified npm integrity; actual 5XCO coordinate rendering at 1600×1200, contact/alignment/ESMC figures, desktop/mobile checks. Dashboard status does not substitute missing predictions.

## Current execution and fallbacks

The initial compute-budget record listed $200 remaining Modal free credits at setup. Initial ESMC reserve $2; calibration reserve $10. No paid overage is authorized. BoltzGen calibration used two designs, finite runtime, one L4 and no automatic retries. A100 allocation was rejected for lack of a payment method before inference; the L4 route was used. Invocation receipts identify exact arguments and outcomes.

During continuation, the named biological plugin tools and local plugin cache entries were no longer available in this session. Their earlier preflight checks are historical, not evidence of current callability. Official Biohub ESM, BoltzGen and Boltz package routes are the fallbacks; Context7 provided official API documentation for implementation reference. Firecrawl's keyless limit was subsequently reached and logged. NGS and slide-analysis tasks have no supplied experimental data and are not being fabricated merely to exercise those plugins.

Later cheap-subagent turns returned a workspace-credit error; the primary agent continued the work directly. This error is distinct from Modal's compute allowance.

## Control gate outcome — 14 September 2026

All six `modal-boltz-controls-002` runs completed on L4 (remote function 686.08 s). Official Boltz 2.2.1 code and checkpoint/CCD hashes are in the run metadata. No affinity property was requested. The exact parsed chain mapping A=0/B=1/C=2/D=3/E=4 was verified for every output before extracting both directional target–peptide ipTM fields. The interface CA confidence and cap/disulfide distances were computed from the predicted mmCIFs. Operation `control-analysis-001` retained its request and successful receipt.

The frozen gate failed: positive mean 0.9183630645, proposed scramble mean 0.9222310980, difference −0.0038680335 versus the required +0.15. Positive exceeded scramble in 2/3 paired seeds, insufficient to satisfy both criteria. Further inference and downstream candidate work stopped. Six validation units were consumed; no control was repeated. Additional diagnostics identified an off-reference positive pose for seed 42 and compressed terminal-cap geometry. The report distinguishes these observations from binding evidence.

BoltzGen calibration `modal-boltzgen-calibration-003` completed in 418.77 s on L4. Both generated backbone cycles preserved the target/GDP and had closed backbone C–N distances, but both failed built-in glycine-content and RMSD filters. The planned main 60-design run was not launched. `final_ranked_designs` export naming does not establish filter passage; undefined native-RMSD zeros were not interpreted as pose recovery.

The latest account snapshot, `modal-billing-after-controls`, reported metered $0.74947587, billed $0, credits −$0.40 and free-storage adjustment −$0.34947587. It is a delayed account-level meter, not a per-job invoice or verification of remaining allowance. All inspected campaign GPU apps reported stopped with zero tasks.

Native tools returned during this continuation. The Sequence Viewer opened the validated four-row RAS alignment, acknowledged alignment mode, and used P01116-2|KRAS4B as reference. Structure Viewer opening against the previous session identity reported a different-source conflict; recovery of the same preflight session returned mount-pending. Adding the 5XCO reference timed out with unknown commit status; the subsequent read-only state request also timed out. The mutation was not repeated and no native render/movie is claimed. The existing 3Dmol dashboard reference view predates this restored-plugin failure. No NGS, microscopy, vendor property or assay data were fabricated to exercise unrelated plugins.

Recorded-data reporting uses `analysis/analyze_controls.py`, `plot_controls.py`, `report_controls.py` and `dashboard_results.py`. Every individual control seed is visible. Full model logs and archives remain local; the gate-failure report and dashboard are the current reviewable outcome. Public repository publication and a top-design movie/overlay were not performed after the declared stop gate.

## Resumed method investigation and revision 2

The failed gate is preserved. CPU audit of the exact saved parsed inputs and official guidance code reproduced a missing lower-distance bound for both cap links; a 0.7 Å link has zero connection-potential penalty. The disulfide remains in model bond features but is omitted by the intrachain-skipping connection-potential builder. See `results/remediation/bond-guidance-audit.json`; this is evidence of a geometry-guidance coverage gap, not proof of the cause of confidence overlap.

A complete molecular SMILES representation was assembled through RDKit 2026.03.6, preserving the two exact sequences, terminal caps and disulfide. Both have 179 heavy atoms and 20 mapped stereocenters. Formal charge +8 follows the existing pinned CCD convention (Arg charged, Asp neutral), not a pH prediction. Both passed the upstream parser, full graph edge/order checks, mapped stereo/valence checks and bounds coverage for all 183 peptide bonds. No experimental coordinates were supplied. Local initial prototype pickles omitted atom label properties; their saved maps were used for evaluator self-tests, and future serialization was corrected to AllProps, matching upstream's existing prediction writer.

One gpt-5.6-luna submodel independently reviewed graph preparation and the v2 execution/protocol. It highlighted validation coverage and output-gating requirements. Original residue atom names intentionally differ from Boltz canonical molecular labels; correspondence is established through full graph identity/order checks rather than label equality. Geometry evaluator self-tests correctly retained all 20 stereocenters, rejected all 20 centers in mirror-image coordinates, and rejected a constructed 0.7 Å cap bond for both controls.

`PROTOCOL_REMEDIATION_V2.md` and `results/remediation/preregistration-v2.json` were saved before the new neural experiment. Same positive/scramble, seeds 17/42/101 and separation threshold +0.15; chemistry is an additional mandatory gate. The old six runs still count, leaving at most 49 candidate ×3 runs plus 10 WT ×3 and 12 controls = 189 units. No repeated negative selection or gate relaxation is allowed.

The first v2 Modal application failed remote import before inference because a sibling module was not mapped. It was explicitly stopped; the standalone script duplicates the same pinned image recipe and removes that import dependency. The corrected app started with one task. Its input preprocessing artifacts are reused across seeds, including a hash check of the manifest. A successful process exit will not establish scientific success; the separately defined evaluator must check all six outputs and both gates.

Firecrawl developer search returned HTTP 403 during this investigation. Official repository source and a general-web fallback were used. Public issue #438 describes a modified-residue geometry report, and #627 reports a different peptide/MSA comparison; neither report is treated as proof that its proposed cause applies here. Current provenance is local; no new experiments or paid vendor jobs were submitted.

## Revision 2 outcome — 14 September 2026

All six full-graph predictions completed in 860.43 seconds of remote function time. The independently evaluated saved outputs matched every processed-input hash, exact graph identity/edge order, 179 atom identities, target numbering and the archived preregistration hash. All six retained every one of 183 bonds within the expanded RDKit bounds, all three critical links and all 20 input stereocenters. This supports the documented chemistry representation repair under these checks; it does not validate general molecular energy or biological activity.

The original separation rule still failed: positive mean 0.6233007709, proposed scramble mean 0.5900865893, difference +0.0332141817 versus +0.150 required. Positive exceeded scramble in 2/3 seeds. Positive mapped core RMSDs after fitting target Cα1–169 were 21.3955, 12.2365 and 11.0290 Å. All seeds remain recorded. Changed tokenization prevents direct cross-revision confidence comparisons. Twelve cumulative validation units were consumed. The main design and downstream candidate pipeline remain stopped, with no additional representation/control retries authorized under revision 2.

The v2 Modal app reported stopped and zero tasks after completion. A during-run account snapshot showed metered $0.99947587, $0 billed, credits −$0.65 and free-storage adjustment −$0.34947587; billing can lag and is not a per-job invoice. The original $200 free balance remains reported at setup, not provider-balance verified.

A gpt-5.6-luna audit identified public-export and reproducibility issues; its subsequent implementation turn ended with a workspace-credit error. The primary agent reviewed and completed its partial export utility locally. No additional model or vendor inference was started in response to either the failed gate or subagent credit error.

Post-run billing snapshot `modal-billing-after-v2`: metered $1.01947587, billed $0, credits −$0.67, free-storage adjustment −$0.34947587. The app was stopped with zero tasks; these remain account-level delayed readings. The complete v1+v2 recorded-data reproduction passed locally without inference. Desktop QA first required restarting the stopped local HTTP preview, then switching the oversized whole-page capture to viewport and individual-section captures. These presentation failures did not alter scientific outputs.

Desktop/mobile dashboard QA passed with 12 visible control rows, no page errors, no broken local report links and no mobile horizontal overflow. Isolated public-export reproduction retained every numerical result and scientific input; initial differences were limited to SVG random identifiers/date metadata and their derived dashboard manifest. SVG export was then made deterministic and a fresh isolated reproduction check was prepared. The local export remains unpublished; raw/private operational records stay outside its allowlist.

Final isolated-export reproduction `public-export-reproduction-v2-003` passed. Every exported SHA-256 hash matched after the offline rebuild, including deterministic SVGs, all numerical outputs and dashboard files. The manifest checker excludes Python-generated bytecode caches; its initial false mismatch from importing the checker was corrected. `results/reproducibility-qc.json` records the tested package versions and scope. Scientific computations and the twelve retained control predictions were not changed.

## Protenix diagnostic outcome — 14 September 2026

A Modal-backed independent-model diagnostic followed the failed Boltz gates. The first A100-80GB dispatch was rejected by Modal because the account had no payment method; no GPU task or prediction ran. The same Protenix-v2 input was then attempted on L4. That run reached the official checkpoint download step and failed before model loading or prediction because `protenix-v2.pt` returned HTTP 403. The failed archive is retained under `results/protenix-diagnostic-001`.

A bounded one-byte range probe against the pinned official Protenix checkpoint URL table showed `protenix-v2.pt` returning HTTP 403 while `protenix_base_default_v1.0.0.pt` and other official full/base/mini weights returned HTTP 206. Before observing any base-model outputs, the run was amended to use `protenix_base_default_v1.0.0`, the strongest reachable official Protenix model with the same 2021-09-30 training cutoff. The unchanged controls, seeds 17/42/101, ten recycles, 200 diffusion steps, saved target MSA, no-template setting and no-gate-change interpretation are recorded in `PROTOCOL_PROTENIX_DIAGNOSTIC.md`.

The base Protenix run completed on Modal L4 in 1280.64 seconds and returned six CIFs plus six confidence JSON files. It strictly loaded 368.48M parameters from upstream commit `4c355be4553512f72453ecbfb65e69f4c35d1413`. The local audit verified the target sequence/numbering and the 179-heavy-atom ligand atom-name/element correspondence in every output. Under the saved RDKit-bound/stereochemistry evaluator, the outputs did not pass all chemistry checks: bonds-in-expanded-bounds ranged from 181 to 182 of 183 and stereocenters-correct ranged from 16 to 19 of 20.

The known positive failed reference-pose recovery in all three base-model seeds. After target C-alpha 1-169 superposition, core C-alpha RMSDs were 29.0606, 30.9316 and 30.5841 A for seeds 17, 42 and 101. Native 5 A residue-contact recovery was 0/41 in every positive-control seed. These six additional predictions raise the recorded validation-unit count to 18 but add no candidate-selection claim, no binding-affinity evidence and no rescue of the failed Boltz control gates.

Post-run Modal billing summary for September 2026 reported metered cost $1.65, credits -$1.27, free storage -$0.38 and billed cost $0.00. This is an account-level, delayed billing summary rather than a precise per-job invoice. All inspected Protenix Modal apps were stopped with zero tasks.

## Project overview revision — 15 September 2026

Two gpt-5.6-luna supporting tasks reviewed the mapping/interpretation and updated the report, brief, editable deck and README. The primary agent implemented and verified the comparison interface and release package. No new model inference or vendor experiment was run.

`analysis/build_demo_assets.py` derives display assets from all 18 recorded control predictions. It fits only the 169 sequence-checked KRAS target C-alpha atoms with a proper rigid transform and applies that transform to every source atom. The nine positive core RMSDs are recomputed and asserted equal to the saved audit within 1e-7 A. Original CIFs remain untouched. Peptide connectivity is carried from each declared full molecular graph, with 179 atom identities and 183 bonds checked; it is not inferred from misleading compressed bond distances or interpreted as a chemistry pass. Scramble native-pose metrics remain null. Every raw-source and display-payload hash is recorded in the transform manifest.

The dashboard now exposes model/representation, control and seed selectors; reference/prediction overlays; target layers; focus and rotation controls; a fixed-order table of all 18 runs; original CIF downloads; and enlargable figures. Counts distinguish 12 Boltz outputs from six Protenix base diagnostics. The original failed gates and stopped candidate stages remain visible. The report and brief incorporate the completed Protenix outcome.

Browser verification selected all 18 rows and checked the corresponding displayed RMSD, contacts and confidence, including non-applicable scramble fields. Layer toggles, focus, rotation and figure enlargement worked without captured errors. At 390 px width the page fits and all wide tables have reachable scrolling; the previously clipped Protenix table was corrected. `results/study-package/demo-qa.json` records scope. This is presentation/recorded-data QA, not new scientific validation.
