# Architecture

The `goldeneye` package follows the BOND suite layer contract. Read this before
changing any `src/` or `scripts/` modular boundary.

## Layer topology

```
scripts/                     thin orchestrators (one per mission phase)
   │ call
   ▼
src/goldeneye/mission.py     bond_api adapter — the ONLY module that imports
   │                         bond_api; implements the frozen MissionProvider
   │ call                    and owns the module-level GADGETS registry
   ▼
src/goldeneye/scenario.py    composition — ARKANGEL defaults, config overlay,
   │                         analyze_arkangel(), input_hash()
   │ call
   ▼
PURE CORE (no bond_* imports; importable in any Python environment)

  emp_model ──┬──> kill_radius ──> grid_resilience
              │         │
              │         └──────────┘
  coupling (independent)      orbital_mechanics (independent)

  dam_security ──> breach_hydrograph

src/goldeneye/manuscript_variables.py   token hydration (reads config + scenario)
src/goldeneye/figures/                  deterministic PNG renderers (Agg backend)
```

## The seven pure-core modules

Each is closed-form, deterministic, fully type-hinted, and free of any BOND
import.

| Module | What it computes | Imports |
| --- | --- | --- |
| `emp_model.py` | Burst-to-ground E1 envelope `E(r) = E0·Y_s·(h/d)²·exp(−(d−h)/λ(h))`; slant range, geometric horizon, line-of-sight test; yield scaling; altitude-dependent gamma attenuation length; normalized double-exponential E1/E2/E3 waveform with per-component amplitudes; field-to-energy-density conversion. | — |
| `orbital_mechanics.py` | Circular-orbit radius, period and speed (vis-viva); period→altitude inversion; great-circle central angle; platform elevation angle, slant range and visibility from a ground point; overhead pass duration above a minimum elevation (deterministic bisection). | — |
| `kill_radius.py` | Four `VulnerabilityClass` records (upset/damage thresholds); kill radius per class by deterministic bisection on the monotone envelope; kill area; footprint fraction; smooth damage-probability logistic (`P = 0.5` exactly at threshold); altitude and footprint sweeps. | `emp_model` |
| `coupling.py` | Skin depth `δ = √(ρ/(π f μ₀ μr))`; Schelkunoff plane-wave absorption and reflection loss and their sum; field behind a shield; conductor effective height `L·sin ε`; induced open-circuit voltage; conducted current into a load; protection margin in dB. Three shield materials. | — |
| `grid_resilience.py` | `GridNode`/`GridLine`/`PowerGrid` with validation; per-node and per-line envelope field and survival probability; certainly-failed down-set; most-reliable path (Dijkstra on `−log` survival, insertion-order ties); edge-disjoint path count (Edmonds-Karp, unit capacities, parallel circuits counted separately); full resilience report. | `emp_model`, `kill_radius` |
| `dam_security.py` | Defense-in-depth cascade — cumulative detection `1−∏(1−pᵢ)`, expected time to first detection, composite security score, access corridor; breach flood — Froehlich (1995) peak outflow, Ritter (1892) celerity/depth/velocity/front speed, arrival time, asymptotic peak depth `4H/9`, severity ratio and risk rating. | — |
| `breach_hydrograph.py` | Froehlich (2008) average breach width; volume-conserving triangular outflow hydrograph (`t_d = 2V/Q_p`) and its sampling; mean outflow; downstream `Station` inundation table (arrival, peak depth, risk); combined breach report. | `dam_security` |

`scenario.py` composes all seven. `ARKANGEL` holds the canonical weapon,
reservoir, facility, access cascade, orbit geometry, coupling inputs, the
five-node regional grid and the three downstream stations.
`load_scenario_config()` overlays `manuscript/config.yaml`. `analyze_arkangel()`
returns the single deterministic dictionary — sections `emp`, `kill_radius`,
`orbit`, `coupling`, `grid`, `dam`, `flood`, `hydrograph`, `access` — consumed by
the mission `execute` stage, the manuscript variables and the figures.
`input_hash()` is the canonical SHA-256 of the inputs.

## How `mission.py` implements the frozen MissionProvider

`mission.py` is the single BOND seam. It imports `bond_api.protocol` and
`bond_api.registry`; nothing in the pure core imports it back. Its public shape
is **frozen** — bond-cli, the coordinator reconcile and the orchestrator consume
it across every package, so the class name, the five method signatures and the
module-level `GADGETS` name must not change.

| Surface | Contract | Implementation here |
| --- | --- | --- |
| `MissionProvider` (class name; `film = "goldeneye"`) | Discovered by `bond_api.discovery.load_provider("goldeneye")`, which imports `goldeneye.mission` and instantiates the module-level class. | Declared at module top level. |
| `brief() -> MissionBrief` | Declare objectives, assets, constraints. | Five objectives (EMP + platform, kill radii, coupling, grid, dam + hydrograph); assets carry the scenario name and the envelope constants; constraints declare determinism, the conservative envelope, and the frozen protocol. |
| `recon(ReconRequest) -> ReconReport` | Survey the request against the scenario. | Five `Finding`s — goal echo, weapon, platform, infrastructure, method. Reads `ARKANGEL` only; performs no computation. |
| `plan(MissionBrief) -> MissionPlan` | Ordered deterministic steps. | Nine `Step`s: `emp`, `kill_radius`, `orbit`, `coupling`, `grid`, `dam_security`, `flood_risk`, `hydrograph`, `synthesize`. |
| `execute(MissionPlan) -> MissionOutcome` | Run the analysis, carry provenance. | Calls `analyze_arkangel(ARKANGEL)`, appends `steps_completed` and `outputs`, attaches `Provenance(package_version, seed=0, input_hash, wall_time_s=0.0)`. The zero wall time is deliberate — a real duration would make the artifact non-reproducible. |
| `debrief(MissionOutcome) -> Debrief` | Human-readable lessons. | Six lessons derived from the outcome's `access`, `grid`, `coupling`, `hydrograph` and `dam` sections. |
| `GADGETS` (module-level `GadgetRegistry`) | Q-branch lookup keyed by slug. | Twenty callables registered under `goldeneye` at import time, spanning all seven core modules. |

Deepening the package means adding modules and enriching what `execute`
computes — never changing the table above.

## Dependency rules

- **Pure core** may import stdlib only; `scenario.py` additionally `pyyaml`.
  Never `bond_api`, `bond_utilities`, or `infrastructure`.
- **`mission.py`** may import `bond_api`. Nothing imports `mission.py` except
  `scripts/` and bond-api discovery.
- **`manuscript_variables.py`** reads config + scenario and may import numpy;
  **`figures/`** render deterministic PNGs on the headless Agg backend.
- **`scripts/`** may import anything (they bootstrap `src/` onto `sys.path`).
  No module ever imports a script.

## Forbidden patterns

- Math authored inside `scripts/` — business logic belongs in `src/`.
- `bond_api` imported anywhere outside `mission.py`.
- Nondeterministic draws or `datetime.now()` inside `analyze_arkangel` or the
  figure renderers.
- Renaming or re-signing any row of the MissionProvider table above.

## Deliberately unreachable branches

Two guards are defensive-only and cannot fire through the public API. They are
kept so that relaxing an upstream invariant cannot silently introduce a divide
by zero, and each is commented as such at the call site:

- `dam_security.expected_detection_time_min` — the zero-detection fallback is
  unreachable while `SecurityLayer` enforces `detection_probability ∈ (0, 1]`.
- `orbital_mechanics._elevation_from_central_angle_deg` — the `sin(γ) ≤ 0`
  fallback is unreachable while `central_angle_deg` clamps γ to `[0, 180]`.

Both invariants are pinned by tests, so relaxing one surfaces there first.

## The BOND integration seam

`scripts/execute.py` runs the provider, persists the outcome with
`bond_api.serialization.to_json`, and writes a provenance record via
`bond_utilities.mission_io.record_provenance_outcome`. If `bond-api` is ever
unavailable the pure core and `analyze_arkangel` remain fully functional — a
subprocess test in `tests/test_mission.py` proves the core imports with
`bond_api` absent from the module table.
