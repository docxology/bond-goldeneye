# COUNTS — goldeneye (live)

> Generated from the last full run; do not hand-edit. Refresh after any
> source/test change by re-running the coverage gate.

- Project: `projects/working/bond/goldeneye` (BOND film package, GoldenEye: ARKANGEL)
- Gate: `uv run pytest tests/ --cov=src --cov-fail-under=90` (line + branch)

| Metric | Value |
| --- | --- |
| Tests passed | 264 |
| Branch coverage (src/) | 95.77% |
| Coverage floor | 90% (line + branch) |
| Gate result | PASS |

## Module coverage (last run)

| Module | Coverage |
| --- | --- |
| `src/goldeneye/figures/emp_footprint.py` | 100% |
| `src/goldeneye/figures/flood_wave.py` | 100% |
| `src/goldeneye/figures/grid_resilience.py` | 100% |
| `src/goldeneye/emp_model.py` | 99.15% |
| `src/goldeneye/kill_radius.py` | 98.04% |
| `src/goldeneye/breach_hydrograph.py` | 97.06% |
| `src/goldeneye/manuscript_variables.py` | 96.20% |
| `src/goldeneye/orbital_mechanics.py` | 96.72% |
| `src/goldeneye/dam_security.py` | 95.06% |
| `src/goldeneye/grid_resilience.py` | 93.43% |
| `src/goldeneye/coupling.py` | 92.59% |
| `src/goldeneye/scenario.py` | 92.90% |
| `src/goldeneye/mission.py` | 92.86% |

Zero mocks; deterministic; pure core verified importable without bond-api.
