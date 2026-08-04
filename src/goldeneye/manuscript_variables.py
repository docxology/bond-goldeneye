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

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

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


def _class_token_suffix(name: str) -> str:
    """Map a vulnerability-class slug to its token suffix (``UNPROTECTED``)."""
    return name.upper()


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), gate on a non-empty scenario
            analysis (the strict-mode check that keeps metrics real).
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

    if require_outputs and not kill_table:
        raise ValueError("ARKANGEL analysis produced no kill-radius rows — gate refused")

    variables: dict[str, str] = {
        "GE_IDENTITY": "GOLDENEYE",
        "GE_CODENAME": str(analysis["codename"]),
        "GE_TITLE": str(paper.get("title", "")),
        "GE_SUBTITLE": str(paper.get("subtitle", "")),
        "GE_VERSION": str(paper.get("version", "")),
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
        # --- Environment ---
        "PYTHON_VERSION": platform.python_version(),
        "NUMPY_VERSION": np.__version__,
        "GENERATION_TIMESTAMP": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }
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
