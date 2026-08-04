# GoldenEye: ARKANGEL — Special-Agent Mission Software

A BOND-suite film package for *GoldenEye* (1995), mission codename **ARKANGEL**.
It models three coupled threat surfaces as deterministic, closed-form physics:

1. **Orbital EMP weapon** — a high-altitude nuclear-burst model from
   detonation geometry to ground-level E1 field and the canonical E1/E2/E3
   pulse waveform (`src/goldeneye/emp_model.py`).
2. **Electronics kill-radius analysis** — per vulnerability class (unprotected,
   commercial, MIL-STD-188-125 hardened, legacy vacuum-tube) via deterministic
   bisection on the field envelope (`src/goldeneye/kill_radius.py`).
3. **Arkangel dam-facility security** — layered defense-in-depth access
   control and breach-flood risk using the Froehlich (1995) peak-outflow
   regression and the Ritter (1892) dam-break solution
   (`src/goldeneye/dam_security.py`).

The three concept modules are pure and infrastructure-free: they can be
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

Regenerable artifacts land under `output/` (git-ignored): the mission outcome
(`data/arkangel_outcome.json` in bond-api wire format), the provenance record
(`data/arkangel_mission.json` via `bond_utilities.mission_io`), the
manuscript-variable map, and two concept figures
(`figures/emp_footprint.png`, `figures/flood_wave.png`).

## Canonical ARKANGEL scenario

| Parameter | Value |
|---|---|
| Weapon yield | 2000 kt |
| Burst altitude | 300 km |
| Reservoir volume / head | 1.3e8 m³ / 75 m |
| Facility downstream | 8 km |
| Access-control layers | 4 |

Scenario defaults live in `manuscript/config.yaml` and
`src/goldeneye/scenario.py::ARKANGEL`; every manuscript token derives from them.

## Layout

```
src/goldeneye/        pure domain core (emp_model, kill_radius, dam_security, scenario)
                      + manuscript_variables, figures/, and mission.py (protocol adapter)
scripts/              thin orchestrators (brief/recon/plan/execute/debrief/z_generate)
tests/                zero-mock suite, ≥90% line+branch coverage
manuscript/           ARKANGEL sections + config.yaml + references.bib
docs/                 agent rules (read-first protocol)
```

See `AGENTS.md` for the layer contract and `docs/agent_instructions.md` for the
read-first behavioral rules. This is a **local-only** working tree — there is no
remote and it must never be pushed.
