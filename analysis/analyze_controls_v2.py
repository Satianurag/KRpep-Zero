"""Evaluate all preregistered full-graph controls; never overwrite revision 1."""
from pathlib import Path
import argparse,csv,hashlib,json,pickle
import numpy as np
import gemmi
from rdkit import Chem
from molecular_geometry import check_geometry

R=Path(__file__).resolve().parents[1]
arg=argparse.ArgumentParser();arg.add_argument('--run-dir',default='results/control-remediation-v2-002');args=arg.parse_args()
run=R/args.run_dir;base=run/'extracted';out=run/'analysis';out.mkdir(exist_ok=True)
metadata=json.loads((base/'metadata.json').read_text())
assert metadata['error'] is None and len(metadata['commands'])==6,metadata.get('error')
assert all(c['exit_code']==0 for c in metadata['commands'])
assert hashlib.sha256((base/'PROTOCOL_REMEDIATION_V2.md').read_bytes()).hexdigest()==metadata['protocol_sha256']
preregistered=json.loads((R/'results/remediation/preregistration-v2.json').read_text())
assert metadata['protocol_sha256']==preregistered['protocol_sha256']
assert metadata['code_revision']=='b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc'
assert metadata['weights_revision']=='6fdef46d763fee7fbb83ca5501ccceff43b85607'
assert metadata['affinity_inference_requested'] is False
graphs=json.loads((R/'results/remediation/full-molecule/graphs.json').read_text())
items={x['id']:x for x in graphs['controls']}
assert set(items)=={'KRpep-2d','SCRAMBLE-20260914'}
assert {c['id'] for c in metadata['commands']}=={f'{name}-seed-{seed}' for name in items for seed in (17,42,101)}
reference=gemmi.read_structure(str(R/'results/target/5xco-reference.cif'))[0]
target_sequence=''.join((R/'target.fasta').read_text().splitlines()[1:])

def ca(chain,positions):
    return np.array([list(next(a for r in chain if r.seqid.num==p for a in r if a.name=='CA' and a.altloc in ('\x00','A')).pos) for p in positions])

rows=[];audit=[]
for seed in (17,42,101):
    for name,item in sorted(items.items()):
        folder=base/f'{name}-seed-{seed}'/f'boltz_results_{name}';proc=folder/'processed'
        actual_hashes={str(p.relative_to(proc)):hashlib.sha256(p.read_bytes()).hexdigest() for p in proc.rglob('*') if p.is_file()}
        assert actual_hashes==metadata['fixed_preprocessing_hashes'][name],f'{name} {seed}: preprocessing hashes differ'
        files=list((folder/'predictions').glob('**/confidence_*_model_0.json'));assert len(files)==1
        confpath=files[0];confidence=json.loads(confpath.read_text());cif=confpath.parent/f'{name}_model_0.cif'
        model=gemmi.read_structure(str(cif))[0];assert [c.name for c in model]==['A','B','C']
        seq=''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in model['A'])
        assert seq==target_sequence and len(model['A'])==169
        assert [r.seqid.num for r in model['A']]==list(range(1,170))
        assert all(r.seqid.icode in (' ','\x00') for r in model['A'])
        assert len(model['B'])==1 and len(model['C'])==1 and model['C'][0].name=='GDP'
        with np.load(proc/'structures'/f'{name}.npz') as p:
            chainmap={str(c['name']):int(c['asym_id']) for c in p['chains']}
            offset=int(next(c['atom_idx'] for c in p['chains'] if c['name']=='B'))
            processed_atoms=p['atoms'].copy()
        assert chainmap=={'A':0,'B':1,'C':2}
        with (proc/'mols'/f'{name}.pkl').open('rb') as f:molecule=next(m for m in pickle.load(f).values() if m.GetNumHeavyAtoms()==179)
        original=Chem.MolFromSmiles(item['smiles'])
        assert Chem.MolToSmiles(molecule,isomericSmiles=True)==Chem.MolToSmiles(original,isomericSmiles=True)
        assert {(b.GetBeginAtomIdx(),b.GetEndAtomIdx(),str(b.GetBondType())) for b in molecule.GetBonds()}=={(b.GetBeginAtomIdx(),b.GetEndAtomIdx(),str(b.GetBondType())) for b in original.GetBonds()}
        atoms={a.name:a for a in model['B'][0] if not a.element.is_hydrogen}
        assert len(atoms)==179 and len(list(model['B'][0]))==179
        names=[a.GetProp('name') for a in molecule.GetAtoms()]
        assert set(names)==set(atoms) and len(set(names))==179
        assert all(atoms[n].element.atomic_number==molecule.GetAtomWithIdx(i).GetAtomicNum() for i,n in enumerate(names))
        assert all(a.occ>0 and a.altloc in ('\x00','A') for a in atoms.values())
        assert all(processed_atoms[offset+i]['name']==n for i,n in enumerate(names))
        coords=np.array([list(atoms[n].pos) for n in names])
        with np.load(proc/'constraints'/f'{name}.npz') as p:bounds=p['rdkit_bounds_constraints']
        geometry=check_geometry(molecule,coords,bounds,offset,item['links'])
        assert len(geometry['stereocenters'])==20
        mapping={e['smiles_atom_index']:e for e in item['atom_map']}
        peptide_residue_indices={p:[i for i,e in mapping.items() if e['peptide_author_residue']==p] for p in range(1,20)}
        ca_indices={e['peptide_author_residue']:i for i,e in mapping.items() if e['atom_name']=='CA'}
        assert set(ca_indices)==set(range(1,20))
        target_interface=set();peptide_interface=set();contacts=[]
        for res in model['A']:
            x=np.array([list(a.pos) for a in res if not a.element.is_hydrogen and a.occ>0 and a.altloc in ('\x00','A')])
            for p,indices in peptide_residue_indices.items():
                distance=float(np.linalg.norm(x[:,None,:]-coords[indices][None,:,:],axis=-1).min())
                if distance<=4:
                    target_interface.add(res.seqid.num);peptide_interface.add(p)
                    contacts.append({'target_residue':res.seqid.num,'peptide_residue':p,'distance_A':distance})
        values=[float(next(a.b_iso for r in model['A'] if r.seqid.num==p for a in r if a.name=='CA')) for p in sorted(target_interface)]
        values += [float(atoms[names[ca_indices[p]]].b_iso) for p in sorted(peptide_interface)]
        assert all(np.isfinite(v) and 0<=v<=100 for v in values)
        pose={}
        if name=='KRpep-2d':
            moving,fixed=ca(model['A'],range(1,170)),ca(reference['A'],range(1,170))
            mc,fc=moving.mean(axis=0),fixed.mean(axis=0)
            u,_,vt=np.linalg.svd((moving-mc).T@(fixed-fc));d=np.eye(3);d[2,2]=np.linalg.det(u@vt);rot=u@d@vt
            for title,positions in [('peptide_CA_1_19',range(1,20)),('core_CA_5_15',range(5,16))]:
                fitted=(coords[[ca_indices[p] for p in positions]]-mc)@rot+fc
                pose[title+'_RMSD_A']=float(np.sqrt(np.mean(np.sum((fitted-ca(reference['B'],positions))**2,axis=-1))))
        pair=confidence['pair_chains_iptm'];forward=float(pair['0']['1']);reverse=float(pair['1']['0'])
        assert all(np.isfinite(v) and 0<=v<=1 for v in (forward,reverse))
        chemistry=geometry['critical_links_passed'] and geometry['stereochemistry_passed']
        row={'control_id':name,'seed':seed,'pair_iptm_0_1':forward,'pair_iptm_1_0':reverse,'pair_iptm_mean':(forward+reverse)/2,
             'mapped_CA_interface_plddt':float(np.mean(values)) if values else None,'chemistry_gate_passed':chemistry,
             'critical_links_passed':geometry['critical_links_passed'],'stereochemistry_passed':geometry['stereochemistry_passed'],
             'fraction_bonds_within_bounds':geometry['fraction_bonds_within_expanded_bounds'],
             'positive_core_CA_RMSD_A':pose.get('core_CA_5_15_RMSD_A'),'structure':str(cif.relative_to(R))}
        rows.append(row);audit.append({'id':name,'seed':seed,'geometry':geometry,'pose':pose,'contacts':contacts,
                                      'confidence_sha256':hashlib.sha256(confpath.read_bytes()).hexdigest(),'cif_sha256':hashlib.sha256(cif.read_bytes()).hexdigest()})
positive=[r['pair_iptm_mean'] for r in rows if r['control_id']=='KRpep-2d'];negative=[r['pair_iptm_mean'] for r in rows if r['control_id']!='KRpep-2d']
delta=np.array(positive)-negative;gap=float(delta.mean());wins=int(sum(delta>0));sep=gap>=.15 and wins>=2;chem=all(r['chemistry_gate_passed'] for r in rows)
summary={'protocol':'revision 2 full-molecule representation','positive_mean_pair_iptm':float(np.mean(positive)),
 'scramble_mean_pair_iptm':float(np.mean(negative)),'positive_minus_scramble':gap,'paired_seed_differences':dict(zip(['17','42','101'],map(float,delta))),
 'required_mean_gap':.15,'positive_higher_seed_count':wins,'required_seed_wins':2,'separation_passed':sep,'chemistry_passed':chem,
 'passed':sep and chem,'decision':'PROCEED_TO_MAIN_GENERATION' if sep and chem else 'STOP_REMEDIATION_GATE_FAILED',
 'completed_v2_validation_units':6,'completed_cumulative_validation_units':12,
 'limitations':['Same original proposed scramble; not experimentally established as a nonbinder.','Do not pool or directly compare confidence with revision 1: tokenization changed.','Confidence and pose are not binding-affinity or biological-activity measurements.']}
with (out/'per-seed.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'structure-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
(out/'gate-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
