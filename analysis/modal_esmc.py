"""Modal entrypoint for masked-residue ESMC-300M KRAS profiles.

Preparation only: this file is intentionally not executed during setup. The
weights revision is required at invocation time; no token is embedded here.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "krpep-zero-esmc-profile"
MODEL_REPO = "biohub/esmc-300m-2024-12"
ESM_GIT = "ba4d7124864eed323a93bf3cfefcd958f573b75a"
TRANSFORMERS_GIT = "ef32577f55da19a4989cd7b22e004dc43a4998cb"
MODEL_NAME = "esmc_300m"
EXPECTED_LENGTH = 169
HOTSPOT_QC_POSITIONS = (12, 13, 61)
CANONICAL_AA = tuple("ACDEFGHIKLMNPQRSTVWY")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install_from_requirements(str(Path(__file__).resolve().parents[1] / "setup/esmc-cloud-base.lock.txt"))
    .pip_install(
        f"git+https://github.com/Biohub/esm.git@{ESM_GIT}",
        f"git+https://github.com/Biohub/transformers.git@{TRANSFORMERS_GIT}",
        extra_options="--no-deps",
    )
)
app = modal.App(APP_NAME)


def _sha256_files(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        result[str(path.relative_to(root))] = digest.hexdigest()
    return result


def _parse_fasta(text: str, source: str) -> tuple[str, str]:
    lines = text.splitlines()
    headers = [line[1:].strip() for line in lines if line.startswith(">")]
    sequence = "".join(line.strip() for line in lines if line and not line.startswith(">"))
    if len(headers) != 1 or not sequence:
        raise ValueError(f"{source}: expected one non-empty FASTA record")
    return headers[0], sequence.upper().replace(" ", "")


def _validate_inputs(wt: str, g12d: str) -> None:
    for label, sequence in (("WT", wt), ("G12D", g12d)):
        if len(sequence) != EXPECTED_LENGTH:
            raise ValueError(f"{label} length {len(sequence)} != {EXPECTED_LENGTH}")
        if any(residue not in CANONICAL_AA for residue in sequence):
            raise ValueError(f"{label} contains a non-canonical residue")
    mismatches = [i for i, (a, b) in enumerate(zip(wt, g12d), start=1) if a != b]
    if mismatches != [12] or wt[11] != "G" or g12d[11] != "D":
        raise ValueError(f"expected exactly WT G12D mismatch at position 12; got {mismatches}")


def _masked_logits(model: Any, sequence: str) -> Any:
    import torch

    tokenizer = model.tokenizer
    tokens = tokenizer(sequence, add_special_tokens=True, return_tensors="pt")["input_ids"].to(model.device)
    assert tokens.shape == (1, EXPECTED_LENGTH + 2)
    mask_id = tokenizer.mask_token_id
    rows = []
    with torch.inference_mode():
        for position in range(EXPECTED_LENGTH):
            masked = tokens.clone()
            masked[0, position + 1] = mask_id
            output = model(sequence_tokens=masked)
            row = output.sequence_logits[0, position + 1, :].detach().float().cpu()
            if row.numel() != 64 or not torch.isfinite(row).all():
                raise ValueError(f"invalid logits at 1-based position {position + 1}")
            rows.append(row)
            if (position + 1) % 50 == 0:
                print(f"Scored {position+1}/{EXPECTED_LENGTH} masked positions", flush=True)
    return torch.stack(rows).numpy()


@app.function(
    image=image,
    gpu="L4",
    max_containers=1,
    min_containers=0,
    timeout=900,
    retries=0,
    scaledown_window=2,
    startup_timeout=300,
    cpu=2,
    memory=8192,
)
def masked_profile(wt_fasta_text: str, g12d_fasta_text: str, weights_revision: str) -> dict[str, Any]:
    """Download/checksum pinned weights, then compute CPU-returned raw logits."""
    import numpy as np
    import torch
    from esm.models.esmc import ESMC
    from esm.tokenization import get_esmc_model_tokenizers
    from huggingface_hub import HfApi, snapshot_download

    started = time.time()
    if len(weights_revision) != 40 or any(c not in '0123456789abcdef' for c in weights_revision):
        raise ValueError("weights_revision must be an immutable HF revision or commit")
    model_info = HfApi().model_info(MODEL_REPO, revision=weights_revision, token=False)
    if model_info.gated or model_info.private:
        raise RuntimeError("expected a public ungated checkpoint; refusing credential fallback")
    wt_name, wt = _parse_fasta(wt_fasta_text, "WT FASTA")
    g12d_name, g12d = _parse_fasta(g12d_fasta_text, "G12D FASTA")
    _validate_inputs(wt, g12d)
    snapshot = Path(snapshot_download(repo_id=MODEL_REPO, revision=weights_revision, token=False))
    resolved_revision = snapshot.name
    checksums = _sha256_files(snapshot)
    weight_files = sorted(snapshot.glob("data/weights/*.pth"))
    if len(weight_files) != 1:
        raise RuntimeError(f"expected one legacy ESMC .pth checkpoint, found {weight_files}")
    torch.manual_seed(17)
    model = ESMC(d_model=960, n_heads=15, n_layers=30,
                 tokenizer=get_esmc_model_tokenizers(), use_flash_attn=False).eval().to("cuda")
    checkpoint = torch.load(weight_files[0], map_location="cpu", weights_only=True)
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        checkpoint = checkpoint["state_dict"]
    if not isinstance(checkpoint, dict):
        raise TypeError("ESMC checkpoint did not contain a state dict")
    model.load_state_dict(checkpoint, strict=True)
    wt_logits = _masked_logits(model, wt)
    g12d_logits = _masked_logits(model, g12d)
    if wt_logits.shape != (EXPECTED_LENGTH, 64) or g12d_logits.shape != (EXPECTED_LENGTH, 64):
        raise ValueError("unexpected raw-logit dimensions")
    pos12_max_abs_logit_delta = float(np.max(np.abs(wt_logits[11] - g12d_logits[11])))
    if not np.isfinite(pos12_max_abs_logit_delta) or pos12_max_abs_logit_delta > 1e-5:
        raise ValueError(f"identical masked context QC failed: {pos12_max_abs_logit_delta}")
    technical_qc = {
        str(position): {
            "wt_shape": list(wt_logits[position - 1].shape),
            "g12d_shape": list(g12d_logits[position - 1].shape),
            "wt_finite": bool(np.isfinite(wt_logits[position - 1]).all()),
            "g12d_finite": bool(np.isfinite(g12d_logits[position - 1]).all()),
        }
        for position in HOTSPOT_QC_POSITIONS
    }
    result = {
        "wt_name": wt_name, "g12d_name": g12d_name,
        "wt_sequence": wt, "g12d_sequence": g12d,
        "wt_logits": wt_logits, "g12d_logits": g12d_logits,
        "metadata": {
            "model_name": MODEL_NAME, "model_repo": MODEL_REPO,
            "requested_weights_revision": weights_revision,
            "resolved_snapshot_revision": resolved_revision,
            "hf_model_sha": getattr(model_info, "sha", None),
            "hf_model_gated": bool(model_info.gated),
            "hf_model_private": bool(model_info.private),
            "checkpoint_relative_path": str(weight_files[0].relative_to(snapshot)),
            "weight_sha256": checksums,
            "esm_git_revision": ESM_GIT, "transformers_git_revision": TRANSFORMERS_GIT,
            "input_length": EXPECTED_LENGTH, "canonical_alphabet": "".join(CANONICAL_AA),
            "mask_context_position_12_max_abs_logit_delta": pos12_max_abs_logit_delta,
            "hotspot_qc_positions": list(HOTSPOT_QC_POSITIONS),
            "technical_qc": technical_qc, "credentials_used": False,
            "seed":17, "dtype":"float32", "elapsed_seconds":time.time()-started,
            "device": str(torch.cuda.get_device_name(0)),
        },
    }
    result['profile_rows'], result['substitution_rows'] = _rows(result)
    return result


def _rows(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import numpy as np
    from esm.tokenization import get_esmc_model_tokenizers

    wt_logits = np.asarray(raw["wt_logits"], dtype=np.float64)
    g12d_logits = np.asarray(raw["g12d_logits"], dtype=np.float64)
    tok = get_esmc_model_tokenizers()
    token_ids = [tok.convert_tokens_to_ids(x) for x in CANONICAL_AA]
    rows: list[dict[str, Any]] = []
    substitutions: list[dict[str, Any]] = []
    for i, (wl, gl) in enumerate(zip(wt_logits, g12d_logits), start=1):
        wt_lp = wl - np.logaddexp.reduce(wl); g_lp = gl - np.logaddexp.reduce(gl)
        wt_native = raw["wt_sequence"][i - 1]; g_native = raw["g12d_sequence"][i - 1]
        wt_native_lp = float(wt_lp[tok.convert_tokens_to_ids(wt_native)])
        g_native_lp = float(g_lp[tok.convert_tokens_to_ids(g_native)])
        wt_non = [wt_lp[tok.convert_tokens_to_ids(x)] - wt_native_lp for x in CANONICAL_AA if x != wt_native]
        g_non = [g_lp[tok.convert_tokens_to_ids(x)] - g_native_lp for x in CANONICAL_AA if x != g_native]
        wt_can = wt_lp[token_ids]; g_can = g_lp[token_ids]
        wt_p = np.exp(wt_can - np.logaddexp.reduce(wt_can)); g_p = np.exp(g_can - np.logaddexp.reduce(g_can))
        rows.append({"position": i, "wt_residue": wt_native, "g12d_residue": g_native,
                     "wt_canonical20_entropy": float(-(wt_p * np.log(wt_p)).sum()),
                     "g12d_canonical20_entropy": float(-(g_p * np.log(g_p)).sum()),
                     "wt_mean_nonnative_minus_native_logprob": float(np.mean(wt_non)),
                     "g12d_mean_nonnative_minus_native_logprob": float(np.mean(g_non)),
                     "wt_native_logprob": wt_native_lp, "g12d_native_logprob": g_native_lp,
                     "g12d_minus_wt_native_logprob": g_native_lp - wt_native_lp})
        for model_name, lp, native in (("WT", wt_lp, wt_native), ("G12D", g_lp, g_native)):
            native_lp = float(lp[tok.convert_tokens_to_ids(native)])
            for substitution in CANONICAL_AA:
                if substitution != native:
                    sub_lp = float(lp[tok.convert_tokens_to_ids(substitution)])
                    substitutions.append({"model": model_name, "position": i, "native": native,
                                          "substitution": substitution, "logprob": sub_lp,
                                          "logprob_minus_native": sub_lp - native_lp})
    return rows, substitutions


@app.local_entrypoint()
def main(wt_fasta: str = "target_wt.fasta", g12d_fasta: str = "target.fasta",
         weights_revision: str = "", out_dir: str = "results/esm") -> None:
    """Explicit invocation only; this entrypoint is not run during setup."""
    if not weights_revision:
        raise ValueError("pass --weights-revision with an immutable HF model revision")
    wt_text = Path(wt_fasta).read_text()
    g12d_text = Path(g12d_fasta).read_text()
    _validate_inputs(_parse_fasta(wt_text,'WT')[1], _parse_fasta(g12d_text,'G12D')[1])
    if Path(out_dir).exists():
        raise ValueError('Output directory exists; choose a new run directory')
    raw = masked_profile.remote(wt_text, g12d_text, weights_revision)
    import numpy as np

    output = Path(out_dir); output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "esmc300m_masked_logits.npz",
                        wt_logits=raw["wt_logits"], g12d_logits=raw["g12d_logits"])
    rows, substitutions = raw['profile_rows'], raw['substitution_rows']
    for name, values in (("profile.csv", rows), ("substitutions.csv", substitutions)):
        with (output / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(values[0])); writer.writeheader(); writer.writerows(values)
    metadata = dict(raw["metadata"]); metadata.update({"wt_name": raw["wt_name"], "g12d_name": raw["g12d_name"]})
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))
