"""Build a result report without changing the declared protocol."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]
g=json.loads((R/'results/controls/gate-summary.json').read_text())
rows=list(csv.DictReader((R/'results/controls/per-seed.csv').open()))
table='\n'.join(f"| {r['control_id']} | {r['seed']} | {float(r['pair_iptm_mean']):.6f} | {float(r['interface_CA_plddt_0_to_100']):.2f} | {float(r['peptide19_C_NH2_N_A']):.3f} |" for r in rows)
report=f'''# KRpep-Zero: control calibration failed

The frozen positive-versus-scramble gate failed. Further generation, candidate ranking, WT counter-screening, developability and assay drafting are stopped. This report records a failed computational calibration, not evidence that a new peptide binds KRAS.

## Decision and all six seeds

Mean target–peptide pair ipTM: KRpep-2d **{g['positive_mean_pair_iptm']:.6f}**, proposed scramble **{g['scramble_mean_pair_iptm']:.6f}**. Positive minus scramble **{g['positive_minus_scramble']:+.6f}**, against the predeclared minimum **+0.150**. Positive exceeds scramble in **{g['positive_higher_seed_count']}/3** paired seeds; the mean-gap criterion still fails. No seeds were dropped or repeated, and no new scramble or threshold was substituted.

| Molecule | Seed | Pair ipTM | Interface Cα pLDDT (0–100) | Terminal C–N (Å) |
|---|---:|---:|---:|---:|
{table}

Pair ipTM is the arithmetic mean of the A→B and B→A fields after checking parsed A=0/B=1 identities. Global ipTM also includes GDP and caps and is not used for this gate. Interface pLDDT averages unique protein Cα residues participating in A–B heavy-atom contacts ≤4 Å, excluding GDP and caps. The raw directional fields, structures, per-residue contact lists and confidence hashes are retained.

## Additional diagnostics

For KRpep-2d seeds 17/42/101, mapped peptide-core Cα RMSD is **0.426 / 21.470 / 0.515 Å** against 5XCO. All 169 target Cα atoms establish the least-squares rigid transform; peptide positions 5–15 supply 11 exact corresponding Cα atoms without a second fit. This is a positive-control core diagnostic, not a new-design interface RMSD. Seed 42 has the highest positive-control confidence but an off-reference pose. All three seeds remain reported. Training-set overlap with 5XCO may contribute to recovery in the other seeds.

ACE/NH2 component identities and the three intended bond endpoints passed the pinned official parser. Predicted terminal bond lengths nevertheless include severe compression (minimum C-terminal C–N approximately 0.725 Å). Input connectivity support therefore did not guarantee physically credible cap geometry. These post-run diagnostics reinforce the need to revise the method; they do not replace or relax the frozen gate.

The scramble was a proposed negative control, not an experimentally demonstrated nonbinder. This run cannot determine whether overlap reflects model limitations, cap/constraint behavior, actual scramble binding, or several factors. Confidence is not affinity. A revised campaign would need an independently justified negative-control set and chemically credible modeling, declared before any new inference; the current results must remain labeled failed.

## Generation and remaining scope

Two BoltzGen technical-calibration structures were produced; **0/2 passed built-in filters**. Their 15- and 13-residue sequences, GDP retention, cyclic-closure measurements and raw filter outputs are preserved. The planned primary 60-design campaign was not run. Files exported into the provider's `final_ranked_designs` directory do not override `pass_filters=False`. These structures are not selected hits.

ESMC technical QC passed for both 169-residue targets. The six controls used seeds 17,42,101 under identical pinned Boltz 2.2.1 settings, GDP, caps, disulfide, MSA policy, 3 recycles and 200 diffusion steps. No affinity inference was requested. All six outputs completed on one Modal L4 in a 686.08-second remote function, excluding image preparation. All campaign GPU apps subsequently reported stopped.

The latest local Modal account snapshot reported **$0 billed**, $0.40 credits applied, and $0.74947587 metered including storage adjustments. This is an account-level snapshot, subject to metering delay, not an exact campaign invoice or independently verified remaining-credit balance. No additional compute is launched after this gate failure.

## Artifacts and reproducibility

- `results/controls/per-seed.csv`: all six confidence and geometry rows.
- `results/controls/gate-summary.json`: thresholds, observed gaps and STOP decision.
- `results/controls/structure-audit.json`: chain mapping, contacts, hashes and pose diagnostics.
- `results/boltz-control-calibration-002/extracted/`: raw inputs, predictions, logs and pinned runtime metadata.
- `results/boltzgen-calibration-003/`: two-design calibration and rejected filter outputs.
- `results/figures/control-calibration.png` and `.svg`: all-seed diagnostic figure.
- `PROTOCOL.md`: preserved pre-inference decision rules.

Run `python analysis/reproduce.py` in the documented analysis environment to rebuild saved-data analyses, figures and dashboard with no API calls or model inference. Named native sequence-viewer control succeeded. Native structure-viewer recovery encountered a mount/acknowledgment timeout; no successful native comparison render or movie is claimed. The existing local dashboard retains its previously generated 3Dmol experimental-reference view.
'''
(R/'results/CALIBRATION_REPORT.md').write_text(report)
print('Wrote calibration failure report.')
