"""Audit Protenix diagnostic outputs without introducing a candidate gate."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json
import numpy as np
import gemmi
from rdkit import Chem
from molecular_geometry import check_geometry
R=Path(__file__).resolve().parents[1]
base=R/'results/protenix-base-default-diagnostic-001/extracted';out=base.parent/'analysis'
meta=json.loads((base/'metadata.json').read_text())
assert meta['error'] is None and meta['source_commit']=='4c355be4553512f72453ecbfb65e69f4c35d1413'
assert meta['model']=='protenix_base_default_v1.0.0'
assert hashlib.sha256((base/'PROTOCOL_PROTENIX_DIAGNOSTIC.md').read_bytes()).hexdigest()==meta['protocol_sha256']
ref=gemmi.read_structure(str(R/'results/target/5xco-reference.cif'))[0]
seq=''.join((R/'target.fasta').read_text().splitlines()[1:])
items=json.loads((R/'results/remediation/full-molecule/graphs.json').read_text())['controls']
def heavy(res):return [a for a in res if not a.element.is_hydrogen and a.occ>0 and a.altloc in ('\x00','A')]
def ca(chain,ps):return np.array([list(next(a for r in chain if r.seqid.num==p for a in heavy(r) if a.name=='CA').pos) for p in ps])
def contacts(target,peptide):
    return {(t.seqid.num,p) for t in target for p,xyz in peptide.items() if np.linalg.norm(np.array([list(a.pos) for a in heavy(t)])[:,None,:]-xyz[None,:,:],axis=-1).min()<=5}
refcontacts=contacts([r for r in ref['A'] if 1<=r.seqid.num<=169],{r.seqid.num:np.array([list(a.pos) for a in heavy(r)]) for r in ref['B'] if 1<=r.seqid.num<=19})
assert len(refcontacts)==41
rows=[];audits=[]
for item in items:
    name=item['id'];mol=Chem.MolFromSmiles(item['smiles']);counts=Counter();names=[]
    # Exact naming rule from pinned upstream rdkit_mol_to_atom_info: per-element,
    # one-based counters in SMILES atom order. Every generated CIF is checked.
    for a in mol.GetAtoms():
        el=a.GetSymbol().upper();counts[el]+=1;n=f'{el}{counts[el]}';a.SetProp('name',n);names.append(n)
    mapping={e['smiles_atom_index']:e for e in item['atom_map']}
    proc=R/f'results/control-remediation-v2-002/extracted/{name}-seed-17/boltz_results_{name}/processed'
    with np.load(proc/'constraints'/f'{name}.npz') as p:bounds=p['rdkit_bounds_constraints'].copy()
    with np.load(proc/'structures'/f'{name}.npz') as p:offset=int(next(c['atom_idx'] for c in p['chains'] if c['name']=='B'))
    for seed in [17,42,101]:
        folder=base/'predictions'/name/f'seed_{seed}'
        cifs=list(folder.rglob('*.cif'));confs=list(folder.rglob('*summary_confidence*.json'))
        assert len(cifs)==len(confs)==1,(folder,cifs,confs)
        cif=cifs[0];model=gemmi.read_structure(str(cif))[0]
        assert [c.name for c in model]==['A','B','C']
        target=list(model['A']);assert len(target)==169 and [r.seqid.num for r in target]==list(range(1,170))
        assert ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in target)==seq
        assert len(model['B'])==1 and len(model['C'])==1 and model['C'][0].name=='GDP'
        atoms={a.name:a for a in heavy(model['B'][0])};assert len(atoms)==179 and set(atoms)==set(names)
        assert all(atoms[n].element.atomic_number==mol.GetAtomWithIdx(i).GetAtomicNum() for i,n in enumerate(names))
        coords=np.array([list(atoms[n].pos) for n in names]);assert np.isfinite(coords).all()
        geometry=check_geometry(mol,coords,bounds,offset,item['links'])
        peptide={p:coords[[i for i,e in mapping.items() if e['peptide_author_residue']==p]] for p in range(1,20)}
        row={'control_id':name,'seed':seed,'bonds_in_expanded_bounds':geometry['bonds_within_expanded_bounds'],
             'stereocenters_correct':sum(c['passed'] for c in geometry['stereocenters']),
             'core_CA_RMSD_A':None,'all19_CA_RMSD_A':None,'native_contacts_recovered':None}
        if name=='KRpep-2d':
            mov,fix=ca(model['A'],range(1,170)),ca(ref['A'],range(1,170));mc,fc=mov.mean(0),fix.mean(0)
            u,_,vt=np.linalg.svd((mov-mc).T@(fix-fc));d=np.eye(3);d[2,2]=np.linalg.det(u@vt);rot=u@d@vt
            cais={e['peptide_author_residue']:i for i,e in mapping.items() if e['atom_name']=='CA'}
            for key,ps in [('core_CA_RMSD_A',range(5,16)),('all19_CA_RMSD_A',range(1,20))]:
                fitted=(coords[[cais[p] for p in ps]]-mc)@rot+fc
                row[key]=float(np.sqrt(np.mean(np.sum((fitted-ca(ref['B'],ps))**2,axis=-1))))
            row['native_contacts_recovered']=len(refcontacts & contacts(target,peptide))
        row['structure']=str(cif.relative_to(R));rows.append(row)
        audits.append({'row':row,'geometry':geometry,'model_confidence':json.loads(confs[0].read_text()),'cif_sha256':hashlib.sha256(cif.read_bytes()).hexdigest()})
assert len(rows)==6
out.mkdir(exist_ok=True)
with (out/'per-seed.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'audit.json').write_text(json.dumps({'scope':'Exploratory cross-model diagnostic; no new selection gate','model':meta['model'],'bond_bounds':'Same saved v2 RDKit bounds expanded by 12.5%; diagnostic only, not Protenix confidence','atom_mapping':'Pinned Protenix per-element atom-name rule, with every CIF name and element verified','native_contact_count':41,'audits':audits},indent=2)+'\n')
print(json.dumps(rows,indent=2))
