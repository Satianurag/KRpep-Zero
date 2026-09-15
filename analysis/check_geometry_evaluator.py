"""Meaningful positive/mirror/compressed-bond checks of the v2 geometry evaluator."""
from pathlib import Path
import json,pickle
import numpy as np
from molecular_geometry import check_geometry

R=Path(__file__).resolve().parents[1];base=R/'results/remediation/full-molecule'
graphs=json.loads((base/'graphs.json').read_text());results=[]
for item in graphs['controls']:
    name=item['id']
    with (base/f'{name}.mols.pkl').open('rb') as f:mol=next(m for m in pickle.load(f).values() if m.GetNumHeavyAtoms()==179)
    # Early local prototype pickles did not retain atom name properties; the
    # upstream inference writer does. Restore labels from the verified sidecar.
    for entry in json.loads((base/f'{name}.atom-map.json').read_text()):
        atom=mol.GetAtomWithIdx(entry['smiles_atom_index'])
        assert atom.GetSymbol()==entry['element']
        atom.SetProp('name',entry['boltz_atom_name'])
    with np.load(base/f'{name}.parsed.npz') as data:offset=int(next(c['atom_idx'] for c in data['chains'] if c['name']=='B'))
    with np.load(base/f'{name}.constraints.npz') as data:bounds=data['rdkit_bounds_constraints']
    coords=mol.GetConformer().GetPositions()
    original=check_geometry(mol,coords,bounds,offset,item['links'])
    assert len(original['stereocenters'])==20 and original['stereochemistry_passed']
    mirrored=coords.copy();mirrored[:,0]*=-1
    mirror=check_geometry(mol,mirrored,bounds,offset,item['links'])
    assert not mirror['stereochemistry_passed'] and not any(x['passed'] for x in mirror['stereocenters'])
    compressed=coords.copy();i,j=item['links'][2]['smiles_indices']
    compressed[j]=compressed[i]+.7*(compressed[j]-compressed[i])/np.linalg.norm(compressed[j]-compressed[i])
    bad=check_geometry(mol,compressed,bounds,offset,item['links'])
    assert not bad['critical_links'][2]['passed']
    results.append({'id':name,'unmodified_ETKDG_centers_correct':20,'mirror_centers_inverted':20,
                    'artificial_0_7_A_cap_bond_rejected':True,
                    'scope':'evaluator self-check on input conformers, not neural predictions'})
(R/'results/remediation/geometry-evaluator-qc.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
