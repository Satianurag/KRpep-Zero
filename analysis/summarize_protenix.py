"""Summarize Protenix diagnostic attempts for project artifacts."""
from __future__ import annotations

from pathlib import Path
import csv
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "submission"
RUNS = (
    ("protenix-diagnostic-001", "Protenix-v2"),
    ("protenix-base-default-diagnostic-001", "Protenix base default v1.0.0"),
)
STATUS_NAMES = {
    "failed_before_prediction": "failed before prediction",
    "failed_with_partial_outputs": "failed with partial outputs",
    "returned_without_expected_outputs": "returned without expected outputs",
    "pending_or_unreturned": "pending",
    "completed": "completed",
    "missing": "not returned",
}


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def summarize_run(folder: str, label: str) -> dict:
    run = ROOT / "results" / folder
    meta = load_json(run / "receipt.json") or load_json(run / "extracted" / "metadata.json")
    out = {
        "run_id": folder,
        "label": label,
        "exists": run.is_dir(),
        "model": meta.get("model"),
        "gpu": meta.get("gpu"),
        "elapsed_seconds": meta.get("elapsed_seconds"),
        "exit_code": meta.get("exit_code"),
        "error": meta.get("error"),
        "source_commit": meta.get("source_commit"),
        "protocol_sha256": meta.get("protocol_sha256"),
        "prediction_cif_count": 0,
        "status": "missing",
    }
    if not run.is_dir():
        return out
    pred_root = run / "extracted" / "predictions"
    out["prediction_cif_count"] = len(list(pred_root.rglob("*.cif"))) if pred_root.is_dir() else 0
    if meta.get("error"):
        out["status"] = "failed_before_prediction" if out["prediction_cif_count"] == 0 else "failed_with_partial_outputs"
    elif out["prediction_cif_count"] == 6:
        out["status"] = "completed"
    elif meta:
        out["status"] = "returned_without_expected_outputs"
    else:
        out["status"] = "pending_or_unreturned"

    per_seed = run / "analysis" / "per-seed.csv"
    if per_seed.is_file():
        rows = list(csv.DictReader(per_seed.open()))
        out["analysis_rows"] = len(rows)
        out["positive_core_rmsd_A"] = [
            float(r["core_CA_RMSD_A"]) for r in rows
            if r.get("control_id") == "KRpep-2d" and r.get("core_CA_RMSD_A")
        ]
        out["positive_native_contacts_recovered"] = [
            int(r["native_contacts_recovered"]) for r in rows
            if r.get("control_id") == "KRpep-2d" and r.get("native_contacts_recovered")
        ]
        out["all_bonds_in_bounds"] = all(int(r["bonds_in_expanded_bounds"]) == 183 for r in rows)
        out["all_stereocenters_correct"] = all(int(r["stereocenters_correct"]) == 20 for r in rows)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    attempts = [summarize_run(folder, label) for folder, label in RUNS]
    summary = {
        "scope": "Exploratory Protenix cross-model control diagnostic; no candidate gate change.",
        "date_IST": "2026-09-14",
        "attempts": attempts,
    }
    (OUT / "protenix-diagnostic-summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Protenix diagnostic summary",
        "",
        "Exploratory cross-model control diagnostic. These attempts do not alter the failed Boltz gates or justify candidate selection.",
        "",
    ]
    for item in attempts:
        lines.append(f"## {item['label']}")
        lines.append("")
        lines.append(f"- Status: {STATUS_NAMES.get(item['status'], item['status'])}")
        if item.get("model"):
            lines.append(f"- Model: `{item['model']}`")
        if item.get("prediction_cif_count") is not None:
            lines.append(f"- Prediction CIFs: {item['prediction_cif_count']}")
        if item.get("error"):
            lines.append(f"- Error: {item['error']}")
        if item.get("positive_core_rmsd_A"):
            values = ", ".join(f"{v:.2f}" for v in item["positive_core_rmsd_A"])
            lines.append(f"- Positive-control core RMSD (A): {values}")
        if item.get("positive_native_contacts_recovered"):
            values = ", ".join(str(v) for v in item["positive_native_contacts_recovered"])
            lines.append(f"- Native contacts recovered out of 41: {values}")
        lines.append("")
    (OUT / "protenix-diagnostic-summary.md").write_text("\n".join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
