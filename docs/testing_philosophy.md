# Testing philosophy

Zero-mock, real computation, deterministic. Read this before writing or
modifying any pytest file.

## Zero-mock policy

No `unittest[.]mock`, `Magic[M]ock`, `mocker.patch`, or `create_auto[s]pec` anywhere
in `tests/`. Tests exercise the real algorithms with real numbers; the
coverage floor is enforced by `pyproject.toml` (`--cov-fail-under=90`,
line + branch on `src/`). Verify with:
`rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo Clean`.

## Determinism

- Fixed input grids and known vectors. No fixed-randomness dependence.
- `test_scenario.py::TestAnalysis::test_analysis_is_deterministic` asserts two
  runs of `analyze_arkangel(ARKANGEL)` are byte-identical.
- `test_mission.py::TestPureCoreWithoutBondApi` runs a subprocess proving the
  pure domain core imports without `bond_api`/`bond_utilities`.

## Test files

| File | Covers |
| --- | --- |
| `tests/test_emp_model.py` | EMP geometry/horizon, envelope limits, waveform normalization, component registry |
| `tests/test_kill_radius.py` | kill radii (bisection + analytic limits), areas, sweep, damage probability |
| `tests/test_dam_security.py` | access control (defense in depth), Froehlich, Ritter wave, flood risk |
| `tests/test_scenario.py` | ARKANGEL defaults, deterministic analysis, input hash, config loading |
| `tests/test_mission.py` | `bond_api.MissionProvider` conformance, gadgets, serialization, discovery, pure-core isolation |
| `tests/test_manuscript_variables.py` | token map + live manuscript cross-reference |
| `tests/test_figures.py` | in-process rendering of both concept figures to real PNGs |
| `tests/test_scripts_smoke.py` | subprocess CLI smoke (exit codes + gitignored artifacts) |

## Running

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Live test count + achieved coverage are tracked in
`docs/_generated/COUNTS.md` (generated, never hardcoded here).
