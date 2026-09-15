"""Reproduce guidance coverage gaps with saved inputs and official CPU code."""
from pathlib import Path
import hashlib,json
import numpy as np
import torch
from boltz.data.types import Input,StructureV2,ResidueConstraints,Record
from boltz.data.tokenize.boltz2 import Boltz2Tokenizer
from boltz.data.feature.featurizerv2 import process_chain_feature_constraints
from boltz.model.potentials.potentials import ConnectionsPotential

R=Path(__file__).resolve().parents[1]
OUT=R/'results/remediation';OUT.mkdir(exist_ok=True)
BASE=R/'results/boltz-control-calibration-002/extracted'
inputs=json.loads((R/'results/controls/validation-inputs.json').read_text())
audits=[]
for name,data in inputs.items():
    base=BASE/f'{name}-seed-17'/f'boltz_results_{name}'/'processed'
    st=StructureV2.load(base/'structures'/f'{name}.npz')
    constraints=ResidueConstraints.load(base/'constraints'/f'{name}.npz')
    record=Record.load(base/'records'/f'{name}.json')
    tokenized=Boltz2Tokenizer().tokenize(Input(structure=st,msa={},record=record,residue_constraints=constraints))
    features=process_chain_feature_constraints(tokenized)
    connected={tuple(sorted(map(int,p))) for p in features['connected_atom_index'].T}
    rdkit_pairs={tuple(sorted(map(int,p['atom_idxs']))):p for p in constraints.rdkit_bounds_constraints}
    chains={str(c['name']):c for c in st.chains}
    def resolve(endpoint):
        chain,residue,atom=endpoint;c=chains[chain]
        r=st.residues[int(c['res_idx'])+residue-1]
        atoms=range(int(r['atom_idx']),int(r['atom_idx']+r['atom_num']))
        found=[i for i in atoms if st.atoms[i]['name']==atom]
        assert len(found)==1
        return found[0]
    result=[]
    for c in data['constraints']:
        a,b=c['bond']['atom1'],c['bond']['atom2'];key=tuple(sorted([resolve(a),resolve(b)]))
        bound=rdkit_pairs.get(key)
        result.append({'endpoints':[a,b],'global_atom_indices':key,
                       'in_structure_bonds':any(tuple(sorted([int(x['atom_1']),int(x['atom_2'])]))==key for x in st.bonds),
                       'in_connections_potential':key in connected,
                       'has_rdkit_distance_bounds':bound is not None,
                       'rdkit_lower_bound_A':float(bound['lower_bound']) if bound is not None else None})
    feats={k:v.unsqueeze(0) for k,v in features.items()}
    potential=ConnectionsPotential()
    _,args,_,_,_=potential.compute_args(feats,{'buffer':2.0})
    assert args[1] is None
    # One distance at a time, run the actual official flat-bottom function.
    penalty={}
    for distance in (.7,1.32,2.0,2.5):
        value=torch.full_like(args[2],distance)
        penalty[str(distance)]=potential.compute_function(value,*args,compute_derivative=False).tolist()
    audits.append({'control':name,'connections':result,'guidance_upper_bound_A':args[2].tolist(),
                   'guidance_lower_bound':None,'official_penalty_by_probe_distance_A':penalty})
sources=['src/boltz/model/potentials/potentials.py','src/boltz/data/feature/featurizerv2.py','src/boltz/data/parse/schema.py']
out={'scope':'CPU-only diagnostic; no prediction or model changes',
     'code_revision':'b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc',
     'source_sha256':{p:hashlib.sha256((R/'.tools/boltz'/p).read_bytes()).hexdigest() for p in sources},
     'controls':audits,
     'interpretation':'External cap links have an upper-only connection potential, no RDKit cross-residue lower bounds, and connected-chain VDW exclusion. The intrachain disulfide is represented in model bond features but omitted by this connections-potential builder. These coverage gaps permit distorted geometry; this does not establish the cause of confidence overlap or prove a remedy will pass the gate.'}
(OUT/'bond-guidance-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
