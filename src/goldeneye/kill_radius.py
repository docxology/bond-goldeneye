"""Electronics kill-radius analysis by vulnerability class.

Given the ground-level E1 field envelope from :mod:`goldeneye.emp_model`, this
module computes, for each electronics vulnerability class, the radius within
which the field meets or exceeds the class's damage threshold (a deterministic
bisection root-find), the enclosed kill area, and a smooth damage-probability
curve.

Vulnerability classes map to documented electronics hardness bands used in
EMP/HEMP hardening assessments (MIL-STD-188-125 fixes E1 hardness at 50 kV/m
for fixed facilities; academic and engineering references place the damage
threshold of unprotected modern microelectronics in the range of ~100 V/m
(upset) to ~1 kV/m (damage), with legacy vacuum-tube / relay electronics far
harder). Thresholds are engineering references, not guarantees.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from goldeneye.emp_model import (
    EmpWeapon,
    ground_range_to_horizon_km,
    peak_e_field_at_nadir_vm,
    peak_e_field_vm,
)

__all__ = [
    "CLASS_INDEX",
    "DAMAGE_LOGISTIC_STEEPNESS",
    "VULNERABILITY_CLASSES",
    "VulnerabilityClass",
    "altitude_sweep",
    "damage_probability_vs_field",
    "footprint_sweep",
    "kill_area_fraction",
    "kill_area_km2",
    "kill_radius_km",
    "kill_table_for_class",
    "lookup_class",
]

#: Width of the damage-probability logistic transition (dimensionless).
DAMAGE_LOGISTIC_STEEPNESS = 6.0

#: Bisection iterations -> deterministic precision (~1e-9 of the bracket).
_BISECTION_ITERATIONS = 60


@dataclass(frozen=True)
class VulnerabilityClass:
    """An electronics vulnerability class: name, labels, and field thresholds.

    Attributes:
        name: Machine-readable slug (e.g. ``"unprotected"``).
        label: Human-readable label.
        upset_threshold_vm: Field level (V/m) at which degraded operation begins.
        damage_threshold_vm: Field level (V/m) at which damage is expected.
        description: Short sourcing note for the thresholds.
    """

    name: str
    label: str
    upset_threshold_vm: float
    damage_threshold_vm: float
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("VulnerabilityClass.name must be non-empty")
        if not (0 < self.upset_threshold_vm < self.damage_threshold_vm):
            raise ValueError(
                f"VulnerabilityClass needs 0 < upset < damage, got {self.upset_threshold_vm}/{self.damage_threshold_vm}"
            )


#: Canonical electronics vulnerability classes for the ARKANGEL analysis.
VULNERABILITY_CLASSES: tuple[VulnerabilityClass, ...] = (
    VulnerabilityClass(
        name="unprotected",
        label="Unprotected microelectronics (CMOS/SoC)",
        upset_threshold_vm=100.0,
        damage_threshold_vm=1000.0,
        description="unshielded modern digital electronics; damage from ~1 kV/m",
    ),
    VulnerabilityClass(
        name="commercial",
        label="Commercial / semi-hardened",
        upset_threshold_vm=1000.0,
        damage_threshold_vm=10000.0,
        description="filtered / lightly shielded industrial electronics",
    ),
    VulnerabilityClass(
        name="military",
        label="MIL-STD-188-125 hardened",
        upset_threshold_vm=20000.0,
        damage_threshold_vm=50000.0,
        description="hardened fixed facilities rated for 50 kV/m E1",
    ),
    VulnerabilityClass(
        name="legacy_tube",
        label="Legacy vacuum-tube / relay",
        upset_threshold_vm=300000.0,
        damage_threshold_vm=1000000.0,
        description="pre-semiconductor discrete electronics, highly immune",
    ),
)

#: Fast name -> class lookup.
CLASS_INDEX: dict[str, VulnerabilityClass] = {c.name: c for c in VULNERABILITY_CLASSES}


def lookup_class(name: str) -> VulnerabilityClass:
    """Return the vulnerability class by ``name`` or raise ``KeyError``."""
    try:
        return CLASS_INDEX[name]
    except KeyError:
        raise KeyError(f"unknown vulnerability class {name!r}; expected one of {', '.join(CLASS_INDEX)}") from None


def kill_area_km2(radius_km: float) -> float:
    """Area (km^2) enclosed by a kill radius: ``pi*r^2``."""
    return math.pi * float(radius_km) ** 2


def kill_area_fraction(radius_km: float, burst_altitude_km: float) -> float:
    """Fraction of the horizon-limited footprint covered by the kill radius."""
    horizon = ground_range_to_horizon_km(burst_altitude_km)
    if horizon <= 0:
        return 0.0
    return min(1.0, (float(radius_km) / horizon) ** 2)


def kill_radius_km(
    weapon: EmpWeapon,
    vulnerability_class: VulnerabilityClass | str,
    *,
    horizon_cap: bool = True,
) -> float:
    """Kill radius (km): ground range within which E1 meets/exceeds the class
    damage threshold.

    Deterministic bisection over the monotone-decreasing field envelope.
    Returns ``0.0`` when the nadir field never reaches the threshold, and the
    horizon range when the footprint is saturated (``horizon_cap=True``).
    """
    cls = (
        vulnerability_class
        if isinstance(vulnerability_class, VulnerabilityClass)
        else lookup_class(vulnerability_class)
    )
    threshold = cls.damage_threshold_vm
    if peak_e_field_at_nadir_vm(weapon.burst_altitude_km, weapon.yield_kt) < threshold:
        return 0.0

    horizon = ground_range_to_horizon_km(weapon.burst_altitude_km)
    if horizon_cap and peak_e_field_vm(horizon, weapon.burst_altitude_km, weapon.yield_kt) >= threshold:
        return horizon

    # Upper bound: at least the horizon (or, uncapped, a large multiple of the
    # analytic point-source radius where the field drops to the threshold).
    if horizon_cap:
        r_hi = horizon
    else:
        # E ~ E0*(h/r)^2 far out; threshold reached near r ~ h*sqrt(E0/T).
        r_hi = (
            weapon.burst_altitude_km
            * math.sqrt(max(peak_e_field_at_nadir_vm(weapon.burst_altitude_km, weapon.yield_kt) / threshold, 1.0))
            * 1.5
        )
        r_hi = max(r_hi, 1.0)

    lo, hi = 0.0, r_hi
    for _ in range(_BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        if peak_e_field_vm(mid, weapon.burst_altitude_km, weapon.yield_kt) >= threshold:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _class(entry: VulnerabilityClass | str) -> VulnerabilityClass:
    if isinstance(entry, VulnerabilityClass):
        return entry
    return lookup_class(entry)


def kill_table_for_class(
    weapon: EmpWeapon,
    vulnerability_class: VulnerabilityClass | str,
) -> dict[str, float | str]:
    """Single-class kill summary: radius, area, and footprint fraction."""
    cls = _class(vulnerability_class)
    radius = kill_radius_km(weapon, cls)
    return {
        "name": cls.name,
        "radius_km": radius,
        "area_km2": kill_area_km2(radius),
        "footprint_fraction": kill_area_fraction(radius, weapon.burst_altitude_km),
    }


def footprint_sweep(
    weapon: EmpWeapon,
    classes: tuple[VulnerabilityClass | str, ...] = VULNERABILITY_CLASSES,
) -> tuple[dict[str, float | str], ...]:
    """Kill summary for every class against one weapon."""
    return tuple(kill_table_for_class(weapon, cls) for cls in classes)


def damage_probability_vs_field(
    field_vm: float,
    vulnerability_class: VulnerabilityClass | str,
    *,
    steepness: float = DAMAGE_LOGISTIC_STEEPNESS,
) -> float:
    """Smooth probability of damage at a given E1 field (logistic on E/T).

    ``P = 1 / (1 + exp(-steepness*(E/T - 1)))``, so ``P = 0.5`` exactly at the
    damage threshold and P -> 1 / P -> 0 on either side.
    """
    cls = _class(vulnerability_class)
    if field_vm < 0:
        raise ValueError(f"field_vm must be >= 0, got {field_vm!r}")
    ratio = float(field_vm) / cls.damage_threshold_vm
    return 1.0 / (1.0 + math.exp(-steepness * (ratio - 1.0)))


def altitude_sweep(
    altitudes_km: tuple[float, ...],
    yield_kt: float,
    classes: tuple[VulnerabilityClass | str, ...] = VULNERABILITY_CLASSES,
) -> tuple[dict[str, float | str], ...]:
    """Kill radius per class across a grid of burst altitudes (radius in km)."""
    rows: list[dict[str, float | str]] = []
    for alt in altitudes_km:
        weapon = EmpWeapon(yield_kt=yield_kt, burst_altitude_km=alt)
        row: dict[str, float | str] = {"burst_altitude_km": alt}
        for cls_entry in classes:
            cls = _class(cls_entry)
            row[cls.name] = kill_radius_km(weapon, cls)
        rows.append(row)
    return tuple(rows)
