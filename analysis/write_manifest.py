"""Hash scientific artifacts while excluding credentials, environments and caches."""
from pathlib import Path
import datetime,hashlib,json
root=Path(__file__).resolve().parents[1]
files=[]
paths=[root/name for name in ['README.md','LICENSE','PROTOCOL.md','PROTOCOL_REMEDIATION_V2.md','PROVENANCE.md','BRIEF.md','POCKET.md','CAMPAIGN_STATE.json','target.fasta','target_wt.fasta','requirements-analysis.txt']]
for folder in ['results','analysis','dashboard','prompts']:
    paths.extend((root/folder).rglob('*'))
for p in sorted(paths):
    if not p.is_file() or p==root/'results/manifest.json' or '__pycache__' in p.parts:continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    files.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(root/'results/manifest.json').write_text(json.dumps({'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files},indent=2)+'\n')
print('Manifest contains',len(files),'files')
