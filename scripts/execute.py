#!/usr/bin/env python3
"""ARKANGEL mission phase 4/5 — EXECUTE: run the analysis and persist results.

Thin orchestrator: executes the mission plan against the provider, prints a
kill-radius summary, and persists two artifacts under ``output/data/``:

* ``arkangel_outcome.json`` — the full :class:`MissionOutcome` in the
  bond-api tagged-JSON wire format (round-trippable via ``bond_api.serialization``).
* ``arkangel_mission.json`` — a provenance-outcome record written through the
  shared ``bond_utilities.mission_io.record_provenance_outcome`` helper.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.serialization import to_json  # noqa: E402
from bond_utilities.mission_io import record_provenance_outcome  # noqa: E402
from bond_utilities.reporting import banner, print_kv, print_table  # noqa: E402
from goldeneye.mission import MissionProvider, SEED  # noqa: E402
from goldeneye.scenario import ARKANGEL, scenario_input_dict  # noqa: E402

_DATA_DIR = _PROJECT_ROOT / "output" / "data"


def main() -> int:
    """Run the ARKANGEL execute stage and persist the artifacts."""
    provider = MissionProvider()
    brief = provider.brief()
    plan = provider.plan(brief)
    outcome = provider.execute(plan)

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    outcome_path = _DATA_DIR / "arkangel_outcome.json"
    outcome_path.write_text(to_json(outcome), encoding="utf-8")

    record_provenance_outcome(
        mission_id="arkangel",
        seed=SEED,
        version=outcome.provenance.package_version,
        input_payload=scenario_input_dict(ARKANGEL),
        outcome=dict(outcome.results),
        path=_DATA_DIR / "arkangel_mission.json",
        codename="ARKANGEL",
    )

    kill = outcome.results["kill_radius"]
    emp = outcome.results["emp"]
    flood = outcome.results["flood"]
    access = outcome.results["access"]

    print(banner("ARKANGEL — EXECUTION REPORT"))
    print_kv(
        [
            ("success", outcome.success),
            ("seed", outcome.provenance.seed),
            ("input_hash", outcome.provenance.input_hash[:16]),
            ("yield_kt", emp["yield_kt"]),
            ("burst_altitude_km", emp["burst_altitude_km"]),
            ("nadir_field_vm", f"{emp['nadir_field_vm']:.0f}"),
            ("horizon_range_km", f"{emp['horizon_range_km']:.0f}"),
        ]
    )
    print("Kill radius by vulnerability class:")
    print_table(
        [[row["name"], row["label"], f"{row['radius_km']:.1f} km"] for row in kill],
        headers=["class", "label", "radius"],
    )
    print_kv(
        [
            ("flood_arrival_min", f"{flood['arrival_time_min']:.2f}"),
            ("flood_peak_depth_m", f"{flood['peak_depth_m']:.1f}"),
            ("flood_risk", flood["risk_rating"]),
            ("access_detection_p", f"{access['detection_probability']:.3f}"),
            ("security_score", f"{access['security_score']:.1f}"),
        ]
    )
    print(f"Wrote {outcome_path}")
    print(f"Wrote {_DATA_DIR / 'arkangel_mission.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
