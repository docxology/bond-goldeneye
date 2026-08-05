---
name: goldeneye
description: Use when building/maintaining the GoldenEye ARKANGEL BOND film package (orbital EMP, kill-radius, dam security).
version: 0.1.0
tags: [bond, goldeneye, emp, kill-radius, dam-security, mission-provider, deterministic]
---

# goldeneye (BOND film package)

GoldenEye: ARKANGEL — special-agent mission software for *GoldenEye* (1995).
Implements the frozen `bond_api.MissionProvider` protocol over a pure,
deterministic domain core.

## Modules

- `src/goldeneye/emp_model.py` — orbital EMP threat envelope `E0·Y_s·(h/d)²·exp(−(d−h)/λ(h))`,
  horizon/line-of-sight, yield scaling, E1/E2/E3 normalized double-exponential waveform.
- `src/goldeneye/kill_radius.py` — 4 vulnerability classes; kill radius by deterministic
  bisection; area, footprint fraction, damage-probability logistic.
- `src/goldeneye/orbital_mechanics.py` — Keplerian circular-orbit period/speed,
  spherical-Earth central angle/elevation/slant range, visibility, overhead pass duration.
- `src/goldeneye/coupling.py` — skin depth `sqrt(rho/(π f μ0 μr))`, Schelkunoff SE
  (absorption + reflection), conductor effective height / induced voltage / protection margin.
- `src/goldeneye/grid_resilience.py` — regional network per-asset survival, most-reliable
  path (Dijkstra on `-log` survival), edge-disjoint path count (Edmonds-Karp), report.
- `src/goldeneye/dam_security.py` — defense-in-depth access control (`1−Π(1−p_i)`),
  expected detection time, security score; Froehlich (1995) peak outflow; Ritter (1892) dam-break.
- `src/goldeneye/breach_hydrograph.py` — Froehlich (2008) breach width, volume-conserving
  triangular hydrograph, downstream station table.
- `src/goldeneye/scenario.py` — `ARKANGEL` defaults, config loading, `analyze_arkangel`
  (deterministic dict), SHA-256 `input_hash`.
- `src/goldeneye/mission.py` — the ONLY `bond_api` import; `MissionProvider`
  (brief/recon/plan/execute/debrief) + `GadgetRegistry` under `goldeneye` (20 gadgets).
- `src/goldeneye/manuscript_variables.py`, `figures/` — tokens + 3 concept figures.

## Quick reference

```bash
cd projects/working/bond/goldeneye
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90   # ≥90% line+branch
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/execute.py                      # analysis → output/data/
uv run python scripts/z_generate_manuscript_variables.py  # tokens + figures
```

## Pitfalls

- Pure core (`emp_model`, `kill_radius`, `dam_security`, `scenario`) must NOT
  import `bond_api`/`bond_utilities`. Only `mission.py` imports `bond_api`.
  Verified by an in-process subprocess test.
- `{{TOKEN}}` cross-ref scan covers `manuscript/[0-9][0-9]_*.md` only — keep
  literal double-brace examples out of numbered sections.
- Determinism: seed 0, no RNG, no wall-clock in persisted analysis. Two runs of
  `analyze_arkangel(ARKANGEL)` must be byte-identical.
- Scripts self-insert `src/` on `sys.path`; bootstrap imports need `# noqa: E402`
  (ruff E402 does not auto-cover 4-level BOND script paths).

## Cross-refs

- Root: `../../AGENTS.md`, `docs/agent_instructions.md` (read-first), `TODO.md`.
- Protocol (frozen): external skill `bond-suite-package-development`
  `references/bond-api-phase1.md`.
