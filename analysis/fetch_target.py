"""Download exact public structural/sequence inputs with SHA-256 receipts."""
from pathlib import Path
import datetime, hashlib, json
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'target'
OUT.mkdir(parents=True, exist_ok=True)
sources = {'5xco.cif': 'https://files.rcsb.org/download/5XCO.cif',
           '5xco-entry.json': 'https://data.rcsb.org/rest/v1/core/entry/5XCO'}
for accession in ('P01116', 'P01111', 'P01112'):
    sources[f'{accession}.json'] = f'https://rest.uniprot.org/uniprotkb/{accession}.json'
receipts = []
for name, url in sources.items():
    path = OUT / name
    if path.exists():
        raise SystemExit(f'Refusing to overwrite {path}')
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    path.write_bytes(r.content)
    receipts.append({'file': name, 'url': url, 'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'sha256': hashlib.sha256(r.content).hexdigest(), 'bytes': len(r.content)})
    print(name, len(r.content), flush=True)
(OUT / 'source-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
