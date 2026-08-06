"""ARKANGEL scenario — composition of the deep-core concept modules.

This module binds the seven domain modules — :mod:`goldeneye.emp_model`,
:mod:`goldeneye.kill_radius`, :mod:`goldeneye.dam_security`,
:mod:`goldeneye.orbital_mechanics`, :mod:`goldeneye.coupling`,
:mod:`goldeneye.grid_resilience`, :mod:`goldeneye.breach_hydrograph` — into the
canonical *GoldenEye* (1995) ARKANGEL mission scenario: an orbital EMP weapon,
its ground effects and electronics kill radii, the coupling/shielding of
sensitive infrastructure, the resilience of the regional power network, and
the Arkangel dam-facility security and breach-flood analysis. It exposes:

* :data:`ARKANGEL`, the deterministic default scenario (including the canonical
  regional power grid and downstream inundation stations);
* :func:`load_scenario_config`, which overlays ``manuscript/config.yaml``;
* :func:`analyze_arkangel`, the deterministic analysis dictionary that feeds
  the mission ``execute`` stage, the manuscript variables, and the figures;
* :func:`input_hash`, a canonical SHA-256 of the scenario inputs for
  provenance auditing.

Like the concept modules, this module is infrastructure-free: it can be
imported without bond-api or any other BOND layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from goldeneye import breach_hydrograph, dam_security
from goldeneye.breach_hydrograph import Station
from goldeneye import coupling as coupling_module
from goldeneye.dam_security import Reservoir, SecurityLayer
from goldeneye.emp_model import (
    EmpWeapon,
    energy_density_jm3,
    ground_range_to_horizon_km,
    peak_e_field_at_nadir_vm,
)
from goldeneye.grid_resilience import GridLine, GridNode, PowerGrid, resilience_report, node_field_vm
from goldeneye.kill_radius import (
    VULNERABILITY_CLASSES,
    kill_area_fraction,
    kill_area_km2,
    kill_radius_km,
    lookup_class,
)
from goldeneye.orbital_mechanics import (
    OrbitGeometry,
    central_angle_deg,
    circular_orbit_period_s,
    circular_orbit_speed_ms,
    elevation_angle_deg,
    is_visible,
    orbital_radius_m,
    overhead_pass_duration_s,
    slant_range_m,
)

__all__ = [
    "ARKANGEL",
    "ArkangelScenario",
    "CouplingParams",
    "analyze_arkangel",
    "input_hash",
    "load_scenario_config",
    "scenario_input_dict",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

#: Military (MIL-STD-188-125) E1 withstand level used for the coupling margin.
MILITARY_WITHSTAND_VM = 50000.0


@dataclass(frozen=True)
class CouplingParams:
    """EM coupling / shielding assessment inputs for a conductor at the facility.

    Attributes:
        conductor_length_m: Length of the exposed conductor feeding electronics.
        shield_material: Material name from ``coupling.MATERIALS``.
        shield_thickness_mm: Enclosure wall thickness (mm).
        e1_frequency_hz: Representative E1 spectral frequency for skin-depth and
            shielding analysis.
        impedance_ohm: Load impedance (ohm) for the conducted-current estimate.
    """

    conductor_length_m: float
    shield_material: str
    shield_thickness_mm: float
    e1_frequency_hz: float
    impedance_ohm: float

    def __post_init__(self) -> None:
        if self.conductor_length_m <= 0:
            raise ValueError(f"conductor_length_m must be > 0, got {self.conductor_length_m!r}")
        coupling_module.lookup_material(self.shield_material)  # raises KeyError
        if self.shield_thickness_mm <= 0:
            raise ValueError(f"shield_thickness_mm must be > 0, got {self.shield_thickness_mm!r}")
        if self.e1_frequency_hz <= 0:
            raise ValueError(f"e1_frequency_hz must be > 0, got {self.e1_frequency_hz!r}")
        if self.impedance_ohm <= 0:
            raise ValueError(f"impedance_ohm must be > 0, got {self.impedance_ohm!r}")


@dataclass(frozen=True)
class ArkangelScenario:
    """Canonical ARKANGEL mission scenario parameters.

    Attributes:
        weapon: The orbital EMP weapon (yield, burst altitude).
        reservoir: The Arkangel dam reservoir (volume, head).
        facility_distance_km: Downstream distance of the facility from the dam.
        facility_elevation_m: Facility ground elevation above the riverbed.
        access_layers: Defense-in-depth access-control cascade.
        orbit: The orbital platform / target geometry.
        coupling: Conductor coupling and shielding inputs.
        grid: The regional power-network model (nadir at its origin).
        stations: Downstream inundation stations for the breach hydrograph.
        name: Scenario identifier.
        codename: Mission codename (ARKANGEL).
    """

    weapon: EmpWeapon
    reservoir: Reservoir
    facility_distance_km: float
    facility_elevation_m: float
    access_layers: tuple[SecurityLayer, ...] = field(default_factory=lambda: dam_security.DEFAULT_ACCESS_LAYERS)
    orbit: OrbitGeometry = field(default_factory=lambda: OrbitGeometry(300.0, 60.0, 108.0, 53.5, 108.0, 10.0))
    coupling: CouplingParams = field(default_factory=lambda: CouplingParams(10.0, "aluminum", 0.1, 1.0e8, 50.0))
    grid: PowerGrid = field(default_factory=lambda: _canonical_grid())
    stations: tuple[Station, ...] = field(
        default_factory=lambda: (
            Station("facility", 8.0, 10.0),
            Station("town", 12.0, 8.0),
            Station("bridge", 20.0, 6.0),
        )
    )
    name: str = "arkangel"
    codename: str = "ARKANGEL"

    def __post_init__(self) -> None:
        if self.facility_distance_km <= 0:
            raise ValueError(f"facility_distance_km must be > 0, got {self.facility_distance_km!r}")
        if self.facility_elevation_m <= 0:
            raise ValueError(f"facility_elevation_m must be > 0, got {self.facility_elevation_m!r}")


def _canonical_grid() -> PowerGrid:
    """The canonical Severnaya-area power network (nadir at the origin).

    Nodes lie 700-900 km from the burst nadir so the E1 envelope spans a real
    gradient: military assets largely survive, unprotected assets are
    destroyed, and commercial assets are marginal.
    """
    nodes = (
        GridNode("hydro_plant", 0.0, 850.0, 0.0, False, "military"),
        GridNode("facility_sub", 40.0, 820.0, 12.0, True, "commercial"),
        GridNode("town_a", -60.0, 880.0, 5.0, True, "unprotected"),
        GridNode("relay", -30.0, 800.0, 0.0, False, "unprotected"),
        GridNode("grid_tie", 90.0, 790.0, 0.0, False, "commercial"),
    )
    lines = (
        GridLine("hydro_relay", "hydro_plant", "relay", "unprotected"),
        GridLine("hydro_facility", "hydro_plant", "facility_sub", "military"),
        GridLine("hydro_gridtie", "hydro_plant", "grid_tie", "military"),
        GridLine("relay_town", "relay", "town_a", "unprotected"),
        GridLine("facility_town", "facility_sub", "town_a", "commercial"),
        GridLine("facility_gridtie", "facility_sub", "grid_tie", "military"),
    )
    return PowerGrid(nodes, lines, source="hydro_plant")


#: Default ARKANGEL scenario: a 2 Mt burst at 300 km orbital altitude, an
#: Arkangel-class reservoir, the default access cascade, the canonical grid,
#: and the three downstream stations.
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
        "orbit": {
            "altitude_km": scenario.orbit.altitude_km,
            "nadir_lat_deg": scenario.orbit.nadir_lat_deg,
            "nadir_lon_deg": scenario.orbit.nadir_lon_deg,
            "target_lat_deg": scenario.orbit.target_lat_deg,
            "target_lon_deg": scenario.orbit.target_lon_deg,
            "min_elevation_deg": scenario.orbit.min_elevation_deg,
        },
        "coupling": {
            "conductor_length_m": scenario.coupling.conductor_length_m,
            "shield_material": scenario.coupling.shield_material,
            "shield_thickness_mm": scenario.coupling.shield_thickness_mm,
            "e1_frequency_hz": scenario.coupling.e1_frequency_hz,
            "impedance_ohm": scenario.coupling.impedance_ohm,
        },
        "grid_nodes": [
            {
                "name": node.name,
                "x_km": node.x_km,
                "y_km": node.y_km,
                "load_mw": node.load_mw,
                "critical": node.critical,
                "class": node.vulnerability_class,
            }
            for node in scenario.grid.nodes
        ],
        "grid_lines": [
            {"name": line.name, "a": line.node_a, "b": line.node_b, "class": line.vulnerability_class}
            for line in scenario.grid.lines
        ],
        "grid_source": scenario.grid.source,
        "stations": [
            {"name": s.name, "distance_km": s.distance_km, "elevation_m": s.elevation_m} for s in scenario.stations
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
    orbit_cfg = block.get("orbit", {})
    coupling_cfg = block.get("coupling", {})

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

    orbit = OrbitGeometry(
        altitude_km=float(orbit_cfg.get("altitude_km", base.orbit.altitude_km)),
        nadir_lat_deg=float(orbit_cfg.get("nadir_lat_deg", base.orbit.nadir_lat_deg)),
        nadir_lon_deg=float(orbit_cfg.get("nadir_lon_deg", base.orbit.nadir_lon_deg)),
        target_lat_deg=float(orbit_cfg.get("target_lat_deg", base.orbit.target_lat_deg)),
        target_lon_deg=float(orbit_cfg.get("target_lon_deg", base.orbit.target_lon_deg)),
        min_elevation_deg=float(orbit_cfg.get("min_elevation_deg", base.orbit.min_elevation_deg)),
    )
    coupling = CouplingParams(
        conductor_length_m=float(coupling_cfg.get("conductor_length_m", base.coupling.conductor_length_m)),
        shield_material=str(coupling_cfg.get("shield_material", base.coupling.shield_material)),
        shield_thickness_mm=float(coupling_cfg.get("shield_thickness_mm", base.coupling.shield_thickness_mm)),
        e1_frequency_hz=float(coupling_cfg.get("e1_frequency_hz", base.coupling.e1_frequency_hz)),
        impedance_ohm=float(coupling_cfg.get("impedance_ohm", base.coupling.impedance_ohm)),
    )

    return ArkangelScenario(
        weapon=weapon,
        reservoir=reservoir,
        facility_distance_km=float(facility.get("distance_km", base.facility_distance_km)),
        facility_elevation_m=float(facility.get("elevation_m", base.facility_elevation_m)),
        access_layers=layers,
        orbit=orbit,
        coupling=coupling,
        grid=base.grid,
        stations=base.stations,
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


def _orbit_section(orbit: OrbitGeometry) -> dict[str, Any]:
    """Orbital-platform geometry metrics (deterministic)."""
    altitude_m = orbit.altitude_km * 1000.0
    radius = orbital_radius_m(altitude_m)
    period = circular_orbit_period_s(radius)
    speed = circular_orbit_speed_ms(radius)
    # Observer is the target; sub-platform point is the nadir.
    gamma = central_angle_deg(orbit.target_lat_deg, orbit.target_lon_deg, orbit.nadir_lat_deg, orbit.nadir_lon_deg)
    elevation = elevation_angle_deg(
        orbit.target_lat_deg, orbit.target_lon_deg, orbit.nadir_lat_deg, orbit.nadir_lon_deg, altitude_m
    )
    slant = slant_range_m(
        orbit.target_lat_deg, orbit.target_lon_deg, orbit.nadir_lat_deg, orbit.nadir_lon_deg, altitude_m
    )
    visible = is_visible(
        orbit.target_lat_deg,
        orbit.target_lon_deg,
        orbit.nadir_lat_deg,
        orbit.nadir_lon_deg,
        altitude_m,
        orbit.min_elevation_deg,
    )
    pass_duration = overhead_pass_duration_s(altitude_m, orbit.min_elevation_deg)
    return {
        "altitude_km": orbit.altitude_km,
        "radius_km": radius / 1000.0,
        "min_elevation_deg": orbit.min_elevation_deg,
        "nadir_lat_deg": orbit.nadir_lat_deg,
        "nadir_lon_deg": orbit.nadir_lon_deg,
        "target_lat_deg": orbit.target_lat_deg,
        "target_lon_deg": orbit.target_lon_deg,
        "period_min": period / 60.0,
        "speed_kms": speed / 1000.0,
        "central_angle_deg": gamma,
        "elevation_angle_deg": elevation,
        "slant_range_km": slant / 1000.0,
        "visible": visible,
        "pass_duration_min": pass_duration / 60.0,
    }


def _coupling_section(
    scenario: ArkangelScenario,
    facility_field_vm: float,
    elevation_deg: float,
) -> dict[str, Any]:
    """Conductor coupling and shielding metrics at the facility."""
    cp = scenario.coupling
    h_eff = coupling_module.effective_height_m(cp.conductor_length_m, elevation_deg)
    induced = coupling_module.induced_voltage_v(facility_field_vm, h_eff)
    rho, mu_r = coupling_module.lookup_material(cp.shield_material)
    thickness_m = cp.shield_thickness_mm / 1000.0
    delta = coupling_module.skin_depth_m(cp.e1_frequency_hz, rho, mu_r)
    absorption = coupling_module.plane_wave_absorption_db(thickness_m, delta)
    reflection = coupling_module.plane_wave_reflection_db(cp.e1_frequency_hz, rho, mu_r)
    se = coupling_module.schelkunoff_se_db(thickness_m, cp.e1_frequency_hz, rho, mu_r)
    shielded = coupling_module.shielded_field_vm(facility_field_vm, se)
    margin = coupling_module.protection_margin_db(MILITARY_WITHSTAND_VM, facility_field_vm)
    conducted = coupling_module.conducted_current_a(induced, cp.impedance_ohm)
    return {
        "facility_field_vm": facility_field_vm,
        "elevation_angle_deg": elevation_deg,
        "conductor_length_m": cp.conductor_length_m,
        "shield_material": cp.shield_material,
        "shield_thickness_mm": cp.shield_thickness_mm,
        "frequency_mhz": cp.e1_frequency_hz / 1.0e6,
        "impedance_ohm": cp.impedance_ohm,
        "military_withstand_vm": MILITARY_WITHSTAND_VM,
        "effective_height_m": h_eff,
        "induced_voltage_v": induced,
        "skin_depth_mm": delta * 1000.0,
        "absorption_db": absorption,
        "reflection_db": reflection,
        "se_db": se,
        "shielded_field_vm": shielded,
        "protection_margin_db_military": margin,
        "conducted_current_a": conducted,
    }


def analyze_arkangel(scenario: ArkangelScenario = ARKANGEL) -> dict[str, Any]:
    """Run the full deterministic ARKANGEL analysis.

    Returns a JSON-serializable dictionary (floats, ints, strings, tuples)
    with the EMP threat envelope, per-class kill radii, coupling/shielding,
    grid resilience, the dam security / breach-flood results, the orbital
    platform geometry, and the breach hydrograph. This dictionary feeds the
    mission execute stage, the manuscript variables, and the figures.
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

    orbit = _orbit_section(scenario.orbit)
    grid_report = resilience_report(scenario.grid, weapon)
    facility_field_vm = node_field_vm(scenario.grid, weapon, "facility_sub")
    coupling = _coupling_section(scenario, facility_field_vm, orbit["elevation_angle_deg"])
    hydro = breach_hydrograph.breach_hydrograph_report(reservoir.volume_m3, reservoir.head_m, scenario.stations)

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
            "energy_density_nadir_jm3": energy_density_jm3(nadir_vm),
        },
        "kill_radius": kill_table,
        "orbit": orbit,
        "coupling": coupling,
        "grid": grid_report,
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
        "hydrograph": hydro,
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
