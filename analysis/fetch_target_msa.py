"""Use the official Boltz MMseqs2 client for one public WT target query."""
from pathlib import Path
import datetime, hashlib, json
from boltz.data.msa.mmseqs2 import run_mmseqs2

root=Path(__file__).resolve().parents[1]
out=root/'results/target/msa';out.mkdir(exist_ok=True)
wt=''.join((root/'target_wt.fasta').read_text().splitlines()[1:])
mut=''.join((root/'target.fasta').read_text().splitlines()[1:])
assert len(wt)==len(mut)==169 and [i for i,(a,b) in enumerate(zip(wt,mut),1) if a!=b]==[12]
result=run_mmseqs2([wt],prefix=str(out/'mmseqs2'),host_url='https://api.colabfold.com',use_env=True,use_pairing=False)
assert len(result)==1
text=result[0];lines=text.splitlines();assert lines[0].startswith('>') and lines[1]==wt
(out/'kras-wt.a3m').write_text(text)
lines[0]='>KRAS4B_G12D_query';lines[1]=mut
(out/'kras-g12d.a3m').write_text('\n'.join(lines)+'\n')
receipt={'provider':'ColabFold public MMseqs2 via official Boltz client','submitted_query':'KRAS4B WT1-169','host':'https://api.colabfold.com',
         'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':sum(x.startswith('>') for x in lines),
         'counter_screen_design':'Identical homolog rows. Only first query row changed G12D for mutant.',
         'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.a3m')}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
