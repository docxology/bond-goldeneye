#!/usr/bin/env python3
"""Thin orchestrator: hydrate manuscript variables, figures, and the resolved tree.

Reads ``manuscript/config.yaml`` and the deterministic ARKANGEL scenario, writes
``output/data/manuscript_variables.json``, renders the EMP-footprint and
flood-wave figures to ``output/figures/``, and substitutes ``{{TOKEN}}`` markers
into ``output/manuscript/`` for downstream rendering.

All computation lives in ``src/goldeneye/manuscript_variables.py`` and
``src/goldeneye/scenario.py``; all figures live in ``src/goldeneye/figures/``.

Exit codes:
    0   variables + figures + tree written
    1   unexpected error (strict mode refused unresolved tokens or empty analysis)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from goldeneye.figures.emp_footprint import plot_emp_footprint  # noqa: E402
from goldeneye.figures.flood_wave import plot_flood_wave  # noqa: E402
from goldeneye.figures.grid_resilience import plot_grid_resilience  # noqa: E402
from goldeneye.manuscript_variables import (  # noqa: E402
    generate_variables,
    resolve_manuscript_tree,
)


def main() -> int:
    """Generate and persist ARKANGEL manuscript variables, figures, and tree."""
    parser = argparse.ArgumentParser(description="Generate GoldenEye: ARKANGEL manuscript variables")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="skip the strict non-empty-analysis gate (early draft mode)",
    )
    args = parser.parse_args()

    variables = generate_variables(require_outputs=not args.allow_draft)
    out_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    figures_dir = _PROJECT_ROOT / "output" / "figures"
    emp_path = plot_emp_footprint(figures_dir / "emp_footprint.png")
    flood_path = plot_flood_wave(figures_dir / "flood_wave.png")
    grid_path = plot_grid_resilience(figures_dir / "grid_resilience.png")

    managed, resolved = resolve_manuscript_tree(variables)
    print(f"wrote {out_path}")
    print(f"wrote {emp_path}")
    print(f"wrote {flood_path}")
    print(f"wrote {grid_path}")
    print(f"resolved {len(resolved)} manuscript sections into {managed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
