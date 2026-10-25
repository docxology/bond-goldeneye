# COUNTS — goldeneye (live)

> Generated from the last full run; do not hand-edit. Refresh after any
> source/test change by re-running the coverage gate.

- Project: `docxology/bond-goldeneye` (BOND film package, GoldenEye: ARKANGEL; from the suite's `projects/working/bond/goldeneye`)
- Gate: `uv run pytest tests/ --cov=src --cov-fail-under=90` (line + branch)
- Python 3.14.6, pytest 9.0.2, pytest-cov 7.0.0

| Metric | Value |
| --- | --- |
| Tests passed | 344 |
| Tests failed / skipped | 0 / 0 |
| Line + branch coverage (src/) | 99.65% |
| Coverage floor | 90% (line + branch) |
| Gate result | PASS |

## Module coverage (last run)

| Module | Coverage |
| --- | --- |
| `src/goldeneye/breach_hydrograph.py` | 100.00% |
| `src/goldeneye/coupling.py` | 100.00% |
| `src/goldeneye/emp_model.py` | 100.00% |
| `src/goldeneye/figures/emp_footprint.py` | 100.00% |
| `src/goldeneye/figures/flood_wave.py` | 100.00% |
| `src/goldeneye/figures/grid_resilience.py` | 100.00% |
| `src/goldeneye/kill_radius.py` | 100.00% |
| `src/goldeneye/manuscript_variables.py` | 100.00% |
| `src/goldeneye/mission.py` | 100.00% |
| `src/goldeneye/scenario.py` | 100.00% |
| `src/goldeneye/grid_resilience.py` | 99.64% |
| `src/goldeneye/dam_security.py` | 98.79% |
| `src/goldeneye/orbital_mechanics.py` | 98.36% |

Residual misses are the three sites documented in `docs/architecture.md`:
the two defensive zero-divide guards (`dam_security.py:198`,
`orbital_mechanics.py:149`) and the Dijkstra loop's unreachable fall-through in
`most_reliable_path` (`grid_resilience.py:257->281`, whose `while` always exits
via its `break`). All are unreachable through the public API given upstream
invariants that are themselves pinned by tests.

Other gates from the same checkout: `ruff check` clean, `ruff format --check`
clean (48 files), `mypy src/ scripts/` clean (23 source files).

Zero mocks; deterministic; pure core verified importable without bond-api.
