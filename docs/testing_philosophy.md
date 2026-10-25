# Testing philosophy

Zero-mock, real computation, deterministic. Read this before writing or
modifying any pytest file in this package.

## Zero-mock policy

No `unittest[.]mock`, `Magic[M]ock`, `mocker.patch`, or `create_auto[s]pec`
anywhere in `tests/`. There is no substitution layer worth introducing — every
module under test is closed-form arithmetic over plain dataclasses, so a
stand-in would only test itself. Tests exercise the real algorithms with real
numbers. Verify:

```bash
rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo Clean
```

Where a test needs a filesystem it uses `tmp_path` with real files (the
manuscript-config tests write real YAML). Where it needs a process boundary it
uses a real subprocess (the CLI smoke tests and the pure-core isolation proof).

## Determinism

- Fixed input grids and known vectors; no reliance on untracked randomness. The
  package draws no random numbers at all — `mission.SEED` is 0 and exists to
  declare that fact to the protocol, not to seed anything.
- `test_scenario.py` asserts two runs of `analyze_arkangel(ARKANGEL)` are
  identical.
- `test_mission.py::TestPureCoreWithoutBondApi` runs a subprocess in which any
  `bond_api`/`bond_utilities` import raises `ImportError` (a `sys.meta_path`
  blocker, self-verified by a positive control), then imports and exercises the
  pure domain core. Both packages remain installed — what is proven is that the
  core never imports them, at module scope or lazily, not that it would run in
  an environment where they are missing. A companion test imports the adapter
  `goldeneye.mission` under the same blocker and requires it to fail, so an
  inert blocker is caught.
- No wall-clock value reaches a persisted analysis artifact;
  `Provenance.wall_time_s` is fixed at 0.0 for exactly this reason.

## Gates must be falsifiable

A gate that cannot fail is worse than no gate, because it reads as protection.
Two conventions follow:

- **Every guard gets a test that makes it fire.** The validation branches in
  `coupling`, `scenario.CouplingParams`, the `grid_resilience` dataclasses and
  `breach_hydrograph` each have a test that triggers them with real bad input.
- **Every strict-mode check ships a positive control.** The `require_outputs`
  gate in `manuscript_variables.generate_variables` refuses non-finite numeric
  tokens, and `TestStrictModeGate` proves it fires by driving a real config to
  an infinite shielding value — then confirms the shipped scenario still clears
  it. This replaced an earlier `not kill_table` check that could never fire,
  since the kill table is built from a non-empty module constant.

The manuscript cross-reference test asserts the token set it scanned is
non-empty before comparing, so it cannot pass vacuously on an empty glob.

Three branches are deliberately unreachable and are *not* chased for coverage;
they are documented in `architecture.md` and commented at the call site.

## Test files

| File | Covers |
| --- | --- |
| `tests/test_emp_model.py` | EMP geometry and horizon, envelope limits and monotonicity, yield scaling, attenuation length, waveform normalization and per-component amplitudes, component registry |
| `tests/test_orbital_mechanics.py` | vis-viva period/speed, period→altitude inversion, central angle, elevation/slant range/visibility, pass duration, degenerate zenith and antipodal geometry |
| `tests/test_kill_radius.py` | kill radii (bisection against analytic limits), kill areas, footprint fraction and its clamps, sweeps, damage-probability logistic |
| `tests/test_coupling.py` | skin depth, absorption/reflection/total shielding effectiveness, shielded field, effective height, induced voltage, conducted current, protection margin, and every input guard |
| `tests/test_grid_resilience.py` | grid validation, per-asset survival, certainly-failed set, Dijkstra most-reliable path, edge-disjoint counts, parallel-circuit redundancy regression, resilience-report aggregates and empty-load behaviour |
| `tests/test_dam_security.py` | access control (defense in depth), security score, Froehlich peak outflow, Ritter celerity/depth/velocity/front, arrival time, risk rating, degenerate wave regions |
| `tests/test_breach_hydrograph.py` | Froehlich (2008) breach width, hydrograph duration and volume conservation, mean outflow, station inundation table, report assembly |
| `tests/test_scenario.py` | ARKANGEL defaults, config overlay and its validation, deterministic analysis, input hash, orbit/coupling section keys |
| `tests/test_claim_ledger.py` | binds every `data/claim_ledger.yaml` row to its named module constant or the live `analyze_arkangel` output, with a negative control proving a perturbed value is caught |
| `tests/test_mission.py` | frozen `bond_api.MissionProvider` conformance, the 20-gadget registry, serialization round-trip, discovery, debrief fallbacks, pure-core isolation |
| `tests/test_manuscript_variables.py` | token map, live manuscript cross-reference, strict-mode gate with positive control, tree resolution (strict and lenient) |
| `tests/test_figures.py` | in-process rendering of all three concept figures to real PNGs |
| `tests/test_scripts_smoke.py` | subprocess CLI smoke for every mission phase (exit codes + gitignored artifacts) |
| `tests/test_reproducibility.py` | byte-identity of the covered regeneration set across two real runs, with the provenance-record exclusion and the wall-clock ban in the token generator |

## Running

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The floor is 90% line **and** branch on `src/`, enforced in `pyproject.toml`.
The live test count and achieved coverage are recorded in
`docs/_generated/COUNTS.md` — generated from a real run, never hardcoded here or
in the manuscript.
