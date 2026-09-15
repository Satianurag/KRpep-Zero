"""One preregistered full-graph remediation batch on the existing Modal image."""
from pathlib import Path
import hashlib,io,json,subprocess,tarfile,time
import modal
ROOT=Path(__file__).resolve().parents[1]
CODE_SHA='b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc'
WEIGHTS_SHA='6fdef46d763fee7fbb83ca5501ccceff43b85607'
# Standalone module: Modal's remote worker must not depend on an unmapped
# sibling Python module. This is the exact previously built image recipe.
image=(modal.Image.from_registry('nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04',add_python='3.11')
 .apt_install('build-essential','cmake','git','libboost-all-dev','libffi-dev','libgl1','libhdf5-dev','libssl-dev','libxml2-dev','libxslt1-dev','pkg-config')
 .pip_install('torch==2.8.0',extra_options='--index-url https://download.pytorch.org/whl/cu126')
 .add_local_dir(str(ROOT/'.tools/boltz'),remote_path='/app/boltz',copy=True)
 .pip_install('/app/boltz','torch==2.8.0','huggingface_hub==0.36.2','cuequivariance_ops_cu12==0.5.1','cuequivariance_ops_torch_cu12==0.5.1','cuequivariance_torch==0.5.1'))

app=modal.App('krpep-zero-control-remediation-v2')

@app.function(image=image,gpu='L4',cpu=4,memory=16384,timeout=6000,startup_timeout=300,
              max_containers=1,min_containers=0,retries=0,scaledown_window=2)
def run(inputs:dict,msa_text:str,protocol_text:str):
    from huggingface_hub import hf_hub_download
    import yaml,shutil
    root=Path('/tmp/krpep-controls-v2');root.mkdir()
    cache=Path('/tmp/boltz-pinned-cache');cache.mkdir(exist_ok=True)
    (root/'inputs').mkdir();(root/'logs').mkdir()
    (root/'target.a3m').write_text(msa_text)
    (root/'PROTOCOL_REMEDIATION_V2.md').write_text(protocol_text)
    assert subprocess.check_output(['git','-C','/app/boltz','rev-parse','HEAD'],text=True).strip()==CODE_SHA
    def digest(path):
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        return h.hexdigest()
    started=time.time();commands=[];assets=[];error=None;input_hashes={}
    try:
        for filename in ('mols.tar','boltz2_conf.ckpt','boltz2_aff.ckpt'):
            print('Acquiring pinned artifact:',filename,flush=True)
            p=Path(hf_hub_download('boltz-community/boltz-2',filename,revision=WEIGHTS_SHA,local_dir=cache,token=False))
            assets.append({'file':filename,'sha256':digest(p),'bytes':p.stat().st_size})
        for name,data in inputs.items():
            assert 'properties' not in data and len(data['sequences'])==3
            data['sequences'][0]['protein']['msa']=str(root/'target.a3m')
            (root/'inputs'/f'{name}.yaml').write_text(yaml.safe_dump(data,sort_keys=False))
        for seed in (17,42,101):
            for name in sorted(inputs):
                identifier=f'{name}-seed-{seed}';destination=root/identifier
                processed=destination/f'boltz_results_{name}'/'processed'
                if seed!=17:
                    original=root/f'{name}-seed-17'/f'boltz_results_{name}'/'processed'
                    shutil.copytree(original,processed)
                argv=['python','-c','from rdkit import rdBase; rdBase.SeedRandomNumberGenerator(20260914); from boltz.main import cli; cli()',
                      'predict',str(root/'inputs'/f'{name}.yaml'),'--out_dir',str(destination),
                      '--cache',str(cache),'--model','boltz2','--devices','1','--accelerator','gpu',
                      '--recycling_steps','3','--sampling_steps','200','--diffusion_samples','1',
                      '--max_parallel_samples','1','--num_workers','1','--preprocessing-threads','1',
                      '--seed',str(seed),'--subsample_msa','--num_subsampled_msa','1024','--max_msa_seqs','8192',
                      '--use_potentials','--write_full_pae','--output_format','mmcif']
                print('Starting',identifier,flush=True);t=time.time()
                with (root/'logs'/f'{identifier}.stdout.txt').open('w') as out,(root/'logs'/f'{identifier}.stderr.txt').open('w') as err:
                    result=subprocess.run(argv,stdout=out,stderr=err,timeout=750)
                commands.append({'id':identifier,'seed':seed,'argv':argv,'exit_code':result.returncode,'elapsed_seconds':time.time()-t})
                print('Finished',identifier,'exit',result.returncode,flush=True)
                if result.returncode:raise RuntimeError(f'{identifier} failed')
                if len(list(destination.glob('**/confidence_*_model_0.json')))!=1:raise RuntimeError('Missing or multiple predictions')
                hashes={str(p.relative_to(processed)):digest(p) for p in processed.rglob('*') if p.is_file()}
                if seed==17:input_hashes[name]=hashes
                elif hashes!=input_hashes[name]:raise RuntimeError(f'{identifier}: preprocessing changed across seeds')
    except Exception as e:error=f'{type(e).__name__}: {e}'
    metadata={'protocol':'PROTOCOL_REMEDIATION_V2.md','protocol_sha256':hashlib.sha256(protocol_text.encode()).hexdigest(),
              'code_revision':CODE_SHA,'weights_revision':WEIGHTS_SHA,'assets':assets,'commands':commands,
              'fixed_preprocessing_hashes':input_hashes,'affinity_inference_requested':False,'elapsed_seconds':time.time()-started,
              'error':error,'gpu':'L4','seeds':[17,42,101],'samples_per_seed':1}
    (root/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (root/'requirements.txt').write_text(subprocess.check_output(['python','-m','pip','freeze'],text=True))
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for p in root.rglob('*'):
            if p.is_file():tar.add(p,arcname=str(p.relative_to(root)))
    return {'metadata':metadata,'archive':stream.getvalue()}

@app.local_entrypoint()
def main(out_dir:str='results/control-remediation-v2-001'):
    dest=ROOT/out_dir
    if dest.exists():raise ValueError('Output directory already exists')
    graphs=json.loads((ROOT/'results/remediation/full-molecule/graphs.json').read_text())
    inputs={x['id']:x['schema'] for x in graphs['controls']}
    qc=json.loads((ROOT/'results/remediation/full-molecule/parser-qc.json').read_text())
    assert len(qc['results'])==2
    protocol=(ROOT/'PROTOCOL_REMEDIATION_V2.md').read_text()
    result=run.remote(inputs,(ROOT/'results/target/msa/kras-g12d.a3m').read_text(),protocol)
    dest.mkdir();archive=result['archive'];(dest/'outputs.tar.gz').write_bytes(archive)
    (dest/'receipt.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive).hexdigest(),'metadata':result['metadata']},indent=2)+'\n')
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(dest/'extracted',filter='data')
    if result['metadata']['error']:raise RuntimeError(result['metadata']['error'])
