#!/usr/bin/env python3
"""ARKANGEL mission phase 3/5 — PLAN: print the deterministic analysis plan.

Thin orchestrator: derives the :class:`MissionPlan` from the brief and prints
the ordered steps.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_utilities.reporting import banner, print_kv, print_table  # noqa: E402
from goldeneye.mission import MissionProvider  # noqa: E402


def main() -> int:
    """Print the ARKANGEL mission plan."""
    provider = MissionProvider()
    brief = provider.brief()
    plan = provider.plan(brief)
    print(banner("ARKANGEL — MISSION PLAN"))
    print_kv([("steps", len(plan.steps))])
    print_table(
        [[step.name, step.action, repr(step.params)] for step in plan.steps],
        headers=["step", "action", "params"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
