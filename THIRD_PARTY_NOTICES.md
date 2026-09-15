# Third-party notices

This file describes the provenance and licensing status of material selected for the bounded public export. It does not grant rights beyond the upstream terms. Full cached articles, provider logs, account records, model archives, and private setup metadata are intentionally omitted.

## Project code

The generated analysis and dashboard code in this repository is released under the MIT License in `LICENSE`.

## Bundled software

`dashboard/vendor/3Dmol-min.js` is distributed with its accompanying `dashboard/vendor/LICENSE` and `dashboard/vendor/source.json`. That vendor notice is authoritative for the bundled 3Dmol.js copy.

The Python analysis environment is described in `requirements-analysis.txt`. The source tree does not attempt to relicense NumPy, Matplotlib, Gemmi, Biopython, Pillow, PyYAML, Requests, RDKit, or their transitive dependencies; consult each installed distribution's license metadata when redistributing an environment.

## Scientific data

- The 5XCO coordinate files and entry metadata are derived from the RCSB Protein Data Bank deposit. The export preserves identifiers and hashes; the applicable PDB and depositor terms remain upstream terms and are not replaced by the project MIT license.
- KRAS, NRAS, and HRAS sequence records are identified by UniProt accessions in the files and reports. UniProt database and attribution terms remain applicable; no additional license is asserted here.
- Boltz 2 pinned source `b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc` explicitly identifies both code and weights as MIT in its README and LICENSE. The recorded checkpoint metadata for `boltz-community/boltz-2` revision `6fdef46d763fee7fbb83ca5501ccceff43b85607` also lists MIT. BoltzGen source LICENSE and recorded model-card metadata list MIT. These outputs remain computational observations; the export contains no model weights.
- ESMC outputs were generated using `biohub/esmc-300m-2024-12` revision `7f10b20ae75017b2dbc884070e03434515709a8d`. The pinned model card lists MIT and `other`, linking to the Biohub ESM third-party notice. On 14 September 2026 that notice was verified at pinned source commit `ba4d7124864eed323a93bf3cfefcd958f573b75a`: it lists dependency licenses, while LICENSE.md is MIT (Chan Zuckerberg Biohub, 2026). Copies and source/hash receipts are in `results/licenses/`. No ESMC weights or dependency source distributions are included; this release contains recorded numeric outputs and analysis code, not a redistributed model environment.
- Publicly available structure/model output formats (mmCIF, PDB, CSV, JSON, NPZ) do not by themselves establish a license for the underlying scientific content.

## Excluded sources

Cached full-text literature, clinical registry captures, search-result dumps, provider receipts, billing snapshots, raw inference archives, and private setup/preflight records are excluded from the public export. The reports retain source URLs, identifiers, and limited factual summaries so downstream users can consult the original source under its own terms.

When a future release adds an upstream artifact, record its source URL/accession, retrieval date, hash, and explicit license or an “unresolved” status in this file before export.
