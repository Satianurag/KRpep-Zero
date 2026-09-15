"""Modal wrapper for a bounded, reproducible BoltzGen calibration/design run.

Preparation only: this module is not imported or deployed during project setup.
The remote function runs the pinned local BoltzGen source, the built-in
peptide-anything pipeline, and returns a compressed copy of the output and
diagnostic logs even when the pipeline fails.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any

import modal


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "krpep-zero-boltzgen"
PINNED_COMMIT = "a3149cf18eeb58648d1abbb27539bd73f746cdda"
MAX_DESIGNS = 60
DEFAULT_BUDGET = 2
REMOTE_ROOT = Path("/app/work")
SPEC_PATH = REMOTE_ROOT / "analysis/boltzgen-pocket.yaml"
TARGET_PATH = REMOTE_ROOT / "results/target/kras-g12d-gdp.cif"


# BoltzGen's pinned Dockerfile uses CUDA 12.2 and cu12 equivariance packages.
# Torch 2.8.0 is installed from the CUDA 12.6 wheel index; no CUDA 13 index is
# used.  The exact wheel/platform compatibility is checked only at invocation.
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04", add_python="3.11"
    )
    .apt_install(
        "build-essential",
        "cmake",
        "git",
        "libboost-all-dev",
        "libffi-dev",
        "libgl1",
        "libhdf5-dev",
        "libssl-dev",
        "libxml2-dev",
        "libxslt1-dev",
        "pkg-config",
    )
    .pip_install(
        "torch==2.8.0",
        extra_options="--index-url https://download.pytorch.org/whl/cu126",
    )
    .add_local_dir(str(ROOT / ".tools/boltzgen"), remote_path="/app/boltzgen", copy=True)
    .pip_install("/app/boltzgen", "torch==2.8.0", "cuequivariance_ops_cu12==0.5.1", "cuequivariance_ops_torch_cu12==0.5.1", "cuequivariance_torch==0.5.1")
    .add_local_file(
        str(ROOT / "analysis/boltzgen-pocket.yaml"),
        remote_path=str(SPEC_PATH),
    )
    .add_local_file(
        str(ROOT / "results/target/kras-g12d-gdp.cif"),
        remote_path=str(TARGET_PATH),
    )
)

app = modal.App(APP_NAME)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_capture(args: list[str], cwd: Path, log_path: Path) -> dict[str, Any]:
    started = time.time()
    print('Starting:', ' '.join(args[:3]), flush=True)
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "HF_HOME": "/tmp/hf-cache", "HF_HUB_DISABLE_IMPLICIT_TOKEN":"1"},
        timeout=3000,
    )
    payload = (
        "$ "
        + " ".join(args)
        + "\n\n--- stdout ---\n"
        + completed.stdout
        + "\n--- stderr ---\n"
        + completed.stderr
    )
    log_path.write_text(payload)
    print('Finished:', log_path.name, 'exit', completed.returncode, 'seconds', round(time.time()-started,1), flush=True)
    return {
        "argv": args,
        "exit_code": completed.returncode,
        "elapsed_seconds": time.time() - started,
        "stdout_bytes": len(completed.stdout.encode()),
        "stderr_bytes": len(completed.stderr.encode()),
        "log": 'logs/' + log_path.name,
    }


def _tar_bytes(root: Path) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            archive.add(path, arcname=str(path.relative_to(root)))
    return stream.getvalue()


@app.function(
    image=image,
    gpu="L4",
    max_containers=1,
    min_containers=0,
    timeout=3600,
    startup_timeout=300,
    retries=0,
    cpu=4,
    memory=16384,
    scaledown_window=2,
)
def run_boltzgen(num_designs: int = 2, budget: int = DEFAULT_BUDGET) -> dict[str, Any]:
    """Run one bounded BoltzGen job and return output tar bytes plus metadata."""
    if not 1 <= num_designs <= MAX_DESIGNS:
        raise ValueError(f"num_designs must be between 1 and {MAX_DESIGNS}")
    if not 1 <= budget <= num_designs:
        raise ValueError("budget must be positive and no larger than num_designs")

    run_root = Path("/tmp/krpep-zero-boltzgen")
    output = run_root / "output"
    logs = run_root / "logs"
    output.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    started = time.time()
    commands: list[dict[str, Any]] = []
    error: str | None = None
    source_revision: str | None = None

    try:
        source_revision = subprocess.run(
            ["git", "-C", "/app/boltzgen", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if source_revision != PINNED_COMMIT:
            raise RuntimeError(
                f"pinned BoltzGen source mismatch: {source_revision} != {PINNED_COMMIT}"
            )
        (logs / "source-revision.txt").write_text(source_revision + "\n")
        commands.append(_run_capture(["python", "-m", "pip", "freeze"], REMOTE_ROOT, logs / "requirements.txt"))
        commands.append(_run_capture(["boltzgen", "--version"], REMOTE_ROOT, logs / "version.txt"))
        commands.append(
            _run_capture(
                ["boltzgen", "run", "--help"], REMOTE_ROOT, logs / "run-help.txt"
            )
        )
        commands.append(
            _run_capture(
                ["boltzgen", "check", "--help"], REMOTE_ROOT, logs / "check-help.txt"
            )
        )
        check_dir = output / "checked-spec"
        commands.append(
            _run_capture(
                [
                    "boltzgen",
                    "check",
                    str(SPEC_PATH),
                    "--output",
                    str(check_dir),
                    "--cache",
                    "/tmp/hf-cache",
                ],
                REMOTE_ROOT,
                logs / "check.txt",
            )
        )
        if commands[-1]["exit_code"] != 0:
            raise RuntimeError("boltzgen check failed; see logs/check.txt")

        commands.append(
            _run_capture(
                [
                    "boltzgen",
                    "run",
                    str(SPEC_PATH),
                    "--output",
                    str(output / "pipeline"),
                    "--protocol",
                    "peptide-anything",
                    "--num_designs",
                    str(num_designs),
                    "--budget",
                    str(budget),
                    "--diffusion_batch_size",
                    "1",
                    "--devices",
                    "1",
                    "--num_workers",
                    "1",
                    "--cache",
                    "/tmp/hf-cache",
                ],
                REMOTE_ROOT,
                logs / "run.txt",
            )
        )
        if commands[-1]["exit_code"] != 0:
            raise RuntimeError("boltzgen run failed; see logs/run.txt")
    except BaseException as exc:  # checkpoint diagnostics even for pipeline failures
        error = f"{type(exc).__name__}: {exc}"

    metadata = {
        "app": APP_NAME,
        "pinned_commit": PINNED_COMMIT,
        "source_revision": source_revision,
        "num_designs": num_designs,
        "budget": budget,
        "protocol": "peptide-anything",
        "diffusion_batch_size": 1,
        "generation_seed": None,
        "seed_note": "Pinned CLI exposes no generation seed; resolved configs and every output retained. Do not claim bitwise deterministic generation.",
        "target_sha256": _sha256(TARGET_PATH.read_bytes()),
        "spec_sha256": _sha256(SPEC_PATH.read_bytes()),
        "device_request": "L4",
        "source_spec": "analysis/boltzgen-pocket.yaml",
        "target": "KRAS chain A + GDP chain C from 5XCO; bound peptide chain B excluded",
        "commands": commands,
        "error": error,
        "elapsed_seconds": time.time() - started,
    }
    artifacts=[]
    for path in sorted(Path('/tmp/hf-cache').glob('**/snapshots/*/*')):
        if path.is_file() and path.suffix in ('.ckpt','.zip'):
            digest=hashlib.sha256()
            with path.open('rb') as handle:
                for chunk in iter(lambda:handle.read(1024*1024),b''):digest.update(chunk)
            artifacts.append({'snapshot_path':str(path.relative_to('/tmp/hf-cache')),'sha256':digest.hexdigest(),'bytes':path.stat().st_size})
    metadata['downloaded_artifacts']=artifacts
    (run_root / "run-metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))
    archive = _tar_bytes(run_root)
    return {
        "metadata": metadata,
        "archive_name": f"boltzgen-{num_designs}-designs.tar.gz",
        "archive_sha256": _sha256(archive),
        "archive_bytes": archive,
    }


@app.local_entrypoint()
def main(
    num_designs: int = 2,
    budget: int = DEFAULT_BUDGET,
    out_dir: str = "results/modal-boltzgen",
) -> None:
    """Explicit invocation only; supports calibration (2) then capped (<=60)."""
    destination = Path(out_dir)
    if destination.exists():
        raise ValueError(f"output directory exists: {destination}")
    result = run_boltzgen.remote(num_designs=num_designs, budget=budget)
    destination.mkdir(parents=True)
    (destination / result["archive_name"]).write_bytes(result["archive_bytes"])
    (destination / "remote-metadata.json").write_text(
        json.dumps(
            {
                "metadata": result["metadata"],
                "archive_name": result["archive_name"],
                "archive_sha256": result["archive_sha256"],
                "archive_bytes": len(result["archive_bytes"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result['metadata']['error']:
        raise RuntimeError(result['metadata']['error'])
