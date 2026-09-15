"""Deterministic structural audit of the six saved KRpep-2d positive poses.

This is an audit only: it does not rank poses or add a validation gate.  The
reported contact, clash, and omega quantities are explicitly custom metrics.
"""
from pathlib import Path
import argparse, csv, hashlib, json, pickle
import gemmi
import numpy as np

R = Path(__file__).resolve().parents[1]
SEEDS = (17, 42, 101)
RUNS = {
    "v1": R / "results/boltz-control-calibration-002/extracted",
    "v2": R / "results/control-remediation-v2-002/extracted",
}
OUT = R / "results/pose-audit"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def heavy(res):
    return [a for a in res if not a.element.is_hydrogen and a.occ > 0 and a.altloc in ("\x00", "A")]

def atom(res, name):
    xs = [a for a in heavy(res) if a.name == name]
    if len(xs) != 1:
        raise AssertionError((res.name, res.seqid.num, name, len(xs)))
    return xs[0]

def xyz(a):
    return np.array(list(a.pos), dtype=float)

def ca(chain, positions):
    return np.array([list(atom(next(r for r in chain if r.seqid.num == p), "CA").pos) for p in positions])

def fit_transform(moving, fixed):
    mc, fc = moving.mean(0), fixed.mean(0)
    u, _, vt = np.linalg.svd((moving - mc).T @ (fixed - fc))
    d = np.eye(3); d[2, 2] = np.linalg.det(u @ vt)
    return mc, fc, u @ d @ vt

def rmsd(moving, fixed, mc, fc, rot):
    fitted = (moving - mc) @ rot + fc
    return float(np.sqrt(np.mean(np.sum((fitted - fixed) ** 2, axis=1))))

def dihedral(a, b, c, d):
    b0 = -(b-a); b1 = c-b; b2 = d-c
    b1 /= np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1)*b1; w = b2 - np.dot(b2, b1)*b1
    return float(np.degrees(np.arctan2(np.dot(np.cross(b1, v), w), np.dot(v, w))))

def pair_contacts(target, peptide):
    """Residue-pair contact set: any primary-altloc heavy pair <=5 A."""
    out = set()
    for tr in target:
        tx = np.array([list(a.pos) for a in heavy(tr)])
        for pidx, pr in enumerate(peptide, 1):
            px = np.array([list(a.pos) for a in heavy(pr)])
            if len(tx) and len(px) and np.linalg.norm(tx[:, None, :] - px[None, :, :], axis=-1).min() <= 5.0:
                out.add((tr.seqid.num, getattr(pr, "seqid", None).num if hasattr(pr, "seqid") else pidx))
    return out

def clash_stats(target, peptide):
    tx = np.array([list(a.pos) for r in target for a in heavy(r)])
    px = np.array([list(a.pos) for r in peptide for a in heavy(r)])
    d = np.linalg.norm(tx[:, None, :] - px[None, :, :], axis=-1)
    return int(np.sum(d < 2.0)), float(d.min())

def residue_proxy(chain, p, names):
    """Create a residue-like atom collection for v2's one-residue ligand."""
    return [names[p][n] for n in names.get(p, {})]

def circular_delta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)

assert circular_delta(179.0, -179.0) == 2.0
assert circular_delta(180.0, -180.0) == 0.0

reference = gemmi.read_structure(str(R / "results/target/5xco-reference.cif"))[0]
ref_target = [r for r in reference["A"] if 1 <= r.seqid.num <= 169]
ref_peptide = [r for r in reference["B"] if 1 <= r.seqid.num <= 19]
target_sequence = "".join((R / "target.fasta").read_text().splitlines()[1:])
ref_native_contacts = pair_contacts(ref_target, ref_peptide)

rows = []
audits = []
positive_cifs = []
input_hashes = {"reference_cif": sha256(R / "results/target/5xco-reference.cif"),
                "script": sha256(Path(__file__))}
atom_map_path = R / "results/remediation/full-molecule/KRpep-2d.atom-map.json"
input_hashes["target_fasta"] = sha256(R / "target.fasta")
input_hashes["v2_atom_map"] = sha256(atom_map_path)
v2_map = json.loads(atom_map_path.read_text())

for version, base in RUNS.items():
    for seed in SEEDS:
        folder = base / f"KRpep-2d-seed-{seed}" / "boltz_results_KRpep-2d"
        conf_path = next((folder / "predictions").glob("**/confidence_*_model_0.json"))
        cif_path = conf_path.parent / "KRpep-2d_model_0.cif"
        model = gemmi.read_structure(str(cif_path))[0]
        assert [c.name for c in model][:2] == ["A", "B"]
        model_target = [r for r in model["A"] if 1 <= r.seqid.num <= 169]
        assert len(model_target) == 169 and [r.seqid.num for r in model_target] == list(range(1, 170))
        assert "".join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in model_target) == target_sequence
        positive_cifs.append(cif_path)
        if version == "v1":
            model_peptide = [r for r in model["B"] if 1 <= r.seqid.num <= 19]
            by_res = {r.seqid.num: r for r in model_peptide}
            pred_residues = [by_res[p] for p in range(1, 20)]
            atom_lookup = None
        else:
            ligand = model["B"][0]
            by_name = {a.name: a for a in heavy(ligand)}
            proc = folder / "processed"
            mol_path = proc / "mols" / "KRpep-2d.pkl"
            with mol_path.open("rb") as fh:
                molecule = next(m for m in pickle.load(fh).values() if m.GetNumHeavyAtoms() == 179)
            input_hashes[f"{version}_{seed}_processed_molecule"] = sha256(mol_path)
            assert molecule.GetNumAtoms() == 179
            assert len(v2_map) == molecule.GetNumAtoms()
            for e in v2_map:
                rd_atom = molecule.GetAtomWithIdx(int(e["smiles_atom_index"]))
                assert rd_atom.GetProp("name") == e["boltz_atom_name"]
                assert rd_atom.GetSymbol() == e["element"]
            assert set(by_name) == {a.GetProp("name") for a in molecule.GetAtoms()}
            atom_lookup = {p: {} for p in range(1, 20)}
            for e in v2_map:
                p = int(e["peptide_author_residue"])
                if 1 <= p <= 19:
                    assert e["boltz_atom_name"] in by_name
                    atom_lookup[p][e["atom_name"]] = by_name[e["boltz_atom_name"]]
            pred_residues = [residue_proxy(model["B"], p, atom_lookup) for p in range(1, 20)]

        moving, fixed = ca(model["A"], range(1, 170)), ca(reference["A"], range(1, 170))
        mc, fc, rot = fit_transform(moving, fixed)
        if version == "v1":
            pred_ca = {p: xyz(atom(pred_residues[p-1], "CA")) for p in range(1, 20)}
        else:
            pred_ca = {p: xyz(atom_lookup[p]["CA"]) for p in range(1, 20)}
        ref_ca = {p: np.array(list(atom(next(r for r in ref_peptide if r.seqid.num == p), "CA").pos)) for p in range(1,20)}
        pred_ca_arr = np.array([pred_ca[p] for p in range(1,20)])
        ref_ca_arr = np.array([ref_ca[p] for p in range(1,20)])
        all_rmsd = rmsd(pred_ca_arr, ref_ca_arr, mc, fc, rot)
        core_idx = [p-1 for p in range(5,16)]
        core_rmsd = rmsd(pred_ca_arr[core_idx], ref_ca_arr[core_idx], mc, fc, rot)
        pred_target_contacts = pair_contacts(model_target, pred_residues)
        native_n = len(ref_native_contacts)
        recovered = len(ref_native_contacts & pred_target_contacts)
        predicted_n = len(pred_target_contacts)
        clashes, min_dist = clash_stats(model_target, pred_residues)
        omegas = []
        native_omegas = []
        for p in range(1, 19):
            r1 = pred_residues[p-1] if version == "v1" else None
            if version == "v1":
                r2 = next(r for r in pred_residues if r.seqid.num == p+1)
                omegas.append(dihedral(xyz(atom(r1,"CA")), xyz(atom(r1,"C")), xyz(atom(r2,"N")), xyz(atom(r2,"CA"))))
            else:
                omegas.append(dihedral(xyz(atom_lookup[p]["CA"]), xyz(atom_lookup[p]["C"]), xyz(atom_lookup[p+1]["N"]), xyz(atom_lookup[p+1]["CA"])))
            nr1 = next(r for r in ref_peptide if r.seqid.num == p); nr2 = next(r for r in ref_peptide if r.seqid.num == p+1)
            native_omegas.append(dihedral(xyz(atom(nr1,"CA")), xyz(atom(nr1,"C")), xyz(atom(nr2,"N")), xyz(atom(nr2,"CA"))))
        def state(x):
            ax = abs(x)
            return "cis" if ax <= 30 else ("trans" if ax >= 150 else "intermediate")
        row = {"version":version,"seed":seed,"positive_id":"KRpep-2d",
               "target_fitted_all19_CA_RMSD_A":all_rmsd,"target_fitted_core5_15_CA_RMSD_A":core_rmsd,
               "native_contact_count":native_n,"predicted_contact_count":predicted_n,
               "native_contact_recovered":recovered,"native_contact_recovery_fraction":(recovered/native_n if native_n else None),
               "predicted_contact_precision":(recovered/predicted_n if predicted_n else None),
               "interchain_atom_pairs_lt2A":clashes,"interchain_min_heavy_distance_A":min_dist,
               "omega_native_cis":sum(state(x)=="cis" for x in native_omegas),"omega_native_trans":sum(state(x)=="trans" for x in native_omegas),
               "omega_predicted_cis":sum(state(x)=="cis" for x in omegas),"omega_predicted_trans":sum(state(x)=="trans" for x in omegas),
               "omega_abs_diff_mean_deg":float(np.mean([circular_delta(a,b) for a,b in zip(omegas,native_omegas)])),
               "structure":str(cif_path.relative_to(R))}
        rows.append(row)
        for key,path in [(f"{version}_{seed}_cif",cif_path),(f"{version}_{seed}_confidence",conf_path)]: input_hashes[key]=sha256(path)
        audits.append({"version":version,"seed":seed,"row":row,"native_contact_pairs":sorted(ref_native_contacts),"predicted_contact_pairs":sorted(pred_target_contacts),"omega_predicted_deg":omegas,"omega_native_deg":native_omegas})

# Negative controls are deliberately limited to the requested geometric clash
# diagnostic; no sequence-specific pose correspondence is imposed on them.
for version, base in RUNS.items():
    map_path = R / "results/remediation/full-molecule/SCRAMBLE-20260914.atom-map.json"
    neg_map = json.loads(map_path.read_text()) if version == "v2" else None
    input_hashes["v2_scramble_atom_map"] = sha256(map_path)
    for seed in SEEDS:
        folder = base / f"SCRAMBLE-20260914-seed-{seed}" / "boltz_results_SCRAMBLE-20260914"
        conf_path = next((folder / "predictions").glob("**/confidence_*_model_0.json"))
        cif_path = conf_path.parent / "SCRAMBLE-20260914_model_0.cif"
        model = gemmi.read_structure(str(cif_path))[0]
        model_target = [r for r in model["A"] if 1 <= r.seqid.num <= 169]
        if version == "v1":
            peptide = [r for r in model["B"] if 1 <= r.seqid.num <= 19]
        else:
            ligand = model["B"][0]; by_name = {a.name:a for a in heavy(ligand)}
            mol_path = folder / "processed/mols/SCRAMBLE-20260914.pkl"
            with mol_path.open("rb") as fh:
                molecule = next(m for m in pickle.load(fh).values() if m.GetNumHeavyAtoms() == 179)
            assert len(neg_map) == molecule.GetNumAtoms() == 179
            for e in neg_map:
                rd_atom = molecule.GetAtomWithIdx(int(e["smiles_atom_index"]))
                assert rd_atom.GetProp("name") == e["boltz_atom_name"]
                assert rd_atom.GetSymbol() == e["element"]
            assert set(by_name) == {a.GetProp("name") for a in molecule.GetAtoms()}
            input_hashes[f"{version}_{seed}_scramble_processed_molecule"] = sha256(mol_path)
            lookup = {p:{} for p in range(1,20)}
            for e in neg_map:
                p = int(e["peptide_author_residue"])
                if 1 <= p <= 19: lookup[p][e["atom_name"]] = by_name[e["boltz_atom_name"]]
            peptide = [residue_proxy(model["B"], p, lookup) for p in range(1,20)]
        clashes, min_dist = clash_stats(model_target, peptide)
        row = {k: None for k in rows[0]}
        row.update({"version":version,"seed":seed,"positive_id":"SCRAMBLE-20260914",
                    "interchain_atom_pairs_lt2A":clashes,"interchain_min_heavy_distance_A":min_dist,
                    "structure":str(cif_path.relative_to(R))})
        rows.append(row)
        input_hashes[f"{version}_{seed}_scramble_cif"] = sha256(cif_path)
        audits.append({"version":version,"seed":seed,"row":row,"scope":"negative clash-only diagnostic"})

assert len(positive_cifs) == 6 and len(set(positive_cifs)) == 6
assert len({sha256(p) for p in positive_cifs}) == 6
assert len(rows) == len(audits) == 12
assert all(0 <= r["omega_abs_diff_mean_deg"] <= 180 for r in rows if r["positive_id"] == "KRpep-2d")

OUT.mkdir(exist_ok=True)
with (OUT / "pose-audit.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(OUT / "pose-audit.json").write_text(json.dumps({"metric_definitions":{"native_contacts":"target residue 1-169 vs peptide residue 1-19; any primary-altloc heavy atom pair <=5 A","interchain_clashes":"all target/peptide primary-altloc heavy atom pairs <2 A; geometric diagnostic, not clash energy","omega":"dihedral(CA_i,C_i,N_i+1,CA_i+1); cis abs(angle)<=30 deg, trans abs(angle)>=150 deg, otherwise intermediate"},"input_sha256":input_hashes,"audits":audits}, indent=2) + "\n")
(OUT / "README.md").write_text("# Saved positive-pose audit\n\nDeterministic metrics for all six KRpep-2d positive predictions (v1/v2; seeds 17, 42, 101) against 5XCO. Target fitting uses residues 1–169. Peptide metrics use residues 1–19 and exclude ACE/NH2/GDP. Contact recovery is a custom F_nat-like residue-pair metric at a 5 Å heavy-atom cutoff. Pairs under 2 Å are reported as a geometric diagnostic, not a chemical clash-energy result. Omega states use cis ≤30° and trans ≥150° by absolute dihedral angle; intermediate values are retained. No threshold or decision gate is added. Input SHA-256 hashes are recorded in `pose-audit.json`.\n")
print(json.dumps({"rows":len(rows),"output":str(OUT)}, indent=2))
