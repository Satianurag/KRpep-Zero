"""Check the documented upstream SMILES parser and full-molecule bond bounds."""
from pathlib import Path
import hashlib,json,pickle
from rdkit import Chem,rdBase
from boltz.data.mol import load_canonicals
from boltz.data.parse.schema import parse_boltz_schema
from boltz.data.tokenize.boltz2 import Boltz2Tokenizer
from boltz.data.types import Input

R=Path(__file__).resolve().parents[1]
OUT=R/'results/remediation/full-molecule'
graphs=json.loads((OUT/'graphs.json').read_text())
ccd=load_canonicals(R/'.tools/boltz-assets/mols')
rdBase.SeedRandomNumberGenerator(20260914)
results=[]
for item in graphs['controls']:
    name=item['id'];print('Parsing whole-molecule representation:',name,flush=True)
    target=parse_boltz_schema(name,item['schema'],ccd,mol_dir=R/'.tools/boltz-assets/mols',boltz_2=True)
    st=target.structure;chains={str(c['name']):c for c in st.chains}
    assert list(chains)==['A','B','C']
    binder=chains['B'];assert binder['res_num']==1 and binder['atom_num']==179
    mol=next(m for m in target.extra_mols.values() if m.GetNumHeavyAtoms()==179)
    assert Chem.GetFormalCharge(mol)==8
    original=Chem.MolFromSmiles(item['smiles'])
    assert Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True)==Chem.MolToSmiles(original,isomericSmiles=True)
    assert {(min(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),max(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),str(b.GetBondType())) for b in original.GetBonds()} == {(min(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),max(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),str(b.GetBondType())) for b in mol.GetBonds()}
    atom_map=[]
    for entry in item['atom_map']:
        a=mol.GetAtomWithIdx(entry['smiles_atom_index'])
        assert a.GetSymbol()==entry['element']
        atom_map.append({**entry,'boltz_atom_name':a.GetProp('name'),
                         'global_atom_index':int(binder['atom_idx'])+entry['smiles_atom_index']})
    assert all(st.atoms[e['global_atom_index']]['name']==e['boltz_atom_name'] for e in atom_map)
    constraints=target.residue_constraints
    bounds={tuple(sorted(map(int,c['atom_idxs']))):c for c in constraints.rdkit_bounds_constraints}
    checks=[]
    for bond in mol.GetBonds():
        pair=tuple(sorted(int(binder['atom_idx'])+i for i in (bond.GetBeginAtomIdx(),bond.GetEndAtomIdx())))
        assert pair in bounds and bounds[pair]['is_bond'] and bounds[pair]['lower_bound']>0
    for link in item['links']:
        indices=tuple(sorted(int(binder['atom_idx'])+i for i in link['smiles_indices']))
        b=bounds[indices];assert b['is_bond'] and b['lower_bound']>1.0
        checks.append({**link,'global_indices':indices,'has_bond_bounds':True,'lower_bound_A':float(b['lower_bound']),'upper_bound_A':float(b['upper_bound'])})
    tokens=Boltz2Tokenizer().tokenize(Input(st,{},record=target.record,residue_constraints=constraints,extra_mols=target.extra_mols))
    assert sum(tokens.tokens['asym_id']==1)==179
    st.dump(OUT/f'{name}.parsed.npz');constraints.dump(OUT/f'{name}.constraints.npz')
    (OUT/f'{name}.atom-map.json').write_text(json.dumps(atom_map,indent=2)+'\n')
    # Raw reference conformer from upstream ETKDG, not crystallographic coordinates.
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    with (OUT/f'{name}.mols.pkl').open('wb') as f:pickle.dump(target.extra_mols,f)
    result={'id':name,'chain_residue_counts':{k:int(c['res_num']) for k,c in chains.items()},
            'total_tokens':len(tokens.tokens),'peptide_atom_tokens':179,'critical_bonds':checks,
            'rdkit_constraint_count':len(constraints.rdkit_bounds_constraints),
            'peptide_bonds_checked':mol.GetNumBonds(),
            'chiral_constraint_count':len(constraints.chiral_atom_constraints),
            'input_geometry_scope':'ETKDG conformer and RDKit bounds only; neural prediction not run',
            'affinity_requested':False,'schema_sha256':hashlib.sha256(json.dumps(item['schema'],sort_keys=True).encode()).hexdigest()}
    results.append(result);print(json.dumps(result),flush=True)
(OUT/'parser-qc.json').write_text(json.dumps({'code_revision':'b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc',
 'rdkit_version':rdBase.rdkitVersion,'global_rdkit_rng_seed':20260914,'results':results,
 'status':'INPUT_GRAPH_AND_BOUNDS_PASSED; prediction geometry and control separation not tested'},indent=2)+'\n')
