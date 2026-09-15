# KRpep-Zero remediation experiment — revision 2

Declared after the revision-1 failure and before any revision-2 neural predictions. The user resumed the task and explicitly directed us to proceed efficiently with models. Revision 1 remains failed, with all six seeds retained. This experiment tests a documented input-representation remedy; it is not a retrospective change to the original gate.

## Reason for one bounded additional experiment

The pinned official Boltz2 parser/feature/potential code and saved inputs show that external ACE/NH2 links have no RDKit lower-distance bounds. `ConnectionsPotential` applies an upper bound of 2 Å, gives zero penalty at 0.7 Å, and omits intrachain disulfides. VDW guidance excludes connected-chain pairs. These are reproduced in `results/remediation/bond-guidance-audit.json`; they permit distorted chemistry but do not establish the cause of overlapping control scores.

The upstream supported SMILES route encodes each complete capped/disulfide peptide as a single connected molecular graph. Both controls passed the exact parser, with all three critical bonds having two-sided RDKit distance bounds. No upstream model, checkpoint, score function or potential is patched.

## Inputs and inference

- Same KRAS4B G12D 1–169 as target A, same GDP C, same two control sequences, same caps and Cys5–Cys15 disulfide. Peptide B is now one ligand entity containing 179 heavy-atom tokens; 376 total tokens. No residue is truncated or replaced by a surrogate.
- RDKit 2026.03.6 assembles the graphs and validates 20 stereocenters. The charge/bond representation follows the pinned CCD: eight Arg guanidinium charges, neutral Asp side-chain acid, total formal charge +8. This is a literal model-input convention, not a physiological-pH or pKa assertion. Both controls have the same formula and charge. Explicit maps relate every molecular atom back to original peptide residue/atom identity.
- No crystal coordinates, binder template, pocket constraint, or reference pose is supplied to inference. RDKit reference conformers are generated independently. For each control, reuse its first completed preprocessing artifacts across seeds and verify their hashes; no output coordinates are reused. Initialize RDKit's global RNG to 20260914 before upstream CLI preprocessing. The fixed reference conformer is an input chemical feature, not a predicted pose.
- Official Boltz 2.2.1 code `b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc`; same pinned model/CCD repository `6fdef46d763fee7fbb83ca5501ccceff43b85607`, Torch 2.8.0/cu126 and L4 runtime as revision 1.
- Seeds 17,42,101; one sample per control/seed, 3 recycles, 200 sampling steps, one parallel sample, `use_potentials`. Same target MSA and 8192/1024 cap/subsampling policy. Peptide B is molecular, so it has no sequence MSA. No affinity property or affinity inference, regardless of the ligand input classification.

## Evaluation frozen before outputs

Require all six outputs and exact atom/chain mapping. Report all six seeds, both directional A/B ipTM fields and their mean. Never compare absolute revision-1 and revision-2 ipTM as evidence of improved binding: tokenization and confidence normalization changed.

The **same control separation rule** applies within revision 2: positive mean pair-ipTM minus the original proposed scramble mean must be ≥0.15, with positive higher on ≥2/3 paired seeds. The scramble remains an unvalidated negative-control proposal. Do not substitute it, select favorable seeds, relax the rule, or rerun failures.

Additional chemistry gate: every predicted capped control must retain all intended atoms and match the stereochemical graph. Evaluate all peptide bond distances against the *precomputed* RDKit bounds expanded by the upstream `bond_buffer=0.125`; report the fraction inside these bounds. All three explicitly diagnosed critical links must fall within their expanded two-sided bounds for all six outputs. Verify peptide tetrahedral stereocenters from predicted coordinates against mapped graph stereochemistry; uncertain or inverted centers fail the chemistry gate. Geometry failure stops advancement even if confidence separates.

Interface pLDDT: retain original definition of unique target and peptide Cα atoms whose residues have any direct target–peptide heavy-atom contact ≤4 Å; use the explicit map to reconstruct peptide residues from the single molecular entity. Exclude ACE/NH2/GDP. pLDDT is per-atom on molecular tokens, so report this as mapped-Cα interface confidence and never pool it with revision-1 values.

Positive-control pose diagnostics retain exact 5XCO correspondence: target A1–169 Cα superposition; peptide Cα1–19 and core Cα5–15 RMSDs. Keep all seeds, and do not use reference-pose RMSD as a hidden selection criterion. No arbitrary residue mapping is allowed for future unequal-length candidates.

## Resources and next decision

One L4 container, no retries, min containers 0, max 1, 6000-second function timeout, 750-second per-inference timeout. Reserve at most $10 of the user-reported $200 free Modal allowance for this experiment; reconcile account meter afterward. This is a local planning reserve, not a provider-enforced spending cap. No payment method, purchase, deployment or wet-lab dispatch is added.

The six revision-1 runs still count. With six additional controls, 49 candidate complexes ×3 seeds plus 10 WT counter-screens ×3 seeds total **189 validation units**, strictly below 190. Therefore reduce the maximum retained candidate count from 50 to 49, without changing the planned 60-design generation arm. No spare retry unit remains at this maximum; missing runs remain missing. Modal charges compute rather than a hosted prediction quota, but the stricter requested run-count guardrail is still preserved.

Only if both separation and chemistry gates pass may the main generation/screening campaign resume. If either fails, retain revision 2 as a failed calibration and stop the candidate pipeline. Do not iterate representations or controls merely until one happens to pass.
