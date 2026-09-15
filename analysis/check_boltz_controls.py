"""Validate exact peptide chemistry against the pinned official Boltz2 parser."""
from pathlib import Path
import hashlib,json,yaml
from boltz.data.mol import load_canonicals
from boltz.data.parse.schema import parse_boltz_schema

root=Path(__file__).resolve().parents[1]
out=root/'results/controls/parsed';out.mkdir(exist_ok=True)
moldir=root/'.tools/boltz-assets/mols'
ccd=load_canonicals(moldir)
controls=json.loads((root/'results/controls/controls.json').read_text())['controls']
seq=''.join((root/'target.fasta').read_text().splitlines()[1:])
def schema(peptide,cyclic=False):
    entities=[{'protein':{'id':'A','sequence':seq,'msa':'empty'}},
              {'protein':{'id':'B','sequence':peptide,'msa':'empty','cyclic':cyclic}},
              {'ligand':{'id':'C','ccd':'GDP'}}]
    bonds=[]
    if not cyclic:
        entities += [{'ligand':{'id':'D','ccd':'ACE'}},{'ligand':{'id':'E','ccd':'NH2'}}]
        bonds=[{'bond':{'atom1':a,'atom2':b}} for a,b in [(['D',1,'C'],['B',1,'N']),(['B',5,'SG'],['B',15,'SG']),(['B',19,'C'],['E',1,'N'])]]
    return {'version':1,'sequences':entities,'constraints':bonds}

results=[];inference_inputs={}
for control in controls+[{'id':'CYCLIC_FORMAT_FIXTURE_ONLY','sequence':'GSGSGSGSGSGS'}]:
    fixture=control['id']=='CYCLIC_FORMAT_FIXTURE_ONLY'
    data=schema(control['sequence'],cyclic=fixture)
    if not fixture: inference_inputs[control['id']]=data
    target=parse_boltz_schema(control['id'],data,ccd,mol_dir=moldir,boltz_2=True)
    st=target.structure
    chains={str(c['name']):c for c in st.chains}
    assert chains['A']['res_num']==169
    assert chains['B']['res_num']==len(control['sequence'])
    assert chains['B']['cyclic_period']==(12 if fixture else 0)
    assert st.residues[chains['C']['res_idx']]['name']=='GDP'
    def atom(endpoint):
        chain,num,name=endpoint
        res=st.residues[chains[chain]['res_idx']+num-1]
        indexes=[i for i in range(res['atom_idx'],res['atom_idx']+res['atom_num']) if st.atoms[i]['name']==name]
        assert len(indexes)==1,endpoint
        return indexes[0]
    actual={frozenset([int(b['atom_1']),int(b['atom_2'])]) for b in st.bonds}
    for constraint in data['constraints']:
        b=constraint['bond'];assert frozenset([atom(b['atom1']),atom(b['atom2'])]) in actual,b
    if not fixture:
        assert chains['D']['atom_num']==3,chains['D']
        assert chains['E']['atom_num']==1,chains['E']
    yaml_text=yaml.safe_dump(data,sort_keys=False)
    (out/(control['id']+'.yaml')).write_text(yaml_text)
    st.dump(out/(control['id']+'.npz'))
    results.append({'id':control['id'],'fixture_only':fixture,'chains':[{k:c[k].item() for k in c.dtype.names} for c in st.chains],
                    'explicit_chemical_bonds_checked':len(data['constraints']), 'schema_sha256':hashlib.sha256(yaml_text.encode()).hexdigest(),
                    'affinity_requested':False,'qc_passed':True})
(out/'qc.json').write_text(json.dumps({'boltz_git_revision':'b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc','model_inference_performed':False,
 'scope':'exact component and connectivity input validation; coordinates and confidence not predicted; MSA empty in these representation-only fixtures', 'results':results},indent=2)+'\n')
(root/'results/controls/validation-inputs.json').write_text(json.dumps(inference_inputs,indent=2)+'\n')
print(json.dumps(results,indent=2))
