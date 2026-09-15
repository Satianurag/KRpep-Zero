"""Plot completed Protenix base diagnostic pose metrics."""
from __future__ import annotations

from pathlib import Path
import csv

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "protenix-base-default-diagnostic-001" / "analysis" / "per-seed.csv"
OUT = ROOT / "results" / "figures"


def main() -> None:
    if not CSV.is_file():
        raise FileNotFoundError(CSV)
    rows = [r for r in csv.DictReader(CSV.open()) if r["control_id"] == "KRpep-2d"]
    if len(rows) != 3:
        raise RuntimeError(f"expected 3 positive-control rows, found {len(rows)}")
    seeds = [r["seed"] for r in rows]
    contacts = [int(r["native_contacts_recovered"]) for r in rows]
    rmsd = [float(r["core_CA_RMSD_A"]) for r in rows]

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.hashsalt": "krpep-zero-protenix",
    })
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), constrained_layout=True)
    x = np.arange(len(seeds))
    axes[0].bar(x, contacts, color="#16B8A6", width=0.62)
    axes[0].axhline(41, color="#102A43", lw=1.4, linestyle="--")
    axes[0].set_xticks(x, [f"seed {s}" for s in seeds])
    axes[0].set_ylim(0, 43)
    axes[0].set_ylabel("Native residue contacts recovered")
    axes[0].set_title("Protenix base: 5 A contact recovery")
    for i, value in enumerate(contacts):
        axes[0].text(i, value + 0.8, f"{value}/41", ha="center", va="bottom", fontsize=10)

    axes[1].bar(x, rmsd, color="#E75288", width=0.62)
    axes[1].set_xticks(x, [f"seed {s}" for s in seeds])
    axes[1].set_ylabel("Target-fitted core C-alpha RMSD, A")
    axes[1].set_title("Protenix base: positive-control pose")
    ymax = max(rmsd) * 1.25 if rmsd else 1
    axes[1].set_ylim(0, ymax)
    for i, value in enumerate(rmsd):
        axes[1].text(i, value + ymax * 0.03, f"{value:.2f}", ha="center", va="bottom", fontsize=10)

    fig.suptitle("Independent Protenix diagnostic, no candidate gate change", fontsize=15, fontweight="bold")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "protenix-base-diagnostic.png", dpi=200, facecolor="white")
    fig.savefig(OUT / "protenix-base-diagnostic.svg", metadata={"Date": "2026-09-14T00:00:00+05:30"}, facecolor="white")
    print("Wrote Protenix diagnostic figure.")


if __name__ == "__main__":
    main()
