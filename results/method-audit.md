# KRpep-Zero method audit

Audit scope: the original specification, `setup/tool-checks.json`, and
`setup/STATUS.md`. This is a setup/schema audit only. No model, network,
compute, account, or paid service was used. Proto is excluded from the
recommendations below.

## Executive assessment

The proposed validation arithmetic can fit the stated nominal cap, but the
method is not yet reproducible or chemically comparable. The largest blockers
are (1) treating a 12–16-residue generic cyclic peptide as a control-equivalent
representation of KRpep-2d, (2) assigning the Proteina-Complexa arm to a
schema that exposes only 70–150-residue protein binders and no cyclic-peptide
option, and (3) making an ESM hotspot profile containing 12/13/61 a mandatory
stop gate without defining the score or proving that those positions must
appear. ipTM/pLDDT ranking can support a structural triage claim, but cannot
support affinity, potency, or “binding” claims by itself.

## Verified facts

### Chemical and structural control

The supplied control paper identifies KRpep-2d as a 19-mer,
`Ac-RRRR-c(CPLYISYDPVC)-RRRR-NH2`. The Cys5–Cys15 disulfide makes the central
11-residue segment cyclic. The crystal paper reports SPR KD values of 8.9 nM
for G12D/GDP versus 58 nM for WT/GDP, and 11 nM for G12D/GTP versus 200 nM
for WT/GTP. It also reports an exchange-inhibition IC50, but these are
literature biochemical results, not outputs available from the proposed
co-folding run. The crystal paper notes that the terminal Arg side chains are
solvent-exposed and do not interact specifically with K-Ras; this audit does
not assign them a demonstrated cell-penetrating function. See
`results/sources/ks58-full.md` and `results/sources/crystal-full.md` (the
latter is Sogabe et al., PDB 5XCO, 1.25 Å). The KS-58 source is treated as
secondary context here; its stronger or subnanomolar claims are not used as
KRpep-2d control values.

The control source also distinguishes disulfide cyclization from amide and
main-chain cyclization. Therefore a generic sequence plus a model-level
`cyclicPeptide` switch does not establish that a prediction represents the
same chemistry as KRpep-2d.

### Boltz/BoltzGen schemas

The Tamarind BoltzGen catalog labels BoltzGen as supporting peptides and
cyclotides. Its verified schema exposes a `peptide` task with a length range
(default 10–20), `cyclic` boolean, optional `peptideSequence`, and optional
`peptideDisulfideBonds`; the cyclotide task separately requires a cysteine
sequence and disulfide bonds. It emits structures/sequences and design
interface metrics including design-to-target ipTM, iipTM, ipSAE, pDockQ,
interface pLDDT, and RMSD-related fields. This verifies input/output fields,
not that a particular closure or disulfide topology reproduces KRpep-2d.

The Tamarind Boltz-2 schema accepts protein sequences and has a
`cyclicPeptide` boolean described as making the shortest protein chain cyclic.
It exposes `seed`, `numSamples`, `numBatches`, `runIpsae`, `iptm`,
`protein_iptm`, `ipSAE_*`, pDockQ*, pLDDT, PAE/PDE, and structure outputs. Its
`predictAffinity` path is explicitly limited to small-molecule binders. The
schema also exposes a protein-protein affinity switch for a hosted server, but
the specification must not treat that as a peptide affinity measurement; the
original prompt expressly prohibits requesting Boltz-2 peptide affinity.

The Proto Boltz-2 record is `needs_deploy`, and STATUS records Proto as
unlinked to Modal. It is therefore not an available route under the current
zero-new-paid-spend, no-Proto constraint.

### Proteina-Complexa schema

The verified Proteina-Complexa schema offers `protein-binder`, `ligand-binder`,
and `motif-ligand`. For `protein-binder`, it requires a target PDB, target
chains, optional hotspot residues, a binder length range defaulting to 70–150,
and a design count. Its outputs include interface pTM, interface PAE, pLDDT,
scRMSD, pDockQ/ipSAE-like fields, and PDB/sequence results. There is no
peptide/cyclic toggle, disulfide specification, 12–16 length range, or seed
field in the saved schema. The tool description says “protein binder”; the
schema does not justify inferring peptide or macrocycle support from the tool
name.

### Seeds and output metrics

Boltz-2 has an explicit integer `seed`. BoltzGen and Proteina-Complexa have no
seed parameter in the saved schemas. Boltz-2 defaults to `numSamples=5` and
`numBatches=1`; a run described as “3 seeds” therefore needs an explicit
`numSamples=1`/one-output convention or the number of generated structures and
the budget unit will be ambiguous. Boltz outputs multiple model indices in its
metrics schema, so “one prediction” must also be defined as one submitted
seed/job versus one model/output structure.

## Missing evidence and methodological risks

1. **Control representation is underspecified.** A 12–16 aa generic cycle
   cannot reproduce the 19-mer KRpep-2d sequence, Arg tails, Cys5–Cys15
   disulfide, termini, or reported chemistry. If the positive control is
   truncated, linearized, or represented as a backbone cycle, its score is not
   a KRpep-2d control score. The negative scramble must preserve length,
   residue composition, and the same closure/charge/PTM representation, or a
   negative result can merely report representation mismatch.

2. **The two generation arms are not comparable as written.** BoltzGen has a
   peptide path in the requested size range. Proteina-Complexa’s verified
   protein-binder path cannot be used to claim a second 12–16 aa cyclic-peptide
   arm. Treating its 70–150 aa proteins as the same candidate class would be a
   protocol violation and confounds length, topology, and model family.

3. **Topology and noncanonical chemistry are not validated.** The saved
   schemas do not show a way to encode KRpep-2d’s acetylated/amidated termini
   and exact disulfide chemistry in a common validation input. A schema
   validation pass, generated structure inspection, and explicit bond/topology
   manifest are required before any score comparison.

4. **ipTM is not affinity.** ipTM, pLDDT, pDockQ, ipSAE, PAE/PDE are confidence
   or geometry surrogates. They are not calibrated KD, IC50, free energy, or
   cellular activity. A high ipTM can reflect a confidently predicted pose
   under model assumptions. Interface RMSD to 5XCO tests pose similarity only,
   and alignment choices, target state, peptide truncation, and closure
   chemistry can change it.

5. **“Blind validation” is overstated unless the ranking and controls are
   frozen first.** Using 5XCO contacts as generation hotspots and then using
   5XCO RMSD for validation is structure-informed validation, not fully blind
   validation. The protocol can still be called a held-out or fixed-protocol
   co-fold comparison if all controls, seeds, filters, ranking fields, and
   exclusion rules are frozen before looking at candidate outcomes.

6. **The ESM gate is brittle and not target-specific.** Positions 12, 13, and
   61 are established Ras mutation hotspots in the supplied crystal-paper
   context, but an ESM mutation-sensitivity profile for G12D versus WT does
   not logically have to show all three positions: the comparison changes
   residue 12, while positions 13 and 61 are unchanged. The specification
   does not define whether “include” means a local maximum, a signed score,
   threshold, or merely a plotted row. ESM mutation sensitivity also measures
   sequence-model plausibility, not peptide binding or pocket engagement.

7. **Free-tier capacity is not verified entitlement.** STATUS says catalog
   access succeeded but free compute allowances and no-paid-overage controls
   remain unverified. The nominal “~200/month” statement in the prompt cannot
   be treated as an enforceable budget until the provider account exposes the
   actual allowance and failure behavior.

## Budget audit

If a validation prediction means one candidate/control, one seed, one target,
and no retries, the specified screen is:

`50 candidates × 3 G12D seeds = 150`

`+ 1 KRpep-2d control × 3 = 3`

`+ 1 scrambled control × 3 = 3`

`+ 10 top candidates × 3 WT seeds = 30`

`= 186 prediction units`

This is under 190 by four units, so the strict cap permits at most four
additional units (186 + 4 = 190), and it is under a nominal 200 by fourteen.
It ceases to be under 190 if “top 50” is selected separately per generation arm,
controls receive additional closure variants, a seed emits multiple counted
models, or any retry/failure/extra control is charged. Freeze the unit of
accounting, reserve no more than the four-unit margin, and fail closed before dispatch if
the provider reports a different count.

## Recommended small control-first calibration

1. **Do a zero-cost schema/topology dry run.** Prepare one KRpep-2d record,
   one composition-matched scrambled record, and one 12–16 aa candidate in the
   exact intended input format. Validate without dispatch; inspect whether
   the input representation encodes the intended chain closure, disulfide (if
   used), termini, and chain IDs. Output-structure inspection requires an
   inference and is not part of a zero-cost dry run; if inference is later
   authorized, inspect the resulting structure and target state separately.
   Record the serialized inputs and validator outputs.

2. **Use one chemically coherent control protocol.** For a model that only
   supports generic cyclic protein chains, label the result as a backbone-cycle
   surrogate and do not call it KRpep-2d. For a KRpep-2d control, preserve its
   19-mer sequence and explicit disulfide/terminal chemistry in a tool path that
   demonstrably accepts them. Apply the same representation to the scramble.

3. **Separate arms by capability.** Either make the generation comparison
   BoltzGen peptide versus another verified 12–16 aa peptide-capable route, or
   run Proteina-Complexa as a distinct 70–150 aa protein-binder exploratory
   arm. Do not merge their leaderboards or claim an apples-to-apples peptide
   comparison.

4. **Replace the ESM stop with a diagnostic QC.** Require the profile to have
   defined rows 12, 13, and 61, report their signed scores and thresholds, and
   run a known synthetic/control mutation check. Stop only for malformed or
   missing output; treat unexpected hotspot ordering as a documented warning
   that does not authorize design claims.

5. **Pre-register validation and language.** Freeze candidate IDs, controls,
   target construct/state, closure chemistry, seeds (17/42/101), Boltz sample
   count, ranking formula, missing-value handling, and the 186-unit ledger
   before running. Report “co-fold confidence under the fixed protocol” and
   pose RMSD only; do not infer affinity, potency, or selectivity from ipTM.

## Major blockers to campaign execution

- No verified common representation currently makes a 12–16 aa design,
  KRpep-2d, and the scramble chemically comparable.
- Proteina-Complexa is not schema-verified for the requested cyclic peptide
  class or length and cannot support the stated second arm as written.
- Seed/retry/output-count semantics are incomplete, so the under-190 claim is
  conditional rather than enforceable.
- ESM 12/13/61 is an unjustified mandatory stop criterion until its metric and
  expected behavior are defined.
- Free-tier/no-paid-overage entitlement remains unverified in STATUS; no job
  should be launched on the nominal allowance alone.
