"""Manuscript variable hydration for GoldenEye: ARKANGEL.

Every ``{{TOKEN}}`` in ``manuscript/*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic ARKANGEL scenario analysis (:func:`goldeneye.scenario.analyze_arkangel`).
Metrics are never hand-authored in prose: they flow through this module so the
manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import math
import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from goldeneye import emp_model
from goldeneye.kill_radius import VULNERABILITY_CLASSES
from goldeneye.scenario import analyze_arkangel, load_scenario_config

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PACKAGE_ROOT",
    "generate_variables",
    "load_manuscript_config",
    "resolve_manuscript_tree",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def _fmt(value: float, ndigits: int = 1) -> str:
    """Format a float to ``ndigits`` decimals (strip trailing zeros)."""
    return f"{float(value):.{ndigits}f}"


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def _non_finite_tokens(variables: dict[str, str]) -> list[str]:
    """Token names whose value parses as a float but is NaN or infinite.

    Non-numeric values (titles, risk ratings, class-name lists) are skipped:
    only values that *claim* to be numbers are checked.
    """
    bad: list[str] = []
    for token, value in variables.items():
        try:
            number = float(value)
        except ValueError:
            continue
        if not math.isfinite(number):
            bad.append(token)
    return sorted(bad)


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), refuse to return a map in which
            any numeric token is NaN or infinite (the strict-mode check that
            keeps metrics real). Set False for draft renders.

    Raises:
        ValueError: In strict mode, when the analysis yields a non-finite
            numeric token.
        now: Deterministic timestamp override (used by tests).
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    scenario = load_scenario_config(config_path)
    analysis = analyze_arkangel(scenario)

    emp = analysis["emp"]
    dam = analysis["dam"]
    flood = analysis["flood"]
    access = analysis["access"]
    kill_table = analysis["kill_radius"]

    per_class_radius = {row["name"]: row["radius_km"] for row in kill_table}
    per_class_threshold = {row["name"]: row["damage_threshold_vm"] for row in kill_table}

    orbit = analysis["orbit"]
    coupling = analysis["coupling"]
    grid = analysis["grid"]
    hydro = analysis["hydrograph"]
    grid_per_load = {row["load"]: row for row in grid["per_load"]}
    stations = hydro["stations"]

    variables: dict[str, str] = {
        "GE_IDENTITY": "GOLDENEYE",
        "GE_CODENAME": str(analysis["codename"]),
        "GE_TITLE": str(paper.get("title", "")),
        "GE_SUBTITLE": str(paper.get("subtitle", "")),
        "GE_VERSION": str(paper.get("version", "")),
        # --- EMP model constants (module-level, auditable) ---
        "GE_E1_REFERENCE_VM": _fmt(emp_model.E1_REFERENCE_VM, 0),
        "GE_REFERENCE_YIELD_KT": _fmt(emp_model.REFERENCE_YIELD_KT, 0),
        "GE_GAMMA_FRACTION_PCT": _fmt(emp_model.GAMMA_YIELD_FRACTION * 100.0, 1),
        "GE_YIELD_EXPONENT": _fmt(emp_model.YIELD_SCALING_EXPONENT, 2),
        # --- EMP threat ---
        "GE_YIELD_KT": _fmt(emp["yield_kt"]),
        "GE_BURST_ALTITUDE_KM": _fmt(emp["burst_altitude_km"]),
        "GE_NADIR_FIELD_VM": _fmt(emp["nadir_field_vm"], 0),
        "GE_HORIZON_RANGE_KM": _fmt(emp["horizon_range_km"], 0),
        "GE_HORIZON_AREA_KM2": _fmt(emp["horizon_area_km2"], 0),
        # --- Vulnerability classes ---
        "GE_NUM_CLASSES": str(len(VULNERABILITY_CLASSES)),
        "GE_CLASS_NAMES": ", ".join(cls.name for cls in VULNERABILITY_CLASSES),
        "GE_RADIUS_UNPROTECTED_KM": _fmt(per_class_radius["unprotected"]),
        "GE_RADIUS_COMMERCIAL_KM": _fmt(per_class_radius["commercial"]),
        "GE_RADIUS_MILITARY_KM": _fmt(per_class_radius["military"]),
        "GE_RADIUS_LEGACY_TUBE_KM": _fmt(per_class_radius["legacy_tube"]),
        "GE_FRACTION_UNPROTECTED": _fmt(access["kill_area_fraction_unprotected"] * 100.0),
        "GE_THRESHOLD_UNPROTECTED_VM": _fmt(per_class_threshold["unprotected"], 0),
        "GE_THRESHOLD_COMMERCIAL_VM": _fmt(per_class_threshold["commercial"], 0),
        "GE_THRESHOLD_MILITARY_VM": _fmt(per_class_threshold["military"], 0),
        "GE_THRESHOLD_LEGACY_TUBE_VM": _fmt(per_class_threshold["legacy_tube"], 0),
        # --- Dam / flood ---
        "GE_RESERVOIR_VOLUME_M3": _fmt(dam["volume_m3"], 0),
        "GE_DAM_HEAD_M": _fmt(dam["head_m"]),
        "GE_PEAK_DISCHARGE_CMS": _fmt(dam["peak_discharge_cms"], 0),
        "GE_FRONT_SPEED_MS": _fmt(dam["front_speed_ms"]),
        "GE_FACILITY_DISTANCE_KM": _fmt(flood["facility_distance_km"]),
        "GE_FLOOD_ARRIVAL_MIN": _fmt(flood["arrival_time_min"]),
        "GE_FLOOD_DEPTH_M": _fmt(flood["peak_depth_m"]),
        "GE_FLOOD_SEVERITY": _fmt(flood["severity_ratio"], 3),
        "GE_FLOOD_RISK": str(flood["risk_rating"]),
        # --- Access control ---
        "GE_ACCESS_DETECT_PROB": _fmt(access["detection_probability"], 3),
        "GE_ACCESS_EXPECTED_TIME_MIN": _fmt(access["expected_detection_time_min"]),
        "GE_SECURITY_SCORE": _fmt(access["security_score"]),
        "GE_NUM_LAYERS": str(access["num_layers"]),
        # --- Orbital platform ---
        "GE_ORBIT_ALTITUDE_KM": _fmt(orbit["altitude_km"], 0),
        "GE_ORBIT_RADIUS_KM": _fmt(orbit["radius_km"], 0),
        "GE_ORBIT_MIN_ELEVATION_DEG": _fmt(orbit["min_elevation_deg"], 0),
        "GE_ORBIT_NADIR_LAT_DEG": _fmt(orbit["nadir_lat_deg"]),
        "GE_ORBIT_NADIR_LON_DEG": _fmt(orbit["nadir_lon_deg"]),
        "GE_ORBIT_TARGET_LAT_DEG": _fmt(orbit["target_lat_deg"]),
        "GE_ORBIT_PERIOD_MIN": _fmt(orbit["period_min"]),
        "GE_ORBIT_SPEED_KMS": _fmt(orbit["speed_kms"]),
        "GE_ORBIT_ELEVATION_DEG": _fmt(orbit["elevation_angle_deg"]),
        "GE_ORBIT_SLANT_RANGE_KM": _fmt(orbit["slant_range_km"]),
        "GE_ORBIT_CENTRAL_ANGLE_DEG": _fmt(orbit["central_angle_deg"]),
        "GE_ORBIT_PASS_DURATION_MIN": _fmt(orbit["pass_duration_min"]),
        # --- Coupling / shielding ---
        "GE_COUPLING_CONDUCTOR_LENGTH_M": _fmt(coupling["conductor_length_m"], 0),
        "GE_COUPLING_SHIELD_MATERIAL": str(coupling["shield_material"]),
        "GE_COUPLING_SHIELD_THICKNESS_MM": _fmt(coupling["shield_thickness_mm"], 2),
        "GE_COUPLING_FREQUENCY_MHZ": _fmt(coupling["frequency_mhz"], 0),
        "GE_COUPLING_IMPEDANCE_OHM": _fmt(coupling["impedance_ohm"], 0),
        "GE_MILITARY_WITHSTAND_VM": _fmt(coupling["military_withstand_vm"], 0),
        "GE_COUPLING_FACILITY_FIELD_VM": _fmt(coupling["facility_field_vm"], 0),
        "GE_COUPLING_EFFECTIVE_HEIGHT_M": _fmt(coupling["effective_height_m"]),
        "GE_COUPLING_INDUCED_V": _fmt(coupling["induced_voltage_v"], 0),
        "GE_COUPLING_SKIN_DEPTH_MM": _fmt(coupling["skin_depth_mm"], 3),
        "GE_COUPLING_SE_DB": _fmt(coupling["se_db"]),
        "GE_COUPLING_SHIELDED_FIELD_VM": _fmt(coupling["shielded_field_vm"], 2),
        "GE_COUPLING_MARGIN_DB": _fmt(coupling["protection_margin_db_military"]),
        "GE_COUPLING_CONDUCTED_A": _fmt(coupling["conducted_current_a"], 0),
        # --- Regional grid resilience ---
        "GE_GRID_NUM_NODES": str(grid["nodes"].__len__()),
        "GE_GRID_NUM_LINES": str(grid["lines"].__len__()),
        "GE_GRID_DOWN_NODES": ", ".join(grid["down_nodes"]),
        "GE_GRID_EXPECTED_SERVED_MW": _fmt(grid["expected_served_mw"]),
        "GE_GRID_TOTAL_CRITICAL_MW": _fmt(grid["total_critical_mw"]),
        "GE_GRID_SERVED_FRACTION": _fmt(grid["served_fraction"] * 100.0),
        "GE_GRID_MIN_RELIABILITY": _fmt(grid["min_reliability"], 3),
        "GE_GRID_MIN_DISJOINT_PATHS": str(grid["min_disjoint_paths"]),
        "GE_FACILITY_RELIABILITY": _fmt(grid_per_load["facility_sub"]["reliability"], 3),
        "GE_FACILITY_DISJOINT_PATHS": str(grid_per_load["facility_sub"]["disjoint_paths"]),
        # --- Breach hydrograph ---
        "GE_BREACH_WIDTH_M": _fmt(hydro["breach_width_m"]),
        "GE_HYDROGRAPH_DURATION_MIN": _fmt(hydro["duration_min"]),
        "GE_MEAN_OUTFLOW_CMS": _fmt(hydro["mean_outflow_cms"], 0),
        "GE_NUM_STATIONS": str(len(stations)),
        "GE_FARTHEST_STATION_KM": _fmt(stations[-1]["distance_km"]),
        "GE_FARTHEST_ARRIVAL_MIN": _fmt(stations[-1]["arrival_time_min"]),
        # --- Environment ---
        "PYTHON_VERSION": platform.python_version(),
        "NUMPY_VERSION": np.__version__,
        "GENERATION_TIMESTAMP": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }

    if require_outputs:
        # Strict mode: refuse to hand the manuscript a token that is NaN or
        # infinite. A degenerate scenario (zero-volume reservoir, unreachable
        # load, zero-field asset) silently produces such values, and a rendered
        # "nan V/m" would read as a result. This gate can fail — see
        # tests/test_manuscript_variables.py::TestStrictModeGate.
        broken = _non_finite_tokens(variables)
        if broken:
            raise ValueError(f"ARKANGEL analysis produced non-finite manuscript tokens — gate refused: {broken}")

    return variables


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``README.md``). In strict mode any leftover ``{{TOKEN}}`` fails so the
    manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript = Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    output = Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    resolved: list[str] = []
    for source in sorted(manuscript.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output.mkdir(parents=True, exist_ok=True)
        (output / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output, resolved
