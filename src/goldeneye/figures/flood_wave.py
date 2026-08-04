"""Ritter dam-break flood-wave figure for ARKANGEL."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend, deterministic in any environment

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from goldeneye.dam_security import (  # noqa: E402
    flood_arrival_time_s,
    ritter_depth_m,
)
from goldeneye.scenario import ARKANGEL, ArkangelScenario  # noqa: E402

__all__ = ["plot_flood_wave"]


def plot_flood_wave(
    path: str | Path,
    scenario: ArkangelScenario = ARKANGEL,
) -> Path:
    """Render the flood-wave figure to ``path`` (PNG)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    head_m = scenario.reservoir.head_m
    distance_m = scenario.facility_distance_km * 1000.0
    elevation_m = scenario.facility_elevation_m

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    fig.suptitle("Arkangel dam-break flood wave (Ritter, frictionless)", fontsize=13)

    # (1) downstream depth profiles at several times
    ax = axes[0]
    xs = np.linspace(0.0, 20000.0, 400)
    for t_s in (1200.0, 3600.0, 7200.0):
        depths = [ritter_depth_m(float(x), t_s, head_m) for x in xs]
        ax.plot(xs / 1000.0, depths, label=f"t = {t_s / 60.0:g} min")
    ax.axhline(4.0 / 9.0 * head_m, color="grey", ls=":", lw=0.9)
    ax.text(15.0, 4.0 / 9.0 * head_m + 0.5, "asymptote 4H/9", fontsize=7, color="grey")
    ax.set_xlabel("Distance downstream (km)")
    ax.set_ylabel("Water depth (m)")
    ax.set_title("Downstream flood depth")
    ax.legend(fontsize=7)

    # (2) depth at facility vs time, with arrival marker and risk band
    ax = axes[1]
    arrivals = flood_arrival_time_s(distance_m, head_m)
    times = np.linspace(arrivals, 6.0 * 3600.0, 400)
    depths = [ritter_depth_m(distance_m, t, head_m) for t in times]
    ax.plot(times / 60.0, depths, label="facility depth")
    ax.axvline(arrivals / 60.0, color="tab:orange", ls="--", lw=1.0, label="front arrival")
    ax.axhline(elevation_m, color="tab:red", ls="--", lw=1.0, label="facility elevation")
    ax.set_xlabel("Time since breach (min)")
    ax.set_ylabel("Depth at facility (m)")
    ax.set_title("Facility inundation")
    ax.legend(fontsize=7)

    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
