#!/usr/bin/env python3
"""ARKANGEL mission phase 5/5 — DEBRIEF: report lessons from the outcome.

Thin orchestrator: loads the persisted :class:`MissionOutcome` written by
``scripts/execute.py``, runs the provider's debrief stage, and prints the
lessons. Exits 1 (with a message) if the outcome artifact is absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.serialization import from_json  # noqa: E402
from bond_utilities.reporting import banner, print_kv  # noqa: E402
from goldeneye.mission import MissionProvider  # noqa: E402

_OUTCOME_PATH = _PROJECT_ROOT / "output" / "data" / "arkangel_outcome.json"


def main() -> int:
    """Print the ARKANGEL debrief from the persisted outcome."""
    if not _OUTCOME_PATH.is_file():
        print(f"no outcome artifact at {_OUTCOME_PATH} — run scripts/execute.py first")
        return 1
    outcome = from_json(_OUTCOME_PATH.read_text(encoding="utf-8"))
    debrief = MissionProvider().debrief(outcome)
    print(banner("ARKANGEL — DEBRIEF"))
    print_kv(
        [
            ("success", outcome.success),
            ("lessons", len(debrief.lessons)),
            ("input_hash", outcome.provenance.input_hash[:16]),
        ]
    )
    for i, lesson in enumerate(debrief.lessons, 1):
        print(f"  {i}. {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
