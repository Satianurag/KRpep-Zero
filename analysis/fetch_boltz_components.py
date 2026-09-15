"""Acquire the exact official CCD bundle, extracting only required components."""
from pathlib import Path
import datetime, hashlib, json, tarfile
import requests

root=Path(__file__).resolve().parents[1]
revision='6fdef46d763fee7fbb83ca5501ccceff43b85607'
url=f'https://huggingface.co/boltz-community/boltz-2/resolve/{revision}/mols.tar'
cache=root/'.tools/boltz-assets';cache.mkdir(exist_ok=True)
archive=cache/'mols.tar'
if not archive.exists():
    temporary=cache/'mols.tar.partial'
    with requests.get(url,stream=True,timeout=(30,90)) as response:
        response.raise_for_status()
        with temporary.open('wb') as handle:
            for chunk in response.iter_content(1024*1024):handle.write(chunk)
    temporary.rename(archive)
sha=hashlib.sha256()
with archive.open('rb') as handle:
    for chunk in iter(lambda:handle.read(1024*1024),b''):sha.update(chunk)
names=set('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL UNK ACE NH2 GDP'.split())
out=cache/'mols';out.mkdir(exist_ok=True);components={}
with tarfile.open(archive) as tar:
    for member in tar:
        name=Path(member.name)
        if member.isfile() and name.suffix=='.pkl' and name.stem in names:
            content=tar.extractfile(member).read();(out/name.name).write_bytes(content)
            components[name.stem]={'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
receipt={'url':url,'repo_revision':revision,'bundle_sha256':sha.hexdigest(),'bundle_bytes':archive.stat().st_size,
         'components':components,'missing':sorted(names-set(components)),
         'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(root/'results/sources/boltz2-components-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
assert not receipt['missing'],receipt['missing']
