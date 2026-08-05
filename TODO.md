# goldeneye TODO

Forward-only backlog for the GoldenEye: ARKANGEL BOND film package.

## Deepened (phase 4)

Four new pure-core modules (infrastructure-free) and their integration:

- `src/goldeneye/orbital_mechanics.py` — Keplerian circular-orbit period/speed,
  spherical-Earth central angle / elevation / slant range, visibility, and
  overhead pass duration (deterministic bisection).
- `src/goldeneye/coupling.py` — skin depth, Schelkunoff absorption+reflection
  shielding effectiveness, conductor effective height / induced voltage /
  protection margin.
- `src/goldeneye/grid_resilience.py` — regional network per-asset survival,
  most-reliable path (Dijkstra on `-log` survival), edge-disjoint path count
  (Edmonds-Karp), resilience report.
- `src/goldeneye/breach_hydrograph.py` — Froehlich (2008) breach width,
  volume-conserving triangular outflow hydrograph, downstream station table.
- `scenario.py::analyze_arkangel` now emits `orbit`, `coupling`, `grid`,
  `hydrograph` sections; `mission.py` exposes 9 plan steps and 20 gadgets while
  keeping the frozen `bond_api` surface unchanged; a third figure
  (`grid_resilience.png`) renders the network analysis.

See `docs/_generated/COUNTS.md` for live test count + coverage.

## Built (phase 2)

- **Pure domain core** (infrastructure-free, importable without bond-api):
  - `src/goldeneye/emp_model.py` — orbital EMP threat envelope (detonation→ground
    E1 field), geometry/horizon, yield scaling, E1/E2/E3 waveform.
  - `src/goldeneye/kill_radius.py` — electronics kill radii by vulnerability
    class (bisection), kill area, footprint fraction, damage probability.
  - `src/goldeneye/dam_security.py` — Arkangel access control (defense in depth)
    and breach-flood risk (Froehlich 1995; Ritter 1892 dam break).
- **Scenario composition** — `src/goldeneye/scenario.py::ARKANGEL`, config
  loading, `analyze_arkangel` (deterministic), canonical input hash.
- **Protocol adapter** — `src/goldeneye/mission.py` implements the frozen
  `bond_api.MissionProvider` (brief/recon/plan/execute/debrief) and registers 8
  analytical gadgets with `bond_api.GadgetRegistry`.
- **Manuscript + figures** — `src/goldeneye/manuscript_variables.py` (token
  hydration), `src/goldeneye/figures/` (EMP footprint, flood wave);
  `manuscript/` ARKANGEL sections + config + references.
- **Thin CLIs** — `scripts/brief.py`, `recon.py`, `plan.py`, `execute.py`,
  `debrief.py`, `z_generate_manuscript_variables.py`.
- **Tests** — zero-mock, in-process figure tests, subprocess CLI smoke, and a
  proof that the pure core imports without bond-api. See `docs/_generated/COUNTS.md`.

## Verification evidence

- `uv run pytest tests/ --cov=src --cov-fail-under=90` (≥90% line+branch).
- `uv run ruff check` / `ruff format --check` on `src/ scripts/ tests/`.
- `uv run mypy src/ scripts/` clean.
- Zero mocks in `tests/`; no `bond_api` import in the pure core.
- Lineage: `rg template[_]code_project` → zero in the tree.

## Declared integration points

- **Provenance persistence**: `scripts/execute.py` records outcomes via
  `bond_utilities.mission_io.record_provenance_outcome` (bond-utilities, phase-1
  done). If that helper is ever unavailable, `analyze_arkangel` still returns
  the `input_hash` + full results for callers to persist themselves.
- **Orchestrator discovery**: `src/goldeneye/mission.py` exposes `MissionProvider`
  at module top level; bond-api (frozen) discovers it by slug `goldeneye`.
  Accept: orchestrator can `load_provider("goldeneye")` and drive all five stages.

## Forward items

- (Optional) dashboard / HTML report mirroring the analysis, if the generator
  pattern in `src/` is extended.
- Add a negative-control test before widening kill-radius claims beyond the
  documented envelope regime (the conservative point-source assumption).
- Refresh `docs/_generated/COUNTS.md` and figures after any public-surface change.
