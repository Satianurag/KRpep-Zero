# KRpep-Zero

A computational KRAS G12D cyclic-peptide campaign **stopped at its declared control-selection gate**. Across the two Boltz protocols, 12 control predictions were retained. Revision 2 repaired the measured bond/stereochemistry problems, but its mean positive-versus-scramble confidence gap **+0.0332** failed the required **+0.150**. A subsequent Protenix base diagnostic added six independent-model control predictions and recovered **0/41 native contacts for the positive control in each seed**; scramble contact recovery is **NA**. Two BoltzGen technical-calibration structures also failed built-in filters (0/2 accepted). The main 60-design batch and downstream candidate work were not run.

The project contains the source-backed evidence brief, matched KRAS4B target, real ESMC masked-residue profiles, all 18 control predictions (12 Boltz + 6 Protenix) and geometry/pose diagnostics in an interactive results dashboard. These are model runs of two control identities, not biological replicates. No novel peptide affinity or biological activity has been demonstrated. See the [current result](results/REMEDIATION_V2_REPORT.md) and [preserved revision-1 report](results/CALIBRATION_REPORT.md).

## Revision 2: chemistry repaired, selection still fails

The additional preregistered six-run experiment completed. Both full-molecule controls retained all 183 bonds within the declared bounds and all 20 stereocenters in every output. The confidence-separation gate nevertheless failed: positive mean **0.6233**, proposed scramble **0.5901**, difference **+0.0332** versus required **+0.150**. Two of three paired seeds favored the positive. The three positive-control core RMSDs were **21.40, 12.24 and 11.03 Å** after target superposition.

The candidate pipeline remains stopped, and the Modal GPU app is stopped with zero tasks. No control was substituted, threshold relaxed, or favorable seed selected. Absolute confidence cannot be compared with revision 1 because peptide tokenization changed. See the [revision-2 result](results/REMEDIATION_V2_REPORT.md), [frozen protocol](PROTOCOL_REMEDIATION_V2.md) and [all-seed figure](results/figures/control-remediation-v2.png).

## Protenix diagnostic: independent model check did not rescue the gate

The authorized Protenix extension first attempted `protenix-v2`, but the official `protenix-v2.pt` checkpoint returned HTTP 403 before model loading or prediction. The strongest reachable official same-cutoff fallback, `protenix_base_default_v1.0.0`, completed six predictions on Modal L4. It loaded 368.48M parameters strictly, used the same controls and seeds, and produced all six CIF/confidence outputs.

The known positive did not recover the crystallographic pose: native 5 A residue-contact recovery was **0/41 in each seed (17, 42 and 101)**, with core C-alpha RMSDs **29.06, 30.93 and 30.58 A** after target superposition; scramble contact recovery is **NA**. The diagnostic also failed the all-output chemistry checks under the saved RDKit-bound/stereo evaluator. This is a model-family stress test and does not alter either failed Boltz gate. See [Protenix protocol](PROTOCOL_PROTENIX_DIAGNOSTIC.md), [summary](results/study-package/protenix-diagnostic-summary.md) and [figure](results/figures/protenix-base-diagnostic.png).

## Open the evidence

- [Dashboard](dashboard/index.html) — interactive experimental structure and recorded-data figures.
- [Demo guide](DEMO_GUIDE.md) — exact controls for the 18-row pose table and one-prediction viewer.
- [Evidence brief](BRIEF.md) — published control chemistry, assay-specific affinity and current clinical context.
- [Target and pocket](POCKET.md) — coordinate-derived contacts and the KRAS4A/4B numbering correction.
- [Fixed protocol](PROTOCOL.md) — control chemistry, seeds, ranking, stop gate and budget definitions.
- [Provenance](PROVENANCE.md) — completed runs, revisions, corrections and fallback decisions.

The dashboard is a local static artifact. Serve it with `python -m http.server 8873 --bind 127.0.0.1 --directory dashboard`, then open `http://127.0.0.1:8873/`. Its molecular viewer uses the vendored 3Dmol.js library and deposited 5XCO coordinates. A designed peptide is never substituted for the experimental reference without an explicit label.

## Reproduce existing figures without API keys

The recorded-data route was tested with Python 3.12 on macOS. GPU/inference libraries and provider accounts are not needed for this route. With Python 3.12:

```sh
python -m venv .venv-analysis
.venv-analysis/bin/pip install -r requirements-analysis.txt
.venv-analysis/bin/python analysis/reproduce.py
```

This regenerates coordinate checks, alignment, control-gate/geometry analysis, contact/ESMC/control figures and the dashboard from saved source data. It does not retrain models, request inference, contact a provider, or recompute an experimental measurement. Optional local-dashboard QA uses `node analysis/render_preview.cjs` with Playwright installed (or `KRPEP_PLAYWRIGHT_MODULE` pointing to that module). It checks the six control rows, stop decision, report links, existing 3D viewer and mobile overflow; it does not create a new standalone molecular render.

## Scientific distinctions

The crystallographic reference is KRAS4B 1–169/GDP with the complete 19-mer KRpep-2d, including acetyl/amidated termini and a Cys5–Cys15 disulfide. The proposed 12–16-residue backbone-cyclic designs have different chemistry. Exact molecule representation must be checked before comparing model confidence.

ESMC scores are sequence-model probabilities. Boltz interface confidence is not affinity, potency, cellular activity or proven mutant selectivity. The control gate and all individual seeds must be reported, including failure. Training-set overlap with a known crystallographic reference is possible; reference-informed design is not a prospective experimental validation.

## Runtime routes and limits

Official Biohub ESM ran on Modal L4. The BoltzGen and Boltz2 source packages are pinned; named biological-plugin tools were temporarily unavailable during inference preparation, so documented package routes were used. Tools later returned; native sequence-viewer control succeeded, while native structure-viewer recovery timed out. Proto is excluded. Free-credit use is bounded and recorded; no paid-overage, experiment dispatch or vendor purchase is authorized. Wet-lab work remains draft-only.

`results/logs/` retains scientific command receipts and raw outputs. Provider billing snapshots and private setup metadata remain local and must not be included in a public export. Third-party literature is referenced by URLs/identifiers and hashes in the public package; cached full texts retain their original rights. The generated analysis code is MIT licensed; third-party software and data retain their own licenses.

## Bounded public export

`python analysis/export_public.py` builds `dist/public-KRpep-Zero/` from an explicit allowlist and records SHA-256 hashes in `release-manifest.json`. It omits raw operational logs, provider billing/setup records, environments, model weights and cached full-text literature. Parsed scientific inputs, all control structures, confidence records and processed-input hashes are retained. Public run metadata is sanitized; original local receipts remain unchanged. Export is local and does not publish to GitHub.

The current campaign has no passing novel design; the export records the failed calibration and method repair. See `THIRD_PARTY_NOTICES.md` for upstream attribution and remaining redistribution limitations.

Verify an untouched export with `python analysis/export_public.py --verify-only --dest dist/public-KRpep-Zero`. Reproduction checks the release manifest before loading its saved inputs. SVG IDs and date metadata are fixed for deterministic figure export in the tested environment; numeric results are independently checked.

## Project materials — 15 September 2026

- `output/pdf/KRpep-Zero-report.pdf`: methods, recorded gates, all-seed pose/contact audit, literature control candidates and limitations.
- `output/pdf/KRpep-Zero-brief.pdf`: one-page discussion brief.
- `output/presentation/KRpep-Zero-overview.pptx`: nine editable slides with source notes, Protenix outcomes, methods and limitations and a single-prediction pose-view guide.
- Dashboard `#package`: documents, audit CSV and experimental analog table.
- `results/pose-audit/`: exact mapping checks, target-fitted RMSDs, 5 Å residue-contact recovery and circular omega deviations. These custom diagnostics are not DockQ or binding-affinity estimates.

The new analysis scripts are included in `analysis/reproduce.py`. PDF regeneration is optional and requires ReportLab (`analysis/build_study_report.py`). The editable slide builder uses the Codex bundled `@oai/artifact-tool` runtime; the exported PPTX can be opened independently without that authoring environment.

A separately documented Protenix diagnostic is included in the final package. It cannot change either recorded Boltz failure or, on its own, justify candidate selection.
