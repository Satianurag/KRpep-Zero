"""Offline plots for a completed masked ESMC profile run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


AA = list("ACDEFGHIKLMNPQRSTVWY")
QC_POSITIONS = (12, 13, 61)


def _read_run(run_dir: Path):
    import csv

    required = [run_dir / "profile.csv", run_dir / "substitutions.csv", run_dir / "metadata.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("completed ESM run is missing: " + ", ".join(missing))
    with (run_dir / "profile.csv").open(newline="") as handle:
        profile = list(csv.DictReader(handle))
    with (run_dir / "substitutions.csv").open(newline="") as handle:
        substitutions = list(csv.DictReader(handle))
    metadata = json.loads((run_dir / "metadata.json").read_text())
    if len(profile) != 169 or len(substitutions) != 169 * 2 * 19:
        raise ValueError("unexpected profile/substitution row count")
    return profile, substitutions, metadata


def _matrix(substitutions, model: str):
    matrix = np.full((169, 20), np.nan, dtype=float)
    native = [None] * 169
    for row in substitutions:
        if row["model"] != model:
            continue
        position = int(row["position"]) - 1
        substitution = row["substitution"]
        native[position] = row["native"]
        matrix[position, AA.index(substitution)] = float(row["logprob_minus_native"])
    for position, residue in enumerate(native):
        if residue is None:
            raise ValueError(f"missing {model} native residue at position {position + 1}")
        matrix[position, AA.index(residue)] = 0.0
    return matrix, native


def _annotate_qc(ax):
    for position, label in ((12.5, "12/13"), (61, "61")):
        ax.axvline(position - 1, color="#111111", linewidth=0.7, alpha=0.7)
        ax.text(position - 1, 19.4, label, va="top", ha="left", rotation=90, fontsize=7, color="#333333")


def render(run_dir: Path, out_dir: Path) -> tuple[Path, Path]:
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm

    profile, substitutions, metadata = _read_run(run_dir)
    wt, wt_native = _matrix(substitutions, "WT")
    g12d, g12d_native = _matrix(substitutions, "G12D")
    delta = g12d - wt
    wt_entropy = np.array([float(row["wt_canonical20_entropy"]) for row in profile])
    g_entropy = np.array([float(row["g12d_canonical20_entropy"]) for row in profile])
    native_delta = np.array([float(row["g12d_minus_wt_native_logprob"]) for row in profile])
    if not np.isfinite(np.concatenate([wt.ravel(), g12d.ravel(), delta.ravel(), wt_entropy, g_entropy, native_delta])).all():
        raise ValueError("plot inputs contain non-finite values")

    vmax = max(float(np.max(np.abs(wt))), float(np.max(np.abs(g12d))), 1e-6)
    dmax = max(float(np.max(np.abs(delta))), 1e-6)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    dnorm = TwoSlopeNorm(vmin=-dmax, vcenter=0, vmax=dmax)
    plt.rcParams.update({"font.size": 14, "axes.titlesize": 14, "axes.labelsize": 14,
                         "xtick.labelsize": 11, "ytick.labelsize": 11})
    fig = plt.figure(figsize=(16, 12), dpi=100, facecolor="white")
    heatmaps = [(wt, "WT masked log-odds: substitution − native", norm),
                (g12d, "G12D masked log-odds: substitution − native", norm),
                (delta, "G12D − WT masked log-odds", dnorm)]
    axes = [fig.add_axes([0.065,0.69,0.80,0.22]), fig.add_axes([0.065,0.40,0.80,0.22]), fig.add_axes([0.065,0.15,0.35,0.18])]
    ims = []
    for ax, (matrix, title, color_norm) in zip(axes, heatmaps):
        im = ax.imshow(matrix.T, aspect="auto", origin="lower", cmap="coolwarm", norm=color_norm, interpolation="nearest")
        ims.append(im)
        ax.set_title(title, loc="left", fontsize=14, weight="bold")
        ax.set_ylabel("substitution")
        ax.set_yticks(np.arange(20), AA)
        ax.set_xticks([0, 24, 49, 74, 99, 124, 149, 168], [1, 25, 50, 75, 100, 125, 150, 169])
        _annotate_qc(ax)
    axes[1].set_xlabel("")
    axes[2].set_xlabel("KRAS residue position")

    # Reserve a dedicated right margin so scales never cover the heatmaps.
    cbar_ax = fig.add_axes([0.885, 0.40, 0.015, 0.51])
    cbar = fig.colorbar(ims[0], cax=cbar_ax)
    cbar.set_label("log-odds: substitution − native (nats)", fontsize=12)
    cbar.ax.tick_params(labelsize=10)
    diff_cbar_ax = fig.add_axes([0.08, 0.074, 0.32, 0.012])
    diff_cbar = fig.colorbar(ims[2], cax=diff_cbar_ax, orientation="horizontal")
    diff_cbar.set_label("G12D − WT log-odds (nats)", fontsize=11, labelpad=2)
    diff_cbar.ax.tick_params(labelsize=10)

    ax = fig.add_axes([0.54,0.15,0.325,0.18])
    positions = np.arange(1, 170)
    ax.plot(positions, wt_entropy, color="#276fbf", label="WT canonical-20 entropy", linewidth=1.1)
    ax.plot(positions, g_entropy, color="#d1495b", label="G12D canonical-20 entropy", linewidth=1.1)
    ax.set_ylabel("canonical-20 entropy (nats)", color="#276fbf")
    ax.tick_params(axis="y", labelcolor="#276fbf")
    native_ax = ax.twinx()
    native_ax.plot(positions, native_delta, color="#333333", label="G12D − WT native log probability", linewidth=1.0, alpha=0.85)
    native_ax.set_ylabel("G12D − WT native log probability (nats)", color="#333333")
    native_ax.tick_params(axis="y", labelcolor="#333333")
    for position in QC_POSITIONS:
        ax.axvline(position, color="#777777", linewidth=0.7, alpha=0.7)
    ax.text(12.5, 0.97, "12/13", transform=ax.get_xaxis_transform(), fontsize=10, va="top", ha="left")
    ax.text(61, 0.97, "61", transform=ax.get_xaxis_transform(), fontsize=10, va="top", ha="left")
    ax.set_title("Difference and uncertainty summary", loc="left", fontsize=14, weight="bold")
    ax.set_xlabel("KRAS residue position")
    lines = ax.get_lines()[:2] + native_ax.get_lines()[:1]
    ax.legend(lines, [line.get_label() for line in lines], fontsize=10, loc="upper right", frameon=False)
    ax.grid(axis="y", alpha=0.2)

    qc = metadata.get("mask_context_position_12_max_abs_logit_delta", "n/a")
    fig.suptitle("ESMC300M masked per-residue KRAS profile", fontsize=17, weight="bold", y=0.985)
    fig.text(0.06, 0.012, f"Masked position 12 contexts identical; native baseline differs (WT G vs G12D D). Self-substitution cells = 0 by definition. Max raw-logit Δ12: {qc}.", fontsize=9)
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "esm-profile.png"
    svg = out_dir / "esm-profile.svg"
    fig.savefig(png, dpi=100)
    import matplotlib
    matplotlib.rcParams['svg.hashsalt']='KRpep-Zero'
    fig.savefig(svg,metadata={'Date':None})
    plt.close(fig)
    return png, svg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=Path("results/esm"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/figures"))
    args = parser.parse_args()
    png, svg = render(args.run_dir, args.out_dir)
    print(f"wrote {png}")
    print(f"wrote {svg}")


if __name__ == "__main__":
    main()
