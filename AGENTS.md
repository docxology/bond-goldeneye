# GoldenEye — ARKANGEL (BOND film package)

**This is a BOND-suite film package**, mission codename **ARKANGEL** (GoldenEye,
1995). It implements the frozen `bond_api.MissionProvider` protocol over a pure,
deterministic domain core of seven concept modules. The agent rulebook lives in
`docs/` — start at `docs/agent_instructions.md`. Live test counts and coverage
are generated into `docs/_generated/COUNTS.md` and never hardcoded in prose.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/goldeneye/{emp_model,kill_radius,dam_security,orbital_mechanics,coupling,grid_resilience,breach_hydrograph,scenario}.py` (pure core) | Deterministic closed-form math. No `bond_api` / `bond_utilities` imports; importable without the suite. |
| `src/goldeneye/mission.py` (protocol adapter) | The only `src` module that imports `bond_api`; implements the frozen `MissionProvider` + registers gadgets. |
| `src/goldeneye/manuscript_variables.py`, `figures/` | Manuscript hydration + concept figures. |
| `scripts/` | Thin orchestrators (one per mission phase); no business logic. |
| Live counts | `docs/_generated/COUNTS.md`; never hardcode test totals or coverage %. |

The layer contract is enforced by the test suite itself, not by a separate
script: `tests/test_mission.py::TestPureCoreWithoutBondApi` spawns a subprocess
with `bond_api`/`bond_utilities` removed and imports the pure core, and the
zero-mock audit below is a one-line grep over `tests/`.

## Concept payload (the deep core)

* **`emp_model.py` — Orbital EMP weapon.** Documented conservative point-source
  envelope `E(r) = E0·Y_s·(h/d)²·exp(−(d−h)/λ(h))`; ground-range geometry,
  line-of-sight/horizon bound, yield scaling, and normalized double-exponential
  E1/E2/E3 waveform (IEC 61000-2-9 E1 constants).
* **`kill_radius.py` — Electronics kill-radius.** Four vulnerability classes;
  deterministic bisection kill radius, kill area, footprint fraction, and a
  smooth damage-probability logistic.
* **`orbital_mechanics.py` — Orbital platform.** Circular-orbit period/speed
  (vis-viva), spherical-Earth central angle / elevation / slant range,
  visibility, and overhead pass duration (deterministic bisection).
* **`coupling.py` — EM coupling & shielding.** Skin depth, Schelkunoff
  absorption + reflection shielding effectiveness, conductor effective height
  and induced voltage, protection margin.
* **`grid_resilience.py` — Power-network resilience.** Per-asset survival,
  most-reliable path (Dijkstra on `-log` survival) and edge-disjoint path count
  (Edmonds-Karp), resilience report.
* **`dam_security.py` — Arkangel dam security.** Defense-in-depth access-control
  cascade (cumulative detection, expected response time, security score) and
  breach-flood risk (Froehlich 1995 peak outflow; Ritter 1892 dam-break).
* **`breach_hydrograph.py` — Breach hydrograph.** Froehlich (2008) breach width,
  volume-conserving triangular outflow hydrograph, downstream station table.

## Protocol integration

* `src/goldeneye/mission.py` exposes `MissionProvider` at module top level
  (slug `goldeneye`), discovered by `bond_api.discovery.load_provider`.
* Gadgets (EMP field, waveform, kill radius, breach discharge, Ritter depth,
  cumulative detection) are registered with `bond_api.GadgetRegistry` under
  `goldeneye` at import time.
* `scripts/execute.py` persists the outcome (bond-api tagged JSON) and a
  provenance record via `bond_utilities.mission_io.record_provenance_outcome`.

## Verification gates

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # ≥90% line+branch
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo Clean
```

No mock framework anywhere in `tests/` — real data + computation only.

## Agent protocol

Start with `docs/agent_instructions.md` (read-first), then
`docs/architecture.md` before changing `src/`/`scripts/` boundaries, and
`docs/testing_philosophy.md` before writing any `pytest` file. Update this file,
`README.md`, and `TODO.md` to reflect the package.
