"""Coordinate checks against an explicit RDKit graph and precomputed bond bounds."""
import numpy as np
from rdkit import Chem

def check_geometry(reference,coords,bounds,atom_offset,critical_links):
    coords=np.asarray(coords,dtype=float)
    assert coords.shape==(reference.GetNumAtoms(),3) and np.isfinite(coords).all()
    expected={i:code for i,code in Chem.FindMolChiralCenters(reference,includeUnassigned=False)}
    molecule=Chem.Mol(reference);molecule.RemoveAllConformers()
    conf=Chem.Conformer(reference.GetNumAtoms());conf.Set3D(True)
    for i,xyz in enumerate(coords):conf.SetAtomPosition(i,xyz.tolist())
    molecule.AddConformer(conf)
    Chem.RemoveStereochemistry(molecule)
    Chem.AssignStereochemistryFrom3D(molecule,confId=0,replaceExistingTags=True)
    observed=dict(Chem.FindMolChiralCenters(molecule,includeUnassigned=True))
    chiral=[{'atom_index':int(i),'expected':code,'observed':observed.get(i,'unassigned'),'passed':observed.get(i)==code} for i,code in expected.items()]
    lookup={tuple(sorted(map(int,b['atom_idxs']))):b for b in bounds}
    distances=[]
    for bond in reference.GetBonds():
        i,j=bond.GetBeginAtomIdx(),bond.GetEndAtomIdx()
        key=tuple(sorted([atom_offset+i,atom_offset+j]));bound=lookup[key]
        assert bound['is_bond']
        distance=float(np.linalg.norm(coords[i]-coords[j]))
        lower=float(bound['lower_bound'])*.875;upper=float(bound['upper_bound'])*1.125
        distances.append({'atom_indices':[i,j],'atom_names':[reference.GetAtomWithIdx(k).GetProp('name') for k in (i,j)],
                          'distance_A':distance,'lower_A':lower,'upper_A':upper,'passed':lower<=distance<=upper})
    bypair={tuple(sorted(d['atom_indices'])):d for d in distances}
    critical=[{**link,**bypair[tuple(sorted(link['smiles_indices']))]} for link in critical_links]
    return {'stereocenters':chiral,'stereochemistry_passed':all(x['passed'] for x in chiral),
            'bonds':distances,'bond_count':len(distances),'bonds_within_expanded_bounds':sum(x['passed'] for x in distances),
            'fraction_bonds_within_expanded_bounds':sum(x['passed'] for x in distances)/len(distances),
            'critical_links':critical,'critical_links_passed':all(x['passed'] for x in critical)}
