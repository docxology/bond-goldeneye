#!/usr/bin/env python3
"""ARKANGEL mission phase 2/5 — RECON: survey the threat and facility.

Thin orchestrator: runs the provider's reconnaissance stage for the supplied
goal and prints the resulting findings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest  # noqa: E402
from bond_utilities.reporting import banner, print_kv  # noqa: E402
from goldeneye.mission import MissionProvider  # noqa: E402

_DEFAULT_GOAL = "assess the orbital EMP threat and the Arkangel dam-facility security"


def main() -> int:
    """Print the ARKANGEL reconnaissance findings."""
    parser = argparse.ArgumentParser(description="ARKANGEL reconnaissance")
    parser.add_argument("goal", nargs="?", default=_DEFAULT_GOAL, help="recon goal")
    args = parser.parse_args()

    report = MissionProvider().recon(ReconRequest(goal=args.goal))
    print(banner("ARKANGEL — RECONNAISSANCE"))
    print_kv([("goal", args.goal), ("findings", len(report.findings))])
    for finding in report.findings:
        print(f"  [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
