"""Control-first, six-run Boltz2 validation on bounded Modal L4 compute."""
from pathlib import Path
import hashlib,io,json,subprocess,tarfile,time
import modal

ROOT=Path(__file__).resolve().parents[1]
CODE_SHA='b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc'
WEIGHTS_SHA='6fdef46d763fee7fbb83ca5501ccceff43b85607'
image=(modal.Image.from_registry('nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04',add_python='3.11')
 .apt_install('build-essential','cmake','git','libboost-all-dev','libffi-dev','libgl1','libhdf5-dev','libssl-dev','libxml2-dev','libxslt1-dev','pkg-config')
 .pip_install('torch==2.8.0',extra_options='--index-url https://download.pytorch.org/whl/cu126')
 .add_local_dir(str(ROOT/'.tools/boltz'),remote_path='/app/boltz',copy=True)
 .pip_install('/app/boltz','torch==2.8.0','huggingface_hub==0.36.2','cuequivariance_ops_cu12==0.5.1','cuequivariance_ops_torch_cu12==0.5.1','cuequivariance_torch==0.5.1'))
app=modal.App('krpep-zero-boltz-controls')

@app.function(image=image,gpu='L4',cpu=4,memory=16384,timeout=3600,startup_timeout=300,
              max_containers=1,min_containers=0,retries=0,scaledown_window=2)
def controls(inputs:dict,msa_text:str):
    from huggingface_hub import hf_hub_download
    import yaml
    root=Path('/tmp/krpep-control-run');root.mkdir(exist_ok=True)
    cache=Path('/tmp/boltz-pinned-cache');cache.mkdir(exist_ok=True)
    (root/'inputs').mkdir(exist_ok=True);(root/'logs').mkdir(exist_ok=True)
    (root/'target.a3m').write_text(msa_text)
    sha=subprocess.check_output(['git','-C','/app/boltz','rev-parse','HEAD'],text=True).strip()
    assert sha==CODE_SHA
    commands=[];error=None;started=time.time();artifacts=[]
    try:
        for filename in ('mols.tar','boltz2_conf.ckpt','boltz2_aff.ckpt'):
            print('Acquiring pinned artifact:',filename,flush=True)
            path=Path(hf_hub_download('boltz-community/boltz-2',filename,revision=WEIGHTS_SHA,local_dir=cache,token=False))
            digest=hashlib.sha256()
            with path.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''):digest.update(b)
            artifacts.append({'file':filename,'sha256':digest.hexdigest(),'bytes':path.stat().st_size})
        # Official CLI eagerly requires the affinity checkpoint to exist. It is
        # downloaded unchanged, but never requested or executed by these inputs.
        for name,data in inputs.items():
            assert 'properties' not in data
            data['sequences'][0]['protein']['msa']=str(root/'target.a3m')
            (root/'inputs'/f'{name}.yaml').write_text(yaml.safe_dump(data,sort_keys=False))
        for seed in (17,42,101):
            for name in sorted(inputs):
                run_id=f'{name}-seed-{seed}'
                argv=['boltz','predict',str(root/'inputs'/f'{name}.yaml'),'--out_dir',str(root/run_id),
                      '--cache',str(cache),'--model','boltz2','--devices','1','--accelerator','gpu',
                      '--recycling_steps','3','--sampling_steps','200','--diffusion_samples','1',
                      '--max_parallel_samples','1','--num_workers','1','--preprocessing-threads','1',
                      '--seed',str(seed),'--subsample_msa','--num_subsampled_msa','1024','--max_msa_seqs','8192',
                      '--use_potentials','--write_full_pae','--output_format','mmcif']
                print('Starting',run_id,flush=True);t=time.time()
                with (root/'logs'/f'{run_id}.stdout.txt').open('w') as stdout, (root/'logs'/f'{run_id}.stderr.txt').open('w') as stderr:
                    r=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=450)
                commands.append({'id':run_id,'seed':seed,'argv':argv,'exit_code':r.returncode,'elapsed_seconds':time.time()-t})
                print('Finished',run_id,'exit',r.returncode,flush=True)
                if r.returncode:raise RuntimeError(f'{run_id} failed')
                if len(list((root/run_id).glob('**/confidence_*_model_0.json')))!=1:
                    raise RuntimeError(f'{run_id} did not emit exactly one prediction')
    except Exception as e:
        error=f'{type(e).__name__}: {e}'
    metadata={'code_revision':sha,'weights_revision':WEIGHTS_SHA,'artifacts':artifacts,'commands':commands,
              'error':error,'elapsed_seconds':time.time()-started,'affinity_inference_requested':False,
              'gpu':'L4','seeds':[17,42,101],'samples_per_seed':1,'msa_sha256':hashlib.sha256(msa_text.encode()).hexdigest()}
    (root/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (root/'requirements.txt').write_text(subprocess.check_output(['python','-m','pip','freeze'],text=True))
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as t:
        for path in root.rglob('*'):
            if path.is_file():t.add(path,arcname=str(path.relative_to(root)))
    return {'metadata':metadata,'archive':stream.getvalue()}

@app.local_entrypoint()
def main(out_dir:str='results/boltz-control-calibration-001'):
    dest=ROOT/out_dir
    if dest.exists():raise ValueError('Output directory already exists')
    inputs=json.loads((ROOT/'results/controls/validation-inputs.json').read_text())
    assert len(inputs)==2
    msa=(ROOT/'results/target/msa/kras-g12d.a3m').read_text()
    result=controls.remote(inputs,msa)
    dest.mkdir(parents=True);archive=result['archive']
    (dest/'outputs.tar.gz').write_bytes(archive)
    (dest/'receipt.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive).hexdigest(),'metadata':result['metadata']},indent=2)+'\n')
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(dest/'extracted',filter='data')
    if result['metadata']['error']:raise RuntimeError(result['metadata']['error'])
