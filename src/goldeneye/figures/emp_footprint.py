"""EMP threat-envelope and kill-radius figure for ARKANGEL."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend, deterministic in any environment

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from goldeneye.emp_model import EmpWeapon, peak_e_field_vm  # noqa: E402
from goldeneye.kill_radius import (  # noqa: E402
    VULNERABILITY_CLASSES,
    altitude_sweep,
    damage_probability_vs_field,
    kill_area_fraction,
    kill_radius_km,
)
from goldeneye.scenario import ARKANGEL, ArkangelScenario  # noqa: E402

__all__ = ["plot_emp_footprint"]


def _field_profile(altitudes_km: tuple[float, ...], yield_kt: float) -> tuple[np.ndarray, list[np.ndarray]]:
    """Radial field profiles (V/m) over ground range for each burst altitude."""
    ranges = np.linspace(0.0, 3000.0, 1200)
    profiles: list[np.ndarray] = []
    for alt in altitudes_km:
        profiles.append(np.array([peak_e_field_vm(float(r), alt, yield_kt) for r in ranges]))
    return ranges, profiles


def plot_emp_footprint(
    path: str | Path,
    scenario: ArkangelScenario = ARKANGEL,
) -> Path:
    """Render the 2x2 EMP / kill-radius figure to ``path`` (PNG)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    yield_kt = scenario.weapon.yield_kt
    weapon = scenario.weapon

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Orbital EMP threat envelope — GoldenEye: ARKANGEL", fontsize=13)

    # (1) radial field profiles + class thresholds
    ax = axes[0, 0]
    ranges, profiles = _field_profile((100.0, 300.0, 600.0), yield_kt)
    for alt, profile in zip((100.0, 300.0, 600.0), profiles, strict=True):
        ax.plot(ranges / 1000.0, profile, label=f"h = {alt:g} km")
    for cls in VULNERABILITY_CLASSES:
        ax.axhline(cls.damage_threshold_vm, color="grey", ls=":", lw=0.8, label=cls.name)
    ax.set_yscale("log")
    ax.set_ylim(10.0, 2.0e5)
    ax.set_xlabel("Ground range (10^3 km)")
    ax.set_ylabel("E1 peak (V/m)")
    ax.set_title("Radial E1 field envelope")
    ax.legend(fontsize=6, loc="upper right")

    # (2) kill radius vs burst altitude per class
    ax = axes[0, 1]
    altitudes = tuple(np.logspace(1.0, 3.0, 40))  # 10..1000 km
    sweep = altitude_sweep(altitudes, yield_kt)
    for cls in VULNERABILITY_CLASSES:
        radii = [row[cls.name] for row in sweep]
        ax.semilogx(altitudes, radii, label=cls.name, marker=".", ms=3)
    ax.set_xlabel("Burst altitude (km)")
    ax.set_ylabel("Kill radius (km)")
    ax.set_title("Kill radius vs burst altitude")
    ax.legend(fontsize=7)

    # (3) damage probability vs field per class
    ax = axes[1, 0]
    fields = np.logspace(1.0, 6.0, 300)
    for cls in VULNERABILITY_CLASSES:
        probs = [damage_probability_vs_field(f, cls) for f in fields]
        ax.semilogx(fields, probs, label=cls.name)
    ax.set_xlabel("E1 field (V/m)")
    ax.set_ylabel("P(damage)")
    ax.set_title("Damage probability curves")
    ax.legend(fontsize=7)

    # (4) kill-area fraction vs yield at the scenario altitude
    ax = axes[1, 1]
    yields_kt = tuple(np.logspace(0.5, 3.5, 40))  # ~3..3000 kt
    for cls in VULNERABILITY_CLASSES:
        fracs = [
            kill_area_fraction(
                kill_radius_km(EmpWeapon(y, weapon.burst_altitude_km), cls),
                weapon.burst_altitude_km,
            )
            for y in yields_kt
        ]
        ax.semilogx(yields_kt, fracs, label=cls.name, marker=".", ms=3)
    ax.set_xlabel("Weapon yield (kt)")
    ax.set_ylabel("Kill-area fraction of footprint")
    ax.set_title("Footprint coverage vs yield")
    ax.legend(fontsize=7)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
