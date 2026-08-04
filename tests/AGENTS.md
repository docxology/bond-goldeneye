# tests/ — zero-mock deterministic suite

Tests validate the ARKANGEL pure core, the BOND `MissionProvider` adapter, the
manuscript token map, the concept figures, and the thin CLIs — all with real
computation, never mocks.

## Layout

| File | Scope |
| --- | --- |
| `conftest.py` | `MPLBACKEND=Agg`, `src/` on `sys.path` |
| `test_emp_model.py` | EMP geometry, envelope, waveform, registry |
| `test_kill_radius.py` | kill radii, areas, sweeps, damage probability |
| `test_dam_security.py` | access control, Froehlich, Ritter, flood risk |
| `test_scenario.py` | ARKANGEL defaults, determinism, input hash, config |
| `test_mission.py` | protocol conformance, gadgets, serialization, discovery, pure-core isolation |
| `test_manuscript_variables.py` | token map + live cross-reference |
| `test_figures.py` | in-process concept-figure rendering |
| `test_scripts_smoke.py` | subprocess CLI smoke + artifact assertions |

## Contract

- Zero mocks: `rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/`.
- Deterministic: fixed inputs, known vectors, analytic limits; byte-identical
  two-run assertions for the analysis.
- Coverage floor: `uv run pytest tests/ --cov=src --cov-fail-under=90`
  (line + branch). Live numbers in `docs/_generated/COUNTS.md`.
