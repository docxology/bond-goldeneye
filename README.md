# GoldenEye: ARKANGEL — Special-Agent Mission Software

A BOND-suite film package for *GoldenEye* (1995), mission codename **ARKANGEL**.
It models, as deterministic closed-form physics, the coupled threat surfaces
of the film:

1. **Orbital EMP weapon & platform** — a high-altitude nuclear-burst model from
   detonation geometry to ground-level E1 field and the E1/E2/E3 pulse
   (`emp_model.py`), plus the Keplerian orbital platform delivering it
   (`orbital_mechanics.py`).
2. **Electronics kill radius** — per vulnerability class (unprotected,
   commercial, MIL-STD-188-125 hardened, legacy vacuum-tube) via deterministic
   bisection (`kill_radius.py`).
3. **EM coupling & shielding** — skin depth, Schelkunoff shielding
   effectiveness, conductor coupling and protection margin over sensitive
   infrastructure (`coupling.py`).
4. **Regional power-network resilience** — per-asset survival from the field
   envelope, most-reliable and edge-disjoint source-to-load routing
   (`grid_resilience.py`).
5. **Arkangel dam security** — layered defense-in-depth access control and
   breach-flood risk (`dam_security.py`), extended by a volume-conserving
   breach hydrograph and downstream station table (`breach_hydrograph.py`).

The seven concept modules are pure and infrastructure-free: they can be
imported in any Python environment with no BOND layer. A thin adapter
(`src/goldeneye/mission.py`) implements the frozen `bond_api.MissionProvider`
protocol (brief / recon / plan / execute / debrief) and registers the mission's
analytical gadgets with the `bond_api.GadgetRegistry`, so the suite's
orchestrator discovers it by slug.

## Quick start

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90

# Mission phases (thin CLIs)
uv run python scripts/brief.py
uv run python scripts/recon.py "assess the Arkangel facility"
uv run python scripts/plan.py
uv run python scripts/execute.py      # runs the analysis, persists outcome + provenance
uv run python scripts/debrief.py       # reads the persisted outcome, prints lessons

# Manuscript variables + figures + resolved tree
uv run python scripts/z_generate_manuscript_variables.py
```

`uv sync` resolves `bond-api` and `bond-utilities` from the suite working tree
via `[tool.uv.sources]`; those two packages are not on PyPI, so outside the
suite see `STANDALONE.md` for the bare-clone verification recipe.

Regenerable artifacts land under `output/` (git-ignored): the mission outcome
(`data/arkangel_outcome.json` in bond-api wire format), the provenance record
(`data/arkangel_mission.json` via `bond_utilities.mission_io`), the
manuscript-variable map, and three concept figures
(`figures/emp_footprint.png`, `figures/flood_wave.png`,
`figures/grid_resilience.png`).

## Canonical ARKANGEL scenario

| Parameter | Value |
|---|---|
| Weapon yield | 2000 kt |
| Burst / orbit altitude | 300 km |
| Reservoir volume / head | 1.3e8 m³ / 75 m |
| Facility downstream | 8 km |
| Access-control layers | 4 |
| Regional grid nodes / lines | 5 / 6 |
| Downstream inundation stations | 3 |

Scenario defaults live in `manuscript/config.yaml` and
`src/goldeneye/scenario.py::ARKANGEL`; every manuscript token derives from them.

## Modules

Every module under `src/goldeneye/` and what it computes:

| Module | One-line description |
| --- | --- |
| `emp_model.py` | Burst-to-ground E1 field envelope, geometry and horizon, yield scaling, atmospheric attenuation, and the normalized E1/E2/E3 double-exponential waveform. |
| `orbital_mechanics.py` | Circular-orbit period and speed (vis-viva), great-circle central angle, platform elevation, slant range, visibility, and overhead pass duration. |
| `kill_radius.py` | Four electronics vulnerability classes, per-class kill radius by deterministic bisection, kill area, footprint fraction, and a smooth damage-probability logistic. |
| `coupling.py` | Skin depth, Schelkunoff absorption + reflection shielding effectiveness, conductor effective height, induced voltage, conducted current, and protection margin. |
| `grid_resilience.py` | Per-asset survival from the local field, most-reliable source-to-load path (Dijkstra on `−log` survival), edge-disjoint path count (Edmonds-Karp), and the network resilience report. |
| `dam_security.py` | Defense-in-depth access-control cascade (cumulative detection, expected response time, security score) and breach-flood risk (Froehlich 1995 peak outflow, Ritter 1892 dam break). |
| `breach_hydrograph.py` | Froehlich (2008) breach width, volume-conserving triangular outflow hydrograph, and the downstream station inundation table. |
| `scenario.py` | Composition layer: the canonical `ARKANGEL` scenario, `manuscript/config.yaml` overlay, the deterministic `analyze_arkangel()` result, and the canonical input hash. |
| `manuscript_variables.py` | Hydrates every manuscript `{{TOKEN}}` from config + analysis, and resolves the section tree into `output/manuscript/`. |
| `mission.py` | The only `bond_api` importer: the frozen `MissionProvider` adapter plus the `GADGETS` registry. |
| `figures/emp_footprint.py` | Renders the EMP threat envelope and per-class kill radii. |
| `figures/flood_wave.py` | Renders the Ritter dam-break flood wave. |
| `figures/grid_resilience.py` | Renders the regional grid with per-asset survival. |

## MissionProvider surface (frozen)

`src/goldeneye/mission.py` exposes the BOND protocol contract that the CLI,
coordinator and orchestrator consume. Its public shape is stable and must not
change:

| Member | Signature | Returns |
| --- | --- | --- |
| `MissionProvider.film` | attribute | `"goldeneye"` (the discovery slug) |
| `brief` | `() -> MissionBrief` | 5 objectives, 2 assets, 3 constraints |
| `recon` | `(ReconRequest) -> ReconReport` | 5 findings |
| `plan` | `(MissionBrief) -> MissionPlan` | 9 ordered steps |
| `execute` | `(MissionPlan) -> MissionOutcome` | full analysis + `Provenance` (seed 0, input hash) |
| `debrief` | `(MissionOutcome) -> Debrief` | 6 lessons |
| `GADGETS` | module-level `GadgetRegistry` | 20 callables registered under `goldeneye` |

Discovery: `bond_api.discovery.load_provider("goldeneye")`.

## Layout

```
src/goldeneye/        pure core (7 concept modules) + scenario composition,
                      manuscript_variables, figures/, mission.py (protocol adapter)
scripts/              thin orchestrators (brief/recon/plan/execute/debrief/z_generate)
tests/                zero-mock suite; 90% line+branch floor enforced on src/
manuscript/           ARKANGEL sections + config.yaml + references.bib
docs/                 agent rulebook (read-first protocol, architecture, testing)
```

Verification gates — all four must pass before any change is done:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Measured test count and coverage live in `docs/_generated/COUNTS.md` (generated
from a real run) and are deliberately not quoted in this file, so it cannot go
stale.

See `AGENTS.md` for the layer contract, `docs/architecture.md` for the
module-by-module architecture, and `docs/agent_instructions.md` for the
read-first behavioral rules. The canonical remote is
`github.com/docxology/bond-goldeneye`; `STANDALONE.md` records how to install
and verify this tree outside the suite working tree.
