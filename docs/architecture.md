# Architecture

The goldeneye package follows the BOND suite layer contract. Read this before
changing `src/` or `scripts/` modular boundaries.

## Layers

```
scripts/                thin orchestrators (one per mission phase)
   │  call
   ▼
src/goldeneye/
   ┌─────────────────────────────────────────────┐
   │ mission.py          bond_api adapter (ONLY   │
   │                     module that imports      │
   │                     bond_api) + gadget reg    │
   └───────────┬─────────────────────────────────┘
               │ call
   ┌───────────▼─────────────────────────────────┐
   │ scenario.py           composition, config,   │
   │                       analyze_arkangel,      │
   │                       input_hash             │
   └───────────┬─────────────────────────────────┘
   ┌───────────▼─────────────────────────────────┐
   │ emp_model.py │ kill_radius.py │ dam_security.py   │  PURE CORE
   │   (EMP)      │  (kill radii)  │ (access + flood)   │  no bond imports
   └─────────────────────────────────────────────┘
   manuscript_variables.py  figures/       (hydration + concept figures)
```

## Dependency rules

- **Pure core** (`emp_model`, `kill_radius`, `dam_security`, `scenario`): stdlib
  + pyyaml only (scenario reads `manuscript/config.yaml`). No `bond_*`, no
  `infrastructure` imports.
- **Protocol adapter** (`mission.py`): imports `bond_api.protocol` and
  `bond_api.registry`; composes the pure core. Nothing imports `mission.py`
  except scripts and discovery.
- **Manuscript/figure layer**: `manuscript_variables.py` reads config + scenario;
  `figures/` render deterministic PNGs (headless Agg backend).
- **scripts** may import anything (they bootstrap `src/` on `sys.path`).
- No module imports upward (nothing imports a script).

## Forbidden patterns

- Math authored inside `scripts/`.
- `bond_api` imported outside `mission.py`.
- Nondeterministic draws or `datetime.now()` in `analyze_arkangel` / figures.

## The BOND integration seam

`scripts/execute.py` runs the provider and persists the outcome via
`bond_api.serialization.to_json` plus a provenance record via
`bond_utilities.mission_io.record_provenance_outcome`. bond-api's discovery
finds `goldeneye.mission.MissionProvider` by slug. If `bond-api` is ever
unavailable, the pure core and `scenario.analyze_arkangel` remain fully
functional independently.
