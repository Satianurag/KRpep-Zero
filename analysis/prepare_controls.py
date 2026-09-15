"""Prepare declared controls; this does not establish negative-control nonbinding."""
from pathlib import Path
from collections import Counter
import json, random

ROOT=Path(__file__).resolve().parents[1]
positive='RRRRCPLYISYDPVCRRRR'
core=list(positive[5:14])
seed=20260914
random.Random(seed).shuffle(core)
negative=positive[:5]+''.join(core)+positive[14:]
assert Counter(positive)==Counter(negative) and positive!=negative
assert len(positive)==len(negative)==19 and negative[4]==negative[14]=='C'
out=ROOT/'results'/'controls';out.mkdir(exist_ok=True)
manifest={'seed':seed,'scramble_algorithm':'Python random.Random(seed).shuffle once on positions6-14; retain Arg tails and Cys5/Cys15',
 'chemistry':{'N_terminus':'acetylated','C_terminus':'amidated','disulfide':[5,15],'backbone_cyclic':False},
 'controls':[{'id':'KRpep-2d','sequence':positive,'role':'published positive control'},
             {'id':'SCRAMBLE-20260914','sequence':negative,'role':'proposed negative control; not an experimentally established nonbinder'}],
 'model_input_status':'NOT_YET_VALIDATED; FASTA is sequence only and must not be submitted without the chemistry manifest'}
(out/'controls.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'controls.fasta').write_text(f'>KRpep-2d|chemistry_in_controls.json\n{positive}\n>SCRAMBLE-20260914|chemistry_in_controls.json\n{negative}\n')
print(json.dumps(manifest,indent=2))
