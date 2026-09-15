"""Assemble exact capped/disulfide control graphs using RDKit and pinned CCD chemistry.

These are input-representation candidates, not new designed peptides or predictions.
No experimental coordinates are supplied as conformers to the inference parser.
"""
from pathlib import Path
import hashlib,json,pickle
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,rdMolDescriptors

R=Path(__file__).resolve().parents[1]
OUT=R/'results/remediation/full-molecule';OUT.mkdir(parents=True,exist_ok=True)
controls=json.loads((R/'results/controls/controls.json').read_text())['controls']
target=''.join((R/'target.fasta').read_text().splitlines()[1:])
ccd={}
for code in set('ARG CYS PRO LEU TYR ILE SER ASP VAL'.split()):
    # Exact trusted official component bundle already pinned in acquisition receipt.
    with (R/'.tools/boltz-assets/mols'/f'{code}.pkl').open('rb') as f:ccd[code]=pickle.load(f)
outputs=[]
for control in controls:
    m=Chem.RWMol(Chem.MolFromSequence(control['sequence'],flavor=0))
    index={}
    for atom in m.GetAtoms():
        info=atom.GetPDBResidueInfo();number=info.GetResidueNumber();name=info.GetName().strip()
        index[(number,name)]=atom.GetIdx()
        atom.SetProp('residue_number',str(number));atom.SetProp('atom_name',name)
        # Match the pinned model's CCD reference formal-charge representation.
        lookup={a.GetProp('name'):a for a in ccd[info.GetResidueName()].GetAtoms()}
        if name in lookup:atom.SetFormalCharge(lookup[name].GetFormalCharge())
    # Resolve equivalent arginine nitrogen naming/bond orders to the same CCD.
    for num,aa in enumerate(control['sequence'],1):
        if aa!='R':continue
        ref={a.GetProp('name'):a.GetIdx() for a in ccd['ARG'].GetAtoms()}
        for name in ('NH1','NH2','NE'):
            bond=ccd['ARG'].GetBondBetweenAtoms(ref['CZ'],ref[name])
            m.GetBondBetweenAtoms(index[(num,'CZ')],index[(num,name)]).SetBondType(bond.GetBondType())
    # Terminal carboxyl leaving O becomes the amidating nitrogen.
    amide=m.GetAtomWithIdx(index[(19,'OXT')]);amide.SetAtomicNum(7);amide.SetFormalCharge(0)
    amide.SetProp('residue_number','20');amide.SetProp('atom_name','N')
    del index[(19,'OXT')];index[(20,'N')]=amide.GetIdx()
    for name,element in [('CH3',6),('C',6),('O',8)]:
        a=Chem.Atom(element);a.SetProp('residue_number','0');a.SetProp('atom_name',name)
        index[(0,name)]=m.AddAtom(a)
    m.AddBond(index[(0,'CH3')],index[(0,'C')],Chem.BondType.SINGLE)
    m.AddBond(index[(0,'C')],index[(0,'O')],Chem.BondType.DOUBLE)
    m.AddBond(index[(0,'C')],index[(1,'N')],Chem.BondType.SINGLE)
    m.AddBond(index[(5,'SG')],index[(15,'SG')],Chem.BondType.SINGLE)
    mol=m.GetMol();Chem.SanitizeMol(mol);Chem.AssignStereochemistry(mol,cleanIt=True,force=True)
    assert len(Chem.GetMolFrags(mol))==1
    assert mol.GetNumHeavyAtoms()==179
    assert Chem.GetFormalCharge(mol)==8
    centers=Chem.FindMolChiralCenters(mol,includeUnassigned=True)
    assert len(centers)==20 and all(label!='?' for _,label in centers),centers
    # All-L alpha centres; cysteine has the conventional R CIP assignment.
    for num,aa in enumerate(control['sequence'],1):
        expected='R' if aa=='C' else 'S'
        assert mol.GetAtomWithIdx(index[(num,'CA')]).GetProp('_CIPCode')==expected,(num,aa)
    smiles=Chem.MolToSmiles(mol,isomericSmiles=True,canonical=True)
    roundtrip=Chem.MolFromSmiles(smiles)
    assert Chem.MolToSmiles(roundtrip,isomericSmiles=True)==smiles
    assert roundtrip.GetNumHeavyAtoms()==179 and Chem.GetFormalCharge(roundtrip)==8
    assert mol.GetAtomWithIdx(index[(20,'N')]).GetTotalNumHs()==2
    assert mol.GetAtomWithIdx(index[(1,'N')]).GetTotalNumHs()==1
    assert mol.GetAtomWithIdx(index[(0,'CH3')]).GetTotalNumHs()==3
    assert mol.GetBondBetweenAtoms(index[(0,'C')],index[(0,'O')]).GetBondType()==Chem.BondType.DOUBLE
    assert mol.GetBondBetweenAtoms(index[(19,'C')],index[(19,'O')]).GetBondType()==Chem.BondType.DOUBLE
    assert all(mol.GetAtomWithIdx(index[(p,'SG')]).GetTotalNumHs()==0 for p in (5,15))
    # Preserve a map through the canonical SMILES atom order for output analysis.
    order=list(map(int,mol.GetProp('_smilesAtomOutputOrder').strip('[],').split(',')))
    inverse={old:new for new,old in enumerate(order)}
    atom_map=[{'smiles_atom_index':inverse[a.GetIdx()], 'peptide_author_residue':int(a.GetProp('residue_number')),
               'atom_name':a.GetProp('atom_name'),'element':a.GetSymbol(),'formal_charge':a.GetFormalCharge(),
               'CIP':a.GetProp('_CIPCode') if a.HasProp('_CIPCode') else None} for a in mol.GetAtoms()]
    for entry in atom_map:
        check=roundtrip.GetAtomWithIdx(entry['smiles_atom_index'])
        assert check.GetSymbol()==entry['element'] and check.GetFormalCharge()==entry['formal_charge']
        assert (check.GetProp('_CIPCode') if check.HasProp('_CIPCode') else None)==entry['CIP']
    expected_edges={tuple(sorted((inverse[b.GetBeginAtomIdx()],inverse[b.GetEndAtomIdx()]))):str(b.GetBondType()) for b in mol.GetBonds()}
    actual_edges={tuple(sorted((b.GetBeginAtomIdx(),b.GetEndAtomIdx()))):str(b.GetBondType()) for b in roundtrip.GetBonds()}
    assert expected_edges==actual_edges
    links=[((0,'C'),(1,'N')),((5,'SG'),(15,'SG')),((19,'C'),(20,'N'))]
    mapped_links=[{'endpoints':[list(a),list(b)],'smiles_indices':[inverse[index[a]],inverse[index[b]]]} for a,b in links]
    for link in mapped_links:assert roundtrip.GetBondBetweenAtoms(*link['smiles_indices']) is not None
    schema={'version':1,'sequences':[{'protein':{'id':'A','sequence':target,'msa':'empty'}},
                                  {'ligand':{'id':'B','smiles':smiles}}, {'ligand':{'id':'C','ccd':'GDP'}}]}
    item={'id':control['id'],'sequence':control['sequence'],'smiles':smiles,'atom_map':atom_map,'links':mapped_links,
          'heavy_atoms':179,'stereocenters':len(centers),'formal_charge':8,
          'formula':rdMolDescriptors.CalcMolFormula(roundtrip),'molecular_weight_Da':Descriptors.MolWt(roundtrip),
          'charge_policy':'Pinned Boltz CCD reference: Arg guanidinium +1 each; Asp neutral COOH. This is not a pH/pKa prediction.',
          'affinity_requested':False,'source_coordinates_used':False,'schema':schema}
    (OUT/f'{control["id"]}.smiles').write_text(smiles+'\n')
    outputs.append(item)
assert outputs[0]['formula']==outputs[1]['formula']
(OUT/'graphs.json').write_text(json.dumps({'rdkit_version':rdBase.rdkitVersion,'scope':'representation preparation only; not a conformational prediction',
    'controls':outputs},indent=2)+'\n')
print(json.dumps([{k:v for k,v in x.items() if k not in ('schema','atom_map','smiles','links')} for x in outputs],indent=2))
