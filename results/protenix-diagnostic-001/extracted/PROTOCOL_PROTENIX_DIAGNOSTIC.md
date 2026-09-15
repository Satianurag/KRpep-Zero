# Independent Protenix-v2 control diagnostic

Frozen 14 September 2026 before any Protenix neural outputs. This is an exploratory extension, not a replacement of either failed Boltz protocol or a newly validated discovery gate.

## Question and input
Can an independent, higher-capacity model recover the known KRpep-2d pose with the verified complete molecular graph? Report the same proposed scramble descriptively, without asserting an experimental nonbinder label.

Use the existing two exact SMILES graphs (179 heavy atoms, 183 bonds, 20 stereocenters), KRAS4B G12D residues 1–169 and GDP. Reuse the saved target MSA. No experimental target/peptide coordinates, contacts or templates are provided. SMILES and mapping hashes are recorded before execution. The original 5XCO complex predates the reported training cutoff (2021-09-30), so this is reference recovery with possible training overlap, not an independent out-of-distribution test.

## Model and fixed computation
Protenix-v2, upstream commit 4c355be4553512f72453ecbfb65e69f4c35d1413, ~464M parameters. Seeds 17, 42, 101; one sample per identity/seed; ten recycles; 200 diffusion steps; BF16 defaults with reference torch triangle kernels and fused diffusion disabled for portability. Six predictions total, all retained. No automatic inference retries or alternate models selected after observing outcomes. Downloaded weight/component SHA-256 hashes and installed requirements will be retained.

Modal A100-80GB, one container, 4 CPU, 32 GiB, 2700-second function ceiling, 2400-second inference/download subprocess ceiling, no idle deployment. Current listed hourly compute cost is about $2.946 including CPU/RAM, or $2.21 for 45 minutes; reserve $5 of the user-confirmed $200 free credits for this attempt including setup. No new paid spend. Current account meter before launch: $1.04635863; billed $0. Meter is delayed and does not independently report remaining credit balance.

## Analysis and interpretation
Verify target sequence and atom correspondence from actual generated outputs. For KRpep-2d report each seed's target-fitted C-alpha RMSD for residues 5–15 and all 1–19; native residue contact recovery at 5 angstrom; peptide bond/stereochemistry checks where exact atom mapping is recovered. Report all model confidence values with their own definitions. Do not treat confidence as KD, compare its scale directly to Boltz, or impose a positive-reference RMSD on the scramble.

There is no new pass threshold and no candidate advancement in this diagnostic. Results, errors and missing outputs are retained. A better known-reference pose does not establish binder discrimination, mutant selectivity or therapeutic activity. The main design screen remains conditional on an independently defensible benchmark. Total recorded control prediction units would become 18 if all six complete.

## Infrastructure amendment before neural outputs

The A100-80GB dispatch was rejected by Modal because the workspace has no payment method. The image build completed but no GPU function or neural prediction ran. Use the same model, inputs, seeds and settings on L4 (24 GB), previously available in this workspace. No scientific parameters change. The L4 + CPU/RAM listed hourly estimate is $1.246, or $0.935 for the unchanged 45-minute ceiling. This is a pre-inference infrastructure repair, not a retry after inspecting scientific outputs. Original rejected app: ap-GZBDbmzoatzd3dp6UcIJI6.
