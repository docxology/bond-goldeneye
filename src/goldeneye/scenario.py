"""ARKANGEL scenario — composition of the three deep-core concept modules.

This module binds :mod:`goldeneye.emp_model`, :mod:`goldeneye.kill_radius`,
and :mod:`goldeneye.dam_security` into the canonical *GoldenEye* (1995)
ARKANGEL mission scenario: a high-altitude EMP weapon, an electronics
kill-radius assessment, and the Arkangel dam-facility security / flood-risk
analysis. It exposes:

* :data:`ARKANGEL`, the deterministic default scenario;
* :func:`load_scenario_config`, which overlays ``manuscript/config.yaml``;
* :func:`analyze_arkangel`, the deterministic analysis dictionary that feeds
  the mission ``execute`` stage, the manuscript variables, and the figures;
* :func:`input_hash`, a canonical SHA-256 of the scenario inputs for
  provenance auditing.

Like the three concept modules, this module is infrastructure-free: it can be
imported without bond-api or any other BOND layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from goldeneye import dam_security
from goldeneye.dam_security import Reservoir, SecurityLayer
from goldeneye.emp_model import EmpWeapon, ground_range_to_horizon_km, peak_e_field_at_nadir_vm
from goldeneye.kill_radius import (
    VULNERABILITY_CLASSES,
    kill_area_fraction,
    kill_area_km2,
    kill_radius_km,
    lookup_class,
)

__all__ = [
    "ARKANGEL",
    "ArkangelScenario",
    "analyze_arkangel",
    "input_hash",
    "load_scenario_config",
    "scenario_input_dict",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"


@dataclass(frozen=True)
class ArkangelScenario:
    """Canonical ARKANGEL mission scenario parameters.

    Attributes:
        weapon: The orbital EMP weapon (yield, burst altitude).
        reservoir: The Arkangel dam reservoir (volume, head).
        facility_distance_km: Downstream distance of the facility from the dam.
        facility_elevation_m: Facility ground elevation above the riverbed.
        access_layers: Defense-in-depth access-control cascade.
        name: Scenario identifier.
        codename: Mission codename (ARKANGEL).
    """

    weapon: EmpWeapon
    reservoir: Reservoir
    facility_distance_km: float
    facility_elevation_m: float
    access_layers: tuple[SecurityLayer, ...] = field(default_factory=lambda: dam_security.DEFAULT_ACCESS_LAYERS)
    name: str = "arkangel"
    codename: str = "ARKANGEL"

    def __post_init__(self) -> None:
        if self.facility_distance_km <= 0:
            raise ValueError(f"facility_distance_km must be > 0, got {self.facility_distance_km!r}")
        if self.facility_elevation_m <= 0:
            raise ValueError(f"facility_elevation_m must be > 0, got {self.facility_elevation_m!r}")


#: Default ARKANGEL scenario: a 2 Mt burst at 300 km orbital altitude, an
#: Arkangel-class reservoir, and the default access cascade.
ARKANGEL = ArkangelScenario(
    weapon=EmpWeapon(yield_kt=2000.0, burst_altitude_km=300.0),
    reservoir=Reservoir(name="arkangel", volume_m3=1.3e8, head_m=75.0),
    facility_distance_km=8.0,
    facility_elevation_m=10.0,
)


def scenario_input_dict(scenario: ArkangelScenario = ARKANGEL) -> dict[str, Any]:
    """Flat, JSON-serializable representation of the scenario inputs."""
    return {
        "name": scenario.name,
        "codename": scenario.codename,
        "weapon_yield_kt": scenario.weapon.yield_kt,
        "burst_altitude_km": scenario.weapon.burst_altitude_km,
        "reservoir_volume_m3": scenario.reservoir.volume_m3,
        "reservoir_head_m": scenario.reservoir.head_m,
        "facility_distance_km": scenario.facility_distance_km,
        "facility_elevation_m": scenario.facility_elevation_m,
        "access_layers": [
            {
                "name": layer.name,
                "detection_probability": layer.detection_probability,
                "response_time_min": layer.response_time_min,
            }
            for layer in scenario.access_layers
        ],
    }


def input_hash(scenario: ArkangelScenario = ARKANGEL) -> str:
    """Canonical SHA-256 of the scenario inputs (sorted, compact JSON)."""
    payload = json.dumps(scenario_input_dict(scenario), sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scenario_from_config(data: dict[str, Any], base: ArkangelScenario = ARKANGEL) -> ArkangelScenario:
    """Build a scenario from a ``manuscript/config.yaml`` ``scenario`` block."""
    block = data.get("scenario", {})
    if not isinstance(block, dict):
        raise ValueError("manuscript config 'scenario' section must be a mapping")

    weapon_cfg = block.get("weapon", {})
    reservoir_cfg = block.get("reservoir", {})
    facility = block.get("facility", {})
    access = block.get("access", {})

    weapon = EmpWeapon(
        yield_kt=float(weapon_cfg.get("yield_kt", base.weapon.yield_kt)),
        burst_altitude_km=float(weapon_cfg.get("burst_altitude_km", base.weapon.burst_altitude_km)),
    )
    reservoir = Reservoir(
        name=str(reservoir_cfg.get("name", base.reservoir.name)),
        volume_m3=float(reservoir_cfg.get("volume_m3", base.reservoir.volume_m3)),
        head_m=float(reservoir_cfg.get("head_m", base.reservoir.head_m)),
    )
    layers: tuple[SecurityLayer, ...]
    layer_list = access.get("layers", ())
    if layer_list:
        built: list[SecurityLayer] = []
        for entry in layer_list:
            if not isinstance(entry, dict):
                raise ValueError("each access layer must be a mapping")
            built.append(
                SecurityLayer(
                    name=str(entry["name"]),
                    detection_probability=float(entry["detection_probability"]),
                    response_time_min=float(entry["response_time_min"]),
                    barrier=str(entry.get("barrier", "")),
                )
            )
        layers = tuple(built)
    else:
        layers = base.access_layers

    return ArkangelScenario(
        weapon=weapon,
        reservoir=reservoir,
        facility_distance_km=float(facility.get("distance_km", base.facility_distance_km)),
        facility_elevation_m=float(facility.get("elevation_m", base.facility_elevation_m)),
        access_layers=layers,
        name=str(block.get("name", base.name)),
        codename=str(block.get("codename", base.codename)),
    )


def load_scenario_config(config_path: str | Path | None = None) -> ArkangelScenario:
    """Load the scenario from ``manuscript/config.yaml`` (or an explicit path).

    Values absent from the file fall back to :data:`ARKANGEL` defaults.
    """
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return _scenario_from_config(data)


def analyze_arkangel(scenario: ArkangelScenario = ARKANGEL) -> dict[str, Any]:
    """Run the full deterministic ARKANGEL analysis.

    Returns a JSON-serializable dictionary (floats, ints, strings, tuples)
    with the EMP threat envelope, per-class kill radius table, and the dam
    security / flood-risk results. This dictionary feeds the mission execute
    stage, the manuscript variables, and the figures.
    """
    weapon = scenario.weapon
    reservoir = scenario.reservoir

    horizon_km = ground_range_to_horizon_km(weapon.burst_altitude_km)
    nadir_vm = peak_e_field_at_nadir_vm(weapon.burst_altitude_km, weapon.yield_kt)

    kill_table = tuple(
        {
            "name": cls.name,
            "label": cls.label,
            "damage_threshold_vm": cls.damage_threshold_vm,
            "radius_km": kill_radius_km(weapon, cls),
        }
        for cls in VULNERABILITY_CLASSES
    )

    peak_q = dam_security.breach_peak_discharge_cms(reservoir.volume_m3, reservoir.head_m)
    front_speed = dam_security.ritter_front_speed_ms(reservoir.head_m)
    distance_m = scenario.facility_distance_km * 1000.0
    arrival_s = dam_security.flood_arrival_time_s(distance_m, reservoir.head_m)
    peak_depth = dam_security.peak_depth_at_distance_m(distance_m, reservoir.head_m)
    risk = dam_security.flood_risk_rating(peak_depth, scenario.facility_elevation_m)
    severity = dam_security.severity_ratio(peak_depth, scenario.facility_elevation_m)

    p_detect = dam_security.cumulative_detection_probability(scenario.access_layers)
    expected_time = dam_security.expected_detection_time_min(scenario.access_layers)
    score = dam_security.security_score(scenario.access_layers)

    return {
        "name": scenario.name,
        "codename": scenario.codename,
        "input_hash": input_hash(scenario),
        "emp": {
            "yield_kt": weapon.yield_kt,
            "burst_altitude_km": weapon.burst_altitude_km,
            "nadir_field_vm": nadir_vm,
            "horizon_range_km": horizon_km,
            "horizon_area_km2": kill_area_km2(horizon_km),
            "energy_density_nadir_jm3": 0.5 * 8.8541878128e-12 * nadir_vm**2,
        },
        "kill_radius": kill_table,
        "dam": {
            "reservoir_name": reservoir.name,
            "volume_m3": reservoir.volume_m3,
            "head_m": reservoir.head_m,
            "peak_discharge_cms": peak_q,
            "front_speed_ms": front_speed,
        },
        "flood": {
            "facility_distance_km": scenario.facility_distance_km,
            "facility_elevation_m": scenario.facility_elevation_m,
            "arrival_time_s": arrival_s,
            "arrival_time_min": arrival_s / 60.0,
            "peak_depth_m": peak_depth,
            "severity_ratio": severity,
            "risk_rating": risk,
        },
        "access": {
            "num_layers": len(scenario.access_layers),
            "detection_probability": p_detect,
            "expected_detection_time_min": expected_time,
            "security_score": score,
            "kill_area_fraction_unprotected": kill_area_fraction(
                kill_radius_km(weapon, lookup_class("unprotected")), weapon.burst_altitude_km
            ),
        },
    }
