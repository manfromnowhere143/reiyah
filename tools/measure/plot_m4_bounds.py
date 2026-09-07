#!/usr/bin/env python3
"""Render two retained synthetic bound counterexamples; no empirical data."""
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / "evidence/m4-bounds/audit-0.1.0.json").read_bytes())
    toy = data["authored_controls"][0]
    thin = data["historical_report_calls"][-1]
    plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "svg.hashsalt": "reiyah.m4-bounds.0.1.0"})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    navy, rust = "#15394c", "#b9472d"
    x = np.linspace(2, 4, 600)
    axes[0].plot(x, x * (x + 3) / (x + 1)**2, color=navy, label="Exact coefficient curve")
    grid = np.linspace(0, 11, 21)
    grid = grid[(grid >= 2) & (grid <= 4)]
    axes[0].scatter(grid, grid * (grid + 3) / (grid + 1)**2, color=rust, zorder=3, label="Retained grid points")
    upper = float(Fraction(toy["result"]["supremum"]["supremum_enclosure"][1]))
    old = toy["historical"]["grid_supremum"]
    axes[0].axhline(old, color=rust, ls="--", lw=1)
    axes[0].scatter([3], [upper], s=55, marker="D", color=navy, zorder=4)
    axes[0].annotate("True maximum: 9/8 at a = 3", xy=(3, upper), xytext=(2.05, 1.1262), fontsize=10)
    axes[0].set(xlabel="Both-error mass a (zoom near maximum)", ylabel="Coincidence coefficient C",
                title="A sampled maximum can exclude feasible values", ylim=(1.113, 1.128))
    axes[0].legend(loc="lower right", frameon=False, fontsize=9)
    x = np.linspace(0.001, 22, 600)
    axes[1].plot(x, 1 + 975 / (x + 20), color=navy, label="C(a, 0, 20, 975), a > 0")
    grid = np.linspace(0, 22, 21)[1:]
    axes[1].scatter(grid, 1 + 975 / (grid + 20), color=rust, s=22, label="Retained grid points")
    limit = float(Fraction(thin["corrected"]["supremum"]["supremum_enclosure"][1]))
    axes[1].scatter([0], [limit], s=70, facecolors="white", edgecolors=navy, linewidths=1.7, zorder=4)
    axes[1].annotate("Finite supremum: 49.75\nOpen point: C is undefined at a = 0",
                     xy=(0, limit), xytext=(4.5, 49.7), fontsize=10, va="center",
                     arrowprops={"arrowstyle": "-", "color": navy})
    axes[1].set(xlabel="Both-error mass a", ylabel="Coincidence coefficient C",
                title="Retained F-03 permits a finite boundary limit", xlim=(-0.6, 22.6), ylim=(22, 54))
    axes[1].legend(loc="lower left", frameon=False, fontsize=9)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.15)
    fig.suptitle("Synthetic mathematical audit; no detector-performance claim", fontsize=14, fontweight="bold")
    out = root / "docs/figures/m4-rectangular-bounds"
    fig.savefig(out.with_suffix(".svg"), metadata={"Date": None})
    svg = out.with_suffix(".svg")
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(out.with_suffix(".png"), dpi=170, metadata={"Software": "Reiyah synthetic M4 bound audit"})


if __name__ == "__main__":
    main()
