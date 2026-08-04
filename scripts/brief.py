#!/usr/bin/env python3
"""ARKANGEL mission phase 1/5 — BRIEF: print the mission definition.

Thin orchestrator: builds the frozen :class:`MissionBrief` from the
:mod:`goldeneye.mission` provider and prints it via bond-utilities reporting.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_utilities.reporting import banner, print_kv  # noqa: E402
from goldeneye.mission import MissionProvider  # noqa: E402


def main() -> int:
    """Print the ARKANGEL mission brief."""
    brief = MissionProvider().brief()
    print(banner("GOLDENEYE :: ARKANGEL — MISSION BRIEF"))
    print_kv(
        [
            ("film", brief.film),
            ("codename", brief.codename),
            ("objectives", len(brief.objectives)),
            ("assets", len(brief.assets)),
            ("constraints", len(brief.constraints)),
        ]
    )
    print("Objectives:")
    for i, objective in enumerate(brief.objectives, 1):
        print(f"  {i}. {objective}")
    print("Constraints:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
