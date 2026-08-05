# Reproducibility

This is version **{{GE_VERSION}}** of **{{GE_TITLE}}**. Every numeric claim in
this manuscript — result, model constant, and scenario input alike — is produced
from source by a regenerable pipeline; none is hand-authored.

## Regeneration contract

1. `uv run python scripts/execute.py` runs the full mission and persists
   `output/data/arkangel_outcome.json` (bond-api wire format) and a
   provenance-outcome record `output/data/arkangel_mission.json` written via
   `bond_utilities.mission_io.record_provenance_outcome`.
2. `scripts/z_generate_manuscript_variables.py` writes
   `output/data/manuscript_variables.json`, renders the three concept figures
   to `output/figures/`, and resolves the numbered sections into
   `output/manuscript/`.
3. `uv run pytest tests/ --cov=src --cov-fail-under=90` enforces the coverage
   gate; a live cross-reference test guarantees the token map and the
   manuscript cannot drift apart.

## Determinism

The analysis is fully deterministic: fixed scenario parameters, closed-form
physics, a fixed seed of 0 (no random draws anywhere), and no wall-clock value
in any persisted analysis artifact. The canonical SHA-256 `input_hash` of the
scenario (16 hex characters appear in the execution report) lets any outcome
be audited against the exact inputs that produced it. Two successive runs of
`analyze_arkangel` are byte-identical by test.

## Output inventory

Regenerable artifacts under `output/` (git-ignored):

- `data/arkangel_outcome.json`, `data/arkangel_mission.json`,
  `data/manuscript_variables.json`
- `figures/emp_footprint.png`, `figures/flood_wave.png`,
  `figures/grid_resilience.png`
- `manuscript/` (numbered sections with tokens resolved)

Live test count and achieved coverage are tracked in
`docs/_generated/COUNTS.md`, not hardcoded here.
