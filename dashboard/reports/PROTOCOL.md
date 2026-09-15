# KRpep-Zero fixed protocol — revision 1

Frozen before design or validation output inspection. Zero new paid spend remains a constraint. Official package fallbacks are used where the named plugin is unavailable. Proto is excluded.

## Target, controls and representation

Use KRAS4B P01116-2 residues 1–169, with G12D for the mutant and G12 for WT. Preserve GDP explicitly; FASTA alone is not a nucleotide-state specification. Experimental reference: 5XCO, author target chain A and peptide chain B. Atom-contact definition is the asymmetric unit, non-H atoms with positive occupancy and blank/A alternate conformer; a 4 Å pocket plus a documented 5 Å sensitivity shell. Ground-truth target coordinates and the reference binder must not be included as hidden binder templates in an allegedly blind co-fold.

The positive control is the full 19-mer KRpep-2d with Cys5–Cys15 disulfide, acetylation and amidation. The proposed scramble is defined once in `results/controls/controls.json`, seed 20260914, retaining termini, Arg tails and cysteine positions. It is not an experimentally confirmed nonbinder. Do not silently substitute a linear or backbone-cyclic surrogate for either control.

Generation uses 12–16-residue backbone-cyclic designs from the documented BoltzGen peptide route. These designs need not share the positive control's topology, but each molecule must be represented faithfully by the same validation engine. A common validated input/output representation for nucleotide and all control chemistry is mandatory before confidence comparison.

## ESMC diagnostic

Official ESMC300M, immutable code and checkpoint revisions recorded in `results/esm/metadata.json`; seed 17, float32. Mask every position independently and save all logits. Report canonical-20 entropy and all 19 nonnative log-odds versus the native residue at each position in both sequence backgrounds.

**Declared correction to the supplied gate:** annotate and validate positions 12/13/61; do not require the language model to rank all three as hotspots. Biological mutation hotspots are not guaranteed maxima of this sequence statistic. Require canonical 169-residue sequences differing only by G12D, complete finite 169×64 output arrays, correct token mapping, and identical position-12 masked-context logits within 1e-5. This is technical QC, not validation of mutant-selective peptide binding.

## Generation and calibration

Use the pinned official BoltzGen source, peptide-anything protocol, explicit pocket bias, and built-in filtering. First test two designs to check parser output, GDP retention, cyclic closure, runtime, and output semantics; these calibration outputs do not become silently selected winners. The planned primary arm has 60 designs. Record all generated sequences and failures before filtering.

Proteina-Complexa's currently inspected schema supports protein binders and does not establish 12–16-residue cyclic-peptide support. Apply the attachment's fallback: omit that arm, record the reason, and do not relabel longer protein binders as peptides. Use of only one arm limits model-family diversity.

## Validation and gate

Use fixed seeds 17,42,101 and exactly one sample per seed for each molecule/target pair. Disable affinity prediction. Retain all individual seed results, missing runs and failures. Report target–peptide pair-specific interface confidence where additional chemical entities would confound global ipTM; the exact selected provider field and indexing must be frozen after schema inspection and before predictions.

**Validated runtime detail, frozen before control inference:** official Boltz 2.2.1 source `b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc`, pinned official checkpoint repository revision `6fdef46d763fee7fbb83ca5501ccceff43b85607`. Protein target A, peptide B, GDP C; positive/scramble caps are ACE D and NH2 E. Native component and all three bond endpoints passed the official parser against the exact CCD bundle. Pair score is the arithmetic mean of `pair_chains_iptm[0][1]` and `[1][0]`, using parsed chain indices A=0/B=1, not global ipTM. Record both directions. Interface pLDDT is the mean CA confidence of protein residues from A and B making any direct A–B heavy-atom contact within 4 Å; caps/GDP are excluded, and absence of contacts is missing rather than zero confidence.

Validation uses no binder template or pocket restraints; explicit chemical bonds and the `use_potentials` option preserve intended chemistry. Use 3 recycling steps, 200 diffusion steps, 1 diffusion sample, 1 parallel sample, target MSA capped at 8192 rows and explicitly subsampled to 1024. The public MMseqs2 WT query produced 16,334 MSA rows. WT and G12D files share all homolog rows; only the first query sequence differs at G12D. Peptide MSA is empty. The official CLI downloads its affinity checkpoint eagerly, but no affinity property is requested and no affinity inference is permitted.

Operational control separation gate: positive-control mean target–peptide ipTM minus scrambled-control mean must be at least 0.15, and the positive must exceed the negative on at least two of three paired seeds. This is an a priori screening rule, not a statistical significance threshold or a validated binding assay. If the controls fail, stop validation and report failure without selecting a new scramble or a favorable subset of seeds.

After a passing control calibration, select up to 50 candidates using the predeclared built-in generator filter score and sequence deduplication. For validation, sort descending mean target–peptide ipTM, then mean interface pLDDT, then stable candidate ID. Missing or failed seeds exclude a candidate from a complete-case rank but remain visible. Do not replace failed seeds automatically. WT-counter-screen up to the top 10 under identical settings; a score difference is a computational hypothesis, not experimentally demonstrated selectivity.

## Budget units

The maximum planned validation units are 150 mutant candidate seed-runs + 6 control seed-runs + 30 WT seed-runs = 186. With a strict under-190 limit there are only three additional units available. The definition is one complex, one seed, one returned sample; provider charging semantics must agree. Built-in generator filtering, calibration, retries and extra samples are separately recorded and never silently excluded from a hosted quota. Self-hosting on Modal is billed in compute time and does not inherit a hosted prediction-count entitlement.

User reported $200 remaining Modal free credits. Reserve $2 for initial ESMC and $10 for BoltzGen calibration; all jobs have single-container limits, finite timeouts and no automatic retries. Reconcile actual usage after each batch before allocating more. These local reservations are not provider-enforced net-spend limits.

A100 access required a payment method, so calibration uses the already available L4. The first environment build unexpectedly upgraded Torch and was corrected with explicit Torch 2.8.0 and cu12 equivariance 0.5.1 constraints. An input-path resolution error was corrected before generation. Both failures and the successful schema rerun are retained. Reserve a further $10 for the six control seed-runs; these six results count toward the 186 planned validation units rather than being repeated later.

## Interpretation and downstream work

Only after passing controls and generating real candidate data proceed to developability and a local draft assay request. Never submit an experiment. Do not invent vendor prices; unavailable quotes are marked pending. Never apply small-molecule pKa/LogD models to these peptides.

Structure figures distinguish crystallographic reference from predictions. RMSD requires an explicitly documented residue/atom correspondence and target superposition; unequal-length peptides cannot be compared through arbitrary residue indexing. Report mapped-core RMSD, coverage, and excluded residues. Confidence, geometric pose recovery, affinity, cell activity and efficacy are distinct claims.
