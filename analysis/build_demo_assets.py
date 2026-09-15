"""Build target-aligned, all-seed display assets from saved predictions only.

No coordinate relaxation, peptide fitting, inference or confidence re-ranking.
Peptide bonds are the declared input graph, not distance-inferred connectivity.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, shutil
import gemmi
import numpy as np
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'dashboard/data/structures'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))

def heavy(res):
    return [a for a in res if not a.element.is_hydrogen and a.occ > 0 and a.altloc in ('\x00', 'A')]

def named(res, name):
    atoms = [a for a in heavy(res) if a.name == name]
    assert len(atoms) == 1, (res.name, res.seqid.num, name)
    return atoms[0]

def target_ca(model):
    residues = [r for r in model['A'] if 1 <= r.seqid.num <= 169]
    assert [r.seqid.num for r in residues] == list(range(1, 170))
    seq = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in residues)
    expected = ''.join((ROOT / 'target.fasta').read_text().splitlines()[1:])
    assert seq == expected
    return np.array([list(named(r, 'CA').pos) for r in residues])

def fit(moving, fixed):
    mc, fc = moving.mean(0), fixed.mean(0)
    u, _, vt = np.linalg.svd((moving - mc).T @ (fixed - fc))
    correction = np.eye(3)
    correction[2, 2] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    assert np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-10)
    assert np.isclose(np.linalg.det(rotation), 1)
    return mc, fc, rotation

def peptide_atoms(model, item, protocol):
    mol = Chem.MolFromSmiles(item['smiles'])
    assert mol.GetNumAtoms() == 179 and mol.GetNumBonds() == 183
    mapping = sorted(item['atom_map'], key=lambda e: e['smiles_atom_index'])
    assert [e['smiles_atom_index'] for e in mapping] == list(range(179))
    if protocol == 'v2':
        saved_map = json.loads((ROOT / f"results/remediation/full-molecule/{item['id']}.atom-map.json").read_text())
        labels = {e['smiles_atom_index']: e['boltz_atom_name'] for e in saved_map}
    elif protocol == 'protenix':
        counts = Counter(); labels = {}
        for i, a in enumerate(mol.GetAtoms()):
            el = a.GetSymbol().upper(); counts[el] += 1
            labels[i] = f'{el}{counts[el]}'
    residues = {r.seqid.num: r for r in model['B']}
    result = []
    for i, e in enumerate(mapping):
        p = e['peptide_author_residue']
        if protocol in ('v2', 'protenix'):
            a = named(model['B'][0], labels[i])
        elif protocol == 'v1' and p in (0, 20):
            a = named(model['D' if p == 0 else 'E'][0], e['atom_name'])
        else:
            a = named(residues[p], e['atom_name'])
        assert a.element.name == e['element'] == mol.GetAtomWithIdx(i).GetSymbol()
        result.append(a)
    assert len({id(a) for a in result}) == 179
    return mol, mapping, result

def build():
    DEST.mkdir(parents=True, exist_ok=True)
    reference_path = ROOT / 'results/target/5xco-reference.cif'
    reference = gemmi.read_structure(str(reference_path))[0]
    fixed = target_ca(reference)
    ref_core = np.array([list(named(next(r for r in reference['B'] if r.seqid.num == p), 'CA').pos) for p in range(5, 16)])
    items = {x['id']: x for x in json.loads((ROOT / 'results/remediation/full-molecule/graphs.json').read_text())['controls']}
    pose = {(r['version'], r['seed']): r for r in read_csv(ROOT / 'results/pose-audit/pose-audit.csv') if r['positive_id'] == 'KRpep-2d'}
    configs = [
        ('v1', 'Boltz · revision 1', 'results/controls/per-seed.csv'),
        ('v2', 'Boltz · revision 2', 'results/control-remediation-v2-002/analysis/per-seed.csv'),
        ('protenix', 'Protenix · base diagnostic', 'results/protenix-base-default-diagnostic-001/analysis/per-seed.csv'),
    ]
    entries = []
    for protocol, label, table_path in configs:
        rows = read_csv(ROOT / table_path)
        assert len(rows) == 6
        for row in sorted(rows, key=lambda r: (r['control_id'] != 'KRpep-2d', int(r['seed']))):
            name, seed = row['control_id'], int(row['seed'])
            item = items[name]
            source = ROOT / row['structure']
            st = gemmi.read_structure(str(source)); model = st[0]
            moving = target_ca(model)
            mc, fc, rot = fit(moving, fixed)
            mol, mapping, atoms = peptide_atoms(model, item, protocol)
            xyz = (np.array([list(a.pos) for a in atoms]) - mc) @ rot + fc
            core_indices = [i for i, e in enumerate(mapping) if e['atom_name'] == 'CA' and 5 <= e['peptide_author_residue'] <= 15]
            core_indices.sort(key=lambda i: mapping[i]['peptide_author_residue'])
            rmsd = None; contacts = None
            if name == 'KRpep-2d':
                rmsd = float(np.sqrt(np.mean(np.sum((xyz[core_indices] - ref_core) ** 2, axis=1))))
                if protocol == 'protenix':
                    expected_rmsd = float(row['core_CA_RMSD_A']); contacts = int(row['native_contacts_recovered'])
                else:
                    audit = pose[(protocol, str(seed))]
                    expected_rmsd = float(audit['target_fitted_core5_15_CA_RMSD_A'])
                    contacts = int(audit['native_contact_recovered'])
                assert abs(rmsd - expected_rmsd) < 1e-7
            display_atoms = []
            for i, (e, a) in enumerate(zip(mapping, atoms)):
                atom = mol.GetAtomWithIdx(i)
                bonds = sorted(atom.GetBonds(), key=lambda b: b.GetOtherAtomIdx(i))
                display_atoms.append({
                    'serial': i + 1, 'index': i, 'elem': e['element'],
                    'atom': e['atom_name'], 'resi': e['peptide_author_residue'],
                    'resn': 'PEP', 'chain': 'B', 'hetflag': True,
                    'x': round(float(xyz[i, 0]), 6), 'y': round(float(xyz[i, 1]), 6), 'z': round(float(xyz[i, 2]), 6),
                    'bonds': [b.GetOtherAtomIdx(i) for b in bonds],
                    'bondOrder': [b.GetBondTypeAsDouble() for b in bonds],
                })
            assert sum(len(a['bonds']) for a in display_atoms) == 366
            # Transform every source atom with the same proper rigid transform.
            for chain in model:
                for residue in chain:
                    for a in residue:
                        new = (np.array(list(a.pos)) - mc) @ rot + fc
                        a.pos = gemmi.Position(*map(float, new))
            target_rmsd = float(np.sqrt(np.mean(np.sum((target_ca(model) - fixed) ** 2, axis=1))))
            # Viewer target is a derived display-only PDB; original CIF is unchanged.
            target_st = gemmi.Structure(); target_model = gemmi.Model('1')
            for chain in model:
                if chain.name in ('A', 'C'):
                    target_model.add_chain(chain.clone())
            target_st.add_model(target_model)
            ident = f"{protocol}-{'positive' if name == 'KRpep-2d' else 'scramble'}-{seed}"
            raw_name = ident + '.cif'; payload_name = ident + '.json'
            shutil.copyfile(source, DEST / raw_name)
            payload = {'target_pdb': target_st.make_pdb_string(), 'peptide_atoms': display_atoms}
            (DEST / payload_name).write_text(json.dumps(payload, separators=(',', ':'), allow_nan=False) + '\n')
            if protocol == 'v2':
                chemistry = 'Measured chemistry passed'
            elif protocol == 'v1':
                chemistry = 'Terminal-cap geometry issue'
            else:
                chemistry = 'Measured chemistry failed'
            entries.append({
                'id': ident, 'protocol': protocol, 'protocol_label': label,
                'control_id': name, 'control_label': 'KRpep-2d' if name == 'KRpep-2d' else 'Proposed scramble',
                'seed': seed, 'sequence': item['sequence'], 'chemistry': chemistry,
                'pair_iptm': float(row['pair_iptm_mean']) if protocol != 'protenix' else None,
                'core_rmsd_A': rmsd, 'native_contacts_recovered': contacts,
                'target_fit_rmsd_A': target_rmsd, 'aligned_target_CA_count': 169,
                'payload': 'data/structures/' + payload_name,
                'raw_cif': 'data/structures/' + raw_name, 'source_cif': row['structure'],
                'source_sha256': sha(source), 'payload_sha256': sha(DEST / payload_name),
                'transform': {'moving_centroid': mc.tolist(), 'reference_centroid': fc.tolist(), 'rotation_row_vectors': rot.tolist()},
            })
    assert len(entries) == 18 and len({e['id'] for e in entries}) == 18
    manifest = {
        'format': 1, 'scope': '18 saved control predictions; no novel designs or inference',
        'alignment': 'Proper rigid least-squares fit on matched target CA residues 1–169. Same transform applied to the entire prediction. No peptide refitting.',
        'connectivity': 'Peptide bonds use the declared full input graph; coordinates are unchanged except rigid alignment. This is not evidence that bond lengths or stereochemistry pass.',
        'rmsd': 'Positive-control CA residues 5–15 after target-only fit (11 atoms); not DockQ or affinity. No residue-equivalence metric is assigned to the scrambled molecule.',
        'reference_sha256': sha(reference_path), 'entries': entries,
    }
    (ROOT / 'dashboard/data/predictions.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    print('Built and validated 18 all-seed overlays; exact positive RMSDs match saved audits.')
    return manifest

if __name__ == '__main__':
    build()
