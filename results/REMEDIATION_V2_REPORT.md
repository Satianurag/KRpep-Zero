# Full-molecule control remediation — revision 2

The repair does not clear validation.

**Decision: `STOP_REMEDIATION_GATE_FAILED`.** All six preregistered predictions completed; separation failed and chemistry passed.

The original revision-1 failure is preserved. This additional experiment changed the representation of the same positive control and proposed scramble to complete chemical graphs. It did not change their sequences, seeds or the confidence-separation rule.

## Frozen gates

- Mean positive pair ipTM: 0.623301; proposed scramble: 0.590087.
- Difference: +0.033214; required ≥ +0.150. Positive higher on 2/3 paired seeds; required ≥2/3.
- Chemistry requires all three diagnosed critical links within the precomputed RDKit distance bounds expanded by 12.5%, and all 20 stereocenters matching the input in every seed. The fraction of all 183 peptide bonds within bounds is reported separately.

## Every seed

| Control | Seed | A→B ipTM | B→A ipTM | Mean | Mapped interface pLDDT | Bonds in bounds | Centers correct | Critical links | Core RMSD Å |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| KRpep-2d | 17 | 0.4209 | 0.7071 | 0.5640 | 56.82 | 183/183 | 20/20 | PASS | 21.395 |
| SCRAMBLE-20260914 | 17 | 0.5374 | 0.7645 | 0.6509 | 67.03 | 183/183 | 20/20 | PASS | — |
| KRpep-2d | 42 | 0.5081 | 0.7899 | 0.6490 | 64.41 | 183/183 | 20/20 | PASS | 12.237 |
| SCRAMBLE-20260914 | 42 | 0.3705 | 0.6005 | 0.4855 | 59.51 | 183/183 | 20/20 | PASS | — |
| KRpep-2d | 101 | 0.5258 | 0.7880 | 0.6569 | 68.26 | 183/183 | 20/20 | PASS | 11.029 |
| SCRAMBLE-20260914 | 101 | 0.4914 | 0.7763 | 0.6338 | 65.23 | 183/183 | 20/20 | PASS | — |

## Interpretation and limits

Interface confidence is not affinity, cellular activity or biological selectivity. The proposed scramble is not an experimentally established nonbinder. A failed separation gate does not establish that either molecule binds or fails to bind.

Absolute confidence and pLDDT must not be pooled or compared with revision 1: atom-token representation changes the model inputs and normalization. Pose RMSD uses the exact positive-control correspondence after fitting only target Cα1–169; no peptide refitting or best-seed selection is used.

The input formal charge follows the pinned CCD representation (+8, neutral Asp acid). This is not a physiological protonation assignment. Possible training-set overlap with 5XCO also limits prospective interpretation.

## Reproducibility and resources

Pinned code `b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc`; weights `6fdef46d763fee7fbb83ca5501ccceff43b85607`. One L4; recorded remote function elapsed 860.4 seconds. Elapsed time is not an invoice or a verified remaining-credit balance.

Six revision-2 runs plus six revision-1 runs consume 12 validation units. The declared maximum of 49 candidate triplets and 10 WT triplets would total 189 units only if both gates pass. No affinity inference was requested.

The archived protocol, preprocessing hashes, input graphs, all structures, per-seed table and complete bond/stereochemistry audit are retained in `results/control-remediation-v2-002/`. Rebuild with `analysis/analyze_controls_v2.py`, then `analysis/report_controls_v2.py`.
