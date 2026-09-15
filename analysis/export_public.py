"""Build a bounded, offline public export without credentials or cached literature.

This module is intentionally opt-in.  Importing it and running the repository's
normal analysis scripts does not create an export.  Run it from the repository
root only after the campaign owner has reviewed the allowlist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = ROOT / "dist" / "public-KRpep-Zero"

# Deliberately explicit: adding a new result requires a conscious review.
ROOT_FILES = (
    ".gitignore", "LICENSE", "README.md", "PROTOCOL.md", "PROTOCOL_REMEDIATION_V2.md",
    "PROVENANCE.md", "BRIEF.md", "POCKET.md", "CAMPAIGN_STATE.json",
    "target.fasta", "target_wt.fasta", "requirements-analysis.txt",
    "THIRD_PARTY_NOTICES.md", "PROTOCOL_PROTENIX_DIAGNOSTIC.md", "DEMO_GUIDE.md",
)
TARGET_FILES = (
    "P01111.json", "P01112.json", "P01116.json", "P01116-2.fasta",
    "5xco.cif", "5xco-entry.json", "5xco-reference.cif", "5xco-reference.pdb",
    "kras-g12d-gdp.cif", "contacts.csv", "alignment-mapping.csv",
    "ras-aligned.fasta", "ras-alignment-summary.json", "target-qc.json",
)
CONTROL_FILES = ("controls.json", "validation-inputs.json", "per-seed.csv", "gate-summary.json", "structure-audit.json")
ESM_FILES = ("profile.csv", "substitutions.csv", "metadata.json", "esmc300m_masked_logits.npz")
REMEDIATION_FILES = (
    "status.json", "geometry-evaluator-qc.json", "bond-guidance-audit.json",
    "reference-graph-qc.json", "preregistration-v2.json",
)
PROTENIX_RUNS = (
    "protenix-diagnostic-001",
    "protenix-base-default-diagnostic-001",
)
SECRET_PATTERNS = (
    ("private-key", re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("bearer-token", re.compile(rb"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{12,}")),
    ("secret-assignment", re.compile(rb"(?i)(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{12,}")),
    ("provider-token", re.compile(rb"(?i)\b(?:sk|hf|xoxb|xoxp)-[A-Za-z0-9_-]{16,}")),
    ("aws-access-key-shape", re.compile(rb"AKIA[0-9A-Z]{16}")),
)


def copy_file(src: Path, dest_root: Path, rel: str) -> None:
    if not src.is_file():
        raise FileNotFoundError(src)
    dst = dest_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_many(src_root: Path, dest_root: Path, predicate) -> int:
    count = 0
    for src in sorted(p for p in src_root.rglob("*") if p.is_file() and predicate(p)):
        copy_file(src, dest_root, str(src.relative_to(ROOT)))
        count += 1
    return count


def sanitize_run_metadata(src: Path, dest: Path) -> None:
    """Retain reproducibility fields while removing host paths and raw logs."""
    data = json.loads(src.read_text())
    scalar_keys = (
        "code_revision", "weights_revision", "error", "protocol_sha256",
        "affinity_inference_requested", "gpu", "elapsed_seconds", "seeds",
    "samples_per_seed", "msa_sha256", "fixed_preprocessing_hashes", "assets",
    )
    keep = {k: data[k] for k in scalar_keys if k in data}
    commands = []
    for item in data.get("commands", []):
        argv = []
        for arg in item.get("argv", []):
            value = str(arg)
            if value.startswith("/"):
                value = "<runtime-path>"
            argv.append(value)
        commands.append({k: item[k] for k in ("id", "seed", "exit_code", "elapsed_seconds") if k in item} | {"argv": argv})
    keep["commands"] = commands
    keep["scope"] = "Sanitized public receipt; host paths, credentials, provider account data and raw logs omitted."
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(keep, indent=2, sort_keys=True) + "\n")


def sanitize_protenix_metadata(src: Path, dest: Path) -> None:
    """Keep Protenix audit fields while removing runtime-local paths."""
    data = json.loads(src.read_text())
    keep_keys = (
        "source_commit", "model", "run_id", "gpu", "protocol_sha256",
        "input_sha256", "msa_sha256", "assets", "elapsed_seconds",
        "exit_code", "error", "scope",
    )
    keep = {k: data[k] for k in keep_keys if k in data}
    command = []
    for arg in data.get("command", []):
        value = str(arg)
        if value.startswith("/"):
            value = "<runtime-path>"
        command.append(value)
    if command:
        keep["command"] = command
    keep["public_receipt_scope"] = (
        "Sanitized Protenix diagnostic receipt; host paths, raw logs, archives, "
        "provider account data and model weights omitted."
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(keep, indent=2, sort_keys=True) + "\n")


def sanitized_source_receipts(src: Path, dest: Path) -> None:
    """Write URL/accession/hash provenance without local paths or raw snapshots."""
    data = json.loads(src.read_text())
    rows = data if isinstance(data, list) else [data]
    allowed = ("file", "url", "retrieved_at_utc", "sha256", "bytes")
    clean = [{k: row[k] for k in allowed if k in row} for row in rows]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(clean if isinstance(data, list) else clean[0], indent=2, sort_keys=True) + "\n")


def hash_manifest(dest: Path) -> dict:
    files = []
    for path in sorted(p for p in dest.rglob("*") if p.is_file()):
        if path.name == "release-manifest.json" or '__pycache__' in path.parts or '.git' in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": str(path.relative_to(dest)), "bytes": path.stat().st_size, "sha256": digest})
    return {"format": 1, "scope": "Bounded public offline export", "files": files}


def verify_existing(dest: Path) -> None:
    manifest_path = dest / "release-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"refusing overwrite: {dest} is not a verified exporter output")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('format')!=1 or manifest.get('scope')!='Bounded public offline export':
        raise RuntimeError('Not an export produced by this utility')
    expected = {(x["path"], x["bytes"], x["sha256"]) for x in manifest.get("files", [])}
    actual = hash_manifest(dest)["files"]
    got = {(x["path"], x["bytes"], x["sha256"]) for x in actual}
    if expected != got:
        raise RuntimeError(f"refusing overwrite: existing export failed manifest verification: {dest}")


def scan_secrets(dest: Path) -> list[tuple[str, str]]:
    hits = []
    for path in sorted(p for p in dest.rglob("*") if p.is_file()):
        data = path.read_bytes()
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                hits.append((str(path.relative_to(dest)), label))
    return hits


def build(dest: Path = DEFAULT_DEST) -> Path:
    if dest.exists():
        verify_existing(dest)
        shutil.rmtree(dest)
    stage = dest.parent / f".{dest.name}.staging"
    if stage.exists():
        raise RuntimeError(f"refusing to use pre-existing staging directory: {stage}")
    stage.mkdir(parents=True)
    try:
        for rel in ROOT_FILES:
            copy_file(ROOT / rel, stage, rel)
        copy_file(ROOT/'results/reproducibility-qc.json',stage,'results/reproducibility-qc.json')
        for rel in TARGET_FILES:
            copy_file(ROOT / "results" / "target" / rel, stage, f"results/target/{rel}")
        sanitized_source_receipts(ROOT / "results/target/source-receipts.json", stage / "results/target/source-receipts.json")
        sanitized_source_receipts(ROOT / "results/target/isoform-receipt.json", stage / "results/target/isoform-receipt.json")
        for rel in CONTROL_FILES:
            copy_file(ROOT / "results" / "controls" / rel, stage, f"results/controls/{rel}")
        for rel in ESM_FILES:
            copy_file(ROOT / "results" / "esm" / rel, stage, f"results/esm/{rel}")
        for rel in REMEDIATION_FILES:
            copy_file(ROOT / "results" / "remediation" / rel, stage, f"results/remediation/{rel}")

        # Scientific reports and chemistry inputs are small, reviewable artifacts.
        copy_many(ROOT / "results", stage, lambda p: p.parent == ROOT / "results" and p.suffix == ".md")
        for name in ("graphs.json", "KRpep-2d.smiles", "SCRAMBLE-20260914.smiles", "KRpep-2d.atom-map.json", "SCRAMBLE-20260914.atom-map.json"):
            copy_file(ROOT / "results" / "remediation" / "full-molecule" / name, stage, f"results/remediation/full-molecule/{name}")

        for folder in ('pose-audit','study-package','licenses','protenix-inputs'):
            copy_many(ROOT/'results'/folder,stage,lambda p:p.suffix in ('.json','.csv','.md'))
        for run_name in PROTENIX_RUNS:
            run = ROOT / "results" / run_name
            if not run.is_dir():
                continue
            for rel in (
                "extracted/input.json",
                "extracted/PROTOCOL_PROTENIX_DIAGNOSTIC.md",
            ):
                src = run / rel
                if src.is_file():
                    copy_file(src, stage, str(src.relative_to(ROOT)))
            for rel in ("receipt.json", "extracted/metadata.json"):
                src = run / rel
                if src.is_file():
                    sanitize_protenix_metadata(src, stage / str(src.relative_to(ROOT)))
            for sub in ("analysis", "extracted/predictions"):
                src_root = run / sub
                if src_root.is_dir():
                    copy_many(src_root, stage, lambda p: p.suffix in (".json", ".csv", ".cif"))
        for name in ('KRpep-Zero-report.pdf','KRpep-Zero-brief.pdf'):
            copy_file(ROOT/'output/pdf'/name,stage,f'output/pdf/{name}')
        name='KRpep-Zero-overview.pptx'
        copy_file(ROOT/'output/presentation'/name,stage,f'output/presentation/{name}')
        copy_file(ROOT/'build_overview.mjs',stage,'build_overview.mjs')

        # Dashboard code is static and reviewed; source snapshots and logs are excluded.
        for folder in ("assets", "reports", "vendor", "data"):
            copy_many(ROOT / "dashboard" / folder, stage, lambda p: True)
        for rel in ("index.html", "viewer.js", "campaign-data.js"):
            copy_file(ROOT / "dashboard" / rel, stage, f"dashboard/{rel}")
        copy_many(ROOT / 'results/figures',stage,lambda p: p.suffix in ('.png','.svg','.json'))
        copy_many(ROOT / 'results/control-remediation-v2-002/analysis',stage,lambda p: p.name in ('per-seed.csv','gate-summary.json','structure-audit.json'))
        # Preserve rejected generator structures and filter evidence with clear labels.
        generator=ROOT/'results/boltzgen-calibration-003/extracted/output/pipeline'
        copy_many(generator/'final_ranked_designs',stage,lambda p: p.suffix in ('.csv','.cif'))

        for src in sorted((ROOT / "analysis").glob("*.py")) + sorted((ROOT / "analysis").glob("*.cjs")):
            copy_file(src, stage, str(src.relative_to(ROOT)))

        # Preserve only portable prediction artifacts; never publish archives, logs,
        # requirements, lightning metadata, or the original host-dependent receipt.
        for run in (ROOT / "results" / "boltz-control-calibration-002" / "extracted",
                    ROOT / "results" / "control-remediation-v2-002" / "extracted"):
            if not run.is_dir():
                continue
            copy_many(run, stage, lambda p: (
                p.name.endswith("_model_0.cif") or p.name.startswith("confidence_") and p.suffix == ".json"
                or "processed" in p.parts
                or p.name == "PROTOCOL_REMEDIATION_V2.md"
            ))
            if (run / "metadata.json").is_file():
                label = "v2" if "remediation" in str(run) else "v1"
                sanitize_run_metadata(run / "metadata.json", stage / str((run / "metadata.json").relative_to(ROOT)))

        hits = scan_secrets(stage)
        if hits:
            # Report only paths and detector labels; never print matched bytes.
            raise RuntimeError("secret-pattern scan failed: " + ", ".join(f"{p} [{label}]" for p, label in hits))
        manifest = hash_manifest(stage)
        (stage / "release-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        dest.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(dest)
        return dest
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument('--verify-only',action='store_true',help='Verify all recorded export hashes without modifying files')
    args = parser.parse_args()
    if args.verify_only:
        verify_existing(args.dest.resolve());print('Every public export artifact matches its recorded SHA-256 hash.');return 0
    path = build(args.dest.resolve())
    print(f"public export written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
