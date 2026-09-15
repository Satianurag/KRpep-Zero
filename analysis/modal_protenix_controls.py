"""Bounded independent-model diagnostic; never advances the candidate gate."""
from pathlib import Path
import hashlib, io, json, subprocess, tarfile, time
import modal
R=Path(__file__).resolve().parents[1]
SOURCE='4c355be4553512f72453ecbfb65e69f4c35d1413'
MODEL_NAME='protenix_base_default_v1.0.0'
RUN_ID='protenix-base-default-diagnostic-001'
image=(modal.Image.from_registry('nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04',add_python='3.11')
 .apt_install('git','build-essential','libgl1','libglib2.0-0')
 .env({'DS_BUILD_OPS':'0','PROTENIX_ROOT_DIR':'/tmp/protenix-cache'})
 .pip_install('torch==2.7.1','setuptools','wheel',extra_options='--index-url https://pypi.org/simple')
 .add_local_dir(str(R/'.tools/protenix'),remote_path='/app/protenix',copy=True)
 .pip_install('/app/protenix'))
app=modal.App('krpep-zero-protenix-base-default-controls')
@app.function(image=image,gpu='L4',cpu=4,memory=32768,timeout=2700,startup_timeout=300,
 max_containers=1,min_containers=0,retries=0,scaledown_window=2)
def run(inputs,msa,protocol):
    import os
    root=Path('/tmp/krpep-protenix');root.mkdir()
    (root/'target.a3m').write_text(msa)
    for x in inputs:x['sequences'][0]['proteinChain']['unpairedMsaPath']=str(root/'target.a3m')
    (root/'input.json').write_text(json.dumps(inputs,indent=2))
    (root/'PROTOCOL_PROTENIX_DIAGNOSTIC.md').write_text(protocol)
    def sha(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        return h.hexdigest()
    assert subprocess.check_output(['git','-C','/app/protenix','rev-parse','HEAD'],text=True).strip()==SOURCE
    command=['protenix','pred','-i',str(root/'input.json'),'-o',str(root/'predictions'),'-s','17,42,101',
      '-n',MODEL_NAME,'-c','10','-p','200','-e','1','--use_default_params','false',
      '--use_msa','true','--use_template','false','--use_rna_msa','false',
      '--trimul_kernel','torch','--triatt_kernel','torch','--enable_fusion','false']
    started=time.time();error=None;code=None
    try:
        with (root/'inference.log').open('w') as log:
            cp=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=2400)
        code=cp.returncode
        if code:raise RuntimeError(f'Protenix exited {code}')
        if len(list((root/'predictions').rglob('*.cif')))!=6:raise RuntimeError('Expected exactly 6 predicted CIFs')
    except Exception as e:error=f'{type(e).__name__}: {e}'
    assets=[]
    for p in Path('/tmp/protenix-cache').rglob('*'):
        if p.is_file():assets.append({'name':str(p.relative_to('/tmp/protenix-cache')),'bytes':p.stat().st_size,'sha256':sha(p)})
    metadata={'source_commit':SOURCE,'model':MODEL_NAME,'run_id':RUN_ID,'gpu':'L4','command':command,
      'protocol_sha256':hashlib.sha256(protocol.encode()).hexdigest(),'input_sha256':sha(root/'input.json'),
      'msa_sha256':sha(root/'target.a3m'),'assets':assets,'elapsed_seconds':time.time()-started,'exit_code':code,'error':error,
      'scope':'exploratory cross-model control diagnostic; no binding classifier validation; old gates unchanged'}
    (root/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (root/'requirements.txt').write_text(subprocess.check_output(['python','-m','pip','freeze'],text=True))
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for p in root.rglob('*'):
            if p.is_file():tar.add(p,arcname=str(p.relative_to(root)))
    print(json.dumps(metadata),flush=True)
    if error:print((root/'inference.log').read_text()[-5000:],flush=True)
    return {'metadata':metadata,'archive':stream.getvalue()}
@app.local_entrypoint()
def main():
    dest=R/'results'/RUN_ID
    if dest.exists():raise RuntimeError('Refusing to overwrite existing diagnostic')
    protocol=(R/'PROTOCOL_PROTENIX_DIAGNOSTIC.md').read_text()
    inputs=json.loads((R/'results/protenix-inputs/inputs.json').read_text())
    result=run.remote(inputs,(R/'results/target/msa/kras-g12d.a3m').read_text(),protocol)
    dest.mkdir();(dest/'outputs.tar.gz').write_bytes(result['archive'])
    (dest/'receipt.json').write_text(json.dumps(result['metadata'],indent=2))
    with tarfile.open(fileobj=io.BytesIO(result['archive'])) as t:t.extractall(dest/'extracted',filter='data')
    if result['metadata']['error']:raise RuntimeError(result['metadata']['error'])
