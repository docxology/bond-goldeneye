"""Regional grid-resilience figure for ARKANGEL."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend, deterministic in any environment

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

from goldeneye.emp_model import EmpWeapon  # noqa: E402
from goldeneye.grid_resilience import (  # noqa: E402
    node_survival_probability,
    resilience_report,
)
from goldeneye.scenario import ARKANGEL, ArkangelScenario  # noqa: E402

__all__ = ["plot_grid_resilience"]


def plot_grid_resilience(
    path: str | Path,
    scenario: ArkangelScenario = ARKANGEL,
) -> Path:
    """Render the grid-resilience figure to ``path`` (PNG)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    grid = scenario.grid
    weapon: EmpWeapon = scenario.weapon
    report = resilience_report(grid, weapon)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    fig.suptitle("Severnaya regional power network — EMP resilience", fontsize=13)

    # (1) network map with node survival colouring
    ax = axes[0]
    survivals = {node.name: node_survival_probability(grid, weapon, node.name) for node in grid.nodes}
    positions = {node.name: (node.x_km, node.y_km) for node in grid.nodes}
    down = set(report["down_nodes"])
    for line in grid.lines:
        ax.plot(
            [positions[line.node_a][0], positions[line.node_b][0]],
            [positions[line.node_a][1], positions[line.node_b][1]],
            color="grey",
            lw=1.0,
            zorder=1,
        )
    for node in grid.nodes:
        surv = survivals[node.name]
        marker = "X" if node.name in down else "o"
        size = 140 if node.critical else 60
        color = surv if node.name not in down else 0.0
        ax.scatter(
            positions[node.name][0],
            positions[node.name][1],
            s=size,
            c=[color],
            cmap="RdYlGn",
            vmin=0.0,
            vmax=1.0,
            marker=marker,
            edgecolors="black",
            linewidths=0.6,
            zorder=2,
        )
        ax.annotate(node.name, positions[node.name], fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("x offset from nadir (km)")
    ax.set_ylabel("y offset from nadir (km)")
    ax.set_title("Network nodes by survival probability (X = certainly failed)")
    ax.invert_yaxis()  # y grows northward; show it descending for readability

    sm = ScalarMappable(norm=Normalize(0, 1), cmap="RdYlGn")
    fig.colorbar(sm, ax=ax, label="node survival probability")

    # (2) critical-load reliability + redundancy
    ax = axes[1]
    loads = [row["load"] for row in report["per_load"]]
    reliabilities = [row["reliability"] for row in report["per_load"]]
    disjoint = [row["disjoint_paths"] for row in report["per_load"]]
    xs = range(len(loads))
    ax.bar(xs, reliabilities, color="steelblue", label="best-path reliability")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(loads, fontsize=8, rotation=15)
    ax.set_ylabel("P(load served)")
    ax.set_ylim(0.0, 1.05)
    for i, (rel, disp) in enumerate(zip(reliabilities, disjoint, strict=True)):
        ax.text(i, rel + 0.02, f"{rel:.2f}", ha="center", fontsize=7)
    twins = ax.twinx()
    twins.plot(xs, disjoint, color="tab:orange", marker="o", label="edge-disjoint paths")
    twins.set_ylabel("edge-disjoint paths", color="tab:orange")
    twins.set_ylim(0.0, max(disjoint) + 1 if disjoint else 1.0)
    ax.set_title("Critical-load resilience")
    ax.legend(loc="upper left", fontsize=7)

    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
