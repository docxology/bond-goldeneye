# goldeneye TODO

Remaining work for the **GoldenEye: ARKANGEL** BOND film package. This file
tracks what is *still open*. Completed work is described in `README.md` (what
the package does) and `docs/architecture.md` (how it is put together) — it is
not re-listed here.

Live test count and coverage: `docs/_generated/COUNTS.md`. Never quote those
figures in prose; cite the gate instead.

## Open — modelling

- **Negative control for the kill-radius envelope.** Before any claim widens
  beyond the documented conservative point-source regime, add a test that fails
  when the envelope is used outside it. The current suite proves the model is
  self-consistent, not that its regime of validity is respected.
- **Grid independence assumption.** `resilience_report`'s expected served load
  sums each critical load's best-path reliability, which assumes independent
  asset failures. A correlated-failure variant (shared corridor, common-mode
  field) would materially change the served fraction. Scoped but not started;
  the limitation is disclosed in `07_scope_and_related_work.md`.
- **Flood routing.** The downstream station table uses the frictionless
  asymptotic peak depth `4H/9` and the Ritter front speed. A friction-aware
  routing step would turn the arrival times from lower bounds into estimates.
- **E2 amplitude fraction.** `E2_AMPLITUDE_FRACTION` is an engineering default,
  not a standardized value (IEC 61000-2-9 specifies E1 most strictly). If a
  sourced value is found, replace the constant and cite it.

## Open — engineering

- **Non-zenith pass geometry.** `overhead_pass_duration_s` assumes a directly
  overhead pass, so durations are upper bounds. A general ground-track pass
  would need the platform's inclination and the target's offset from the track.
- **Parallel-circuit reporting.** Parallel circuits now count correctly toward
  redundancy and collapse to the most survivable circuit for path reliability.
  The canonical grid has no parallel pair, so that path is exercised only by
  tests — add one to the scenario if the grid is ever expanded.

## Deliberately not doing

- Chasing the last two uncovered branches. Both are defensive guards that are
  unreachable through the public API given upstream invariants
  (`SecurityLayer`'s probability range and `central_angle_deg`'s clamp). They
  are commented at the call site and listed in `docs/architecture.md`, and the
  invariants that make them unreachable are pinned by tests. Deleting them would
  turn a future invariant change into a silent zero-divide.
- Changing anything in the frozen `bond_api` MissionProvider surface. Depth goes
  inside the package.

## Integration points

- **Provenance persistence** — `scripts/execute.py` records outcomes via
  `bond_utilities.mission_io.record_provenance_outcome`. If that helper is ever
  unavailable, `analyze_arkangel` still returns `input_hash` plus the full
  results for callers to persist themselves.
- **Orchestrator discovery** — `src/goldeneye/mission.py` exposes
  `MissionProvider` at module top level; bond-api discovers it by the slug
  `goldeneye`. Acceptance: the orchestrator can `load_provider("goldeneye")` and
  drive all five stages.

## Housekeeping

- Refresh `docs/_generated/COUNTS.md` and re-render the three figures after any
  change to the public surface or the scenario defaults.
