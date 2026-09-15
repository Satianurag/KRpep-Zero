"""Run an exact nonsecret tool command and retain inputs, timing and raw outputs."""
import argparse, datetime, hashlib, json, pathlib, subprocess, sys

p = argparse.ArgumentParser()
p.add_argument('name')
p.add_argument('--stdin-file')
p.add_argument('--timeout', type=int, default=120)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ['--'] else a.command
root = pathlib.Path(__file__).resolve().parents[1]
out = root/'results/logs'/a.name
out.mkdir(parents=True, exist_ok=False)
payload = pathlib.Path(a.stdin_file).read_bytes() if a.stdin_file else None
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
record = {'name':a.name, 'started_at':started, 'argv':command,
          'stdin_file':a.stdin_file, 'stdin_sha256':hashlib.sha256(payload).hexdigest() if payload else None}
(out/'request.json').write_text(json.dumps(record,indent=2)+'\n')
try:
    run = subprocess.run(command,input=payload,capture_output=True,cwd=root,timeout=a.timeout)
    stdout, stderr, code = run.stdout,run.stderr,run.returncode
except subprocess.TimeoutExpired as error:
    stdout,stderr,code=error.stdout or b'',error.stderr or b'',124
(out/'stdout.txt').write_bytes(stdout)
(out/'stderr.txt').write_bytes(stderr)
record.update(ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=code,
              stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest())
(out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'operation':a.name,'exit_code':code,'receipt':str(out/'receipt.json')}))
raise SystemExit(code)
