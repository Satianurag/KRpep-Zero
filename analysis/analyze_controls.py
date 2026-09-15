"""Audit all six frozen Boltz2 controls; no inference, ranking changes or retries."""
from pathlib import Path
import csv, hashlib, json
import gemmi
import numpy as np

R = Path(__file__).resolve().parents[1]
SOURCE = R / 'results/boltz-control-calibration-002/extracted'
OUT = R / 'results/controls'
control_manifest = json.loads((OUT/'controls.json').read_text())
controls = {x['id']: x for x in control_manifest['controls']}
target = ''.join((R/'target.fasta').read_text().splitlines()[1:])
metadata = json.loads((SOURCE/'metadata.json').read_text())
assert metadata['error'] is None, metadata['error']
assert len(metadata['commands']) == 6
assert all(c['exit_code'] == 0 for c in metadata['commands'])
ref = gemmi.read_structure(str(R/'results/target/5xco-reference.cif'))[0]

def heavy(residue):
    return [a for a in residue if not a.element.is_hydrogen and a.occ > 0 and a.altloc in ('\x00', 'A')]

def atom(chain, residue, name):
    matches = [a for r in chain if r.seqid.num == residue for a in heavy(r) if a.name == name]
    assert len(matches) == 1, (chain.name, residue, name, len(matches))
    return matches[0]

def ca(chain, positions):
    return np.array([list(atom(chain, p, 'CA').pos) for p in positions])

rows, audits = [], []
for seed in (17, 42, 101):
    for name in sorted(controls):
        run = SOURCE/f'{name}-seed-{seed}'
        files = list(run.glob('**/confidence_*_model_0.json'))
        assert len(files) == 1
        conf_path = files[0]
        conf = json.loads(conf_path.read_text())
        cif_path = conf_path.parent/f'{name}_model_0.cif'
        st = gemmi.read_structure(str(cif_path))
        assert len(st) == 1
        m = st[0]
        assert [c.name for c in m] == ['A','B','C','D','E']
        sequences = {c.name: ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in c) for c in m if c.name in ('A','B')}
        assert sequences == {'A':target, 'B':controls[name]['sequence']}, sequences
        assert [r.seqid.num for r in m['A']] == list(range(1,170))
        assert [r.seqid.num for r in m['B']] == list(range(1,20))
        assert [(c.name,r.name) for c in m for r in c if c.name in ('C','D','E')] == [('C','GDP'),('D','ACE'),('E','NH2')]
        # The parsed structure ties confidence indices to exact chain identities.
        parsed = list(run.glob('**/processed/structures/*.npz'))
        assert len(parsed) == 1
        with np.load(parsed[0],allow_pickle=False) as data:
            mapping = {str(c['name']):int(c['asym_id']) for c in data['chains']}
        assert mapping == {'A':0,'B':1,'C':2,'D':3,'E':4}, mapping
        pair = conf['pair_chains_iptm']
        forward, reverse = float(pair['0']['1']), float(pair['1']['0'])
        assert all(np.isfinite(v) and 0 <= v <= 1 for v in (forward,reverse))
        contacts = []
        interface = {'A':set(),'B':set()}
        for a in m['A']:
            for b in m['B']:
                distance = min(x.pos.dist(y.pos) for x in heavy(a) for y in heavy(b))
                if distance <= 4:
                    interface['A'].add(a.seqid.num); interface['B'].add(b.seqid.num)
                    contacts.append({'target_residue':a.seqid.num,'peptide_residue':b.seqid.num,'minimum_heavy_atom_distance_A':distance})
        # Official writer serializes residue pLDDT as B_iso = pLDDT * 100.
        values = [float(atom(m[c],p,'CA').b_iso) for c in ('A','B') for p in sorted(interface[c])]
        assert all(np.isfinite(v) and 0 <= v <= 100 for v in values)
        lengths = {
            'Cys5_SG_Cys15_SG_A': atom(m['B'],5,'SG').pos.dist(atom(m['B'],15,'SG').pos),
            'ACE_C_peptide1_N_A': atom(m['D'],1,'C').pos.dist(atom(m['B'],1,'N').pos),
            'peptide19_C_NH2_N_A': atom(m['B'],19,'C').pos.dist(atom(m['E'],1,'N').pos),
        }
        # Distances are reported as diagnostics; no new fitted geometry gate is added.
        pose = {}
        if name == 'KRpep-2d':
            moving, fixed = ca(m['A'],range(1,170)), ca(ref['A'],range(1,170))
            mc, fc = moving.mean(axis=0), fixed.mean(axis=0)
            u, _, vt = np.linalg.svd((moving-mc).T @ (fixed-fc))
            correction = np.eye(3); correction[2,2] = np.linalg.det(u @ vt)
            rotation = u @ correction @ vt
            def rmsd(mob,reference):
                return float(np.sqrt(np.mean(np.sum(((mob-mc)@rotation+fc-reference)**2,axis=1))))
            pose = {'target_CA_169_RMSD_A':rmsd(moving,fixed),
                    'positive_peptide_CA_19_RMSD_A':rmsd(ca(m['B'],range(1,20)),ca(ref['B'],range(1,20))),
                    'positive_core_CA_5_to_15_RMSD_A':rmsd(ca(m['B'],range(5,16)),ca(ref['B'],range(5,16)))}
        row = {'control_id':name,'seed':seed,'pair_iptm_A_to_B':forward,'pair_iptm_B_to_A':reverse,
               'pair_iptm_mean':(forward+reverse)/2,'interface_CA_plddt_0_to_100':float(np.mean(values)) if values else None,
               'target_interface_residues':len(interface['A']),'peptide_interface_residues':len(interface['B']),
               'global_iptm_not_used_for_gate':conf['iptm'],**lengths,
               'positive_core_CA_5_to_15_RMSD_A':pose.get('positive_core_CA_5_to_15_RMSD_A'),
               'structure':str(cif_path.relative_to(R))}
        rows.append(row)
        audits.append({'id':name,'seed':seed,'chain_indices':mapping,'contacts':contacts,
                       'interface_residues':{k:sorted(v) for k,v in interface.items()},'geometry':lengths,'reference_pose_diagnostic':pose,
                       'confidence_sha256':hashlib.sha256(conf_path.read_bytes()).hexdigest(),
                       'cif_sha256':hashlib.sha256(cif_path.read_bytes()).hexdigest()})

positive = [r['pair_iptm_mean'] for r in rows if r['control_id']=='KRpep-2d']
negative = [r['pair_iptm_mean'] for r in rows if r['control_id']!='KRpep-2d']
deltas = np.array(positive)-negative
delta = float(np.mean(deltas)); wins = int(np.sum(deltas>0))
passed = delta >= .15 and wins >= 2
summary = {'scope':'six-run control calibration, no novel candidates',
           'protocol':'PROTOCOL.md revision 1; thresholds frozen before inference',
           'positive_mean_pair_iptm':float(np.mean(positive)), 'scramble_mean_pair_iptm':float(np.mean(negative)),
           'positive_minus_scramble':delta,'paired_seed_differences':dict(zip(['17','42','101'],map(float,deltas))),
           'positive_higher_seed_count':wins,'required_mean_gap':.15,'required_seed_wins':2,
           'passed':passed,'decision':'PROCEED' if passed else 'STOP_CONTROL_GATE_FAILED',
           'completed_validation_units':6,'seeds':[17,42,101],
           'limitations':['The scramble is not an experimentally established nonbinder.',
                         'ipTM is model confidence, not an affinity or activity measurement.',
                         'Possible training-set overlap with the reference limits interpretation of positive pose recovery.',
                         'No new scramble, cherry-picked seed or relaxed gate is permitted.']}
with (OUT/'per-seed.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(OUT/'structure-audit.json').write_text(json.dumps(audits,indent=2)+'\n')
(OUT/'gate-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
