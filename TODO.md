# TODO — goldeneye (ARKANGEL)

`goldeneye` is the BOND-suite film package for *GoldenEye* (1995), mission
codename **ARKANGEL**. It models the film's coupled threat surfaces as
deterministic closed-form physics across seven pure-core modules (orbital EMP
weapon and platform, electronics kill radius, EM coupling and shielding,
regional grid resilience, dam access control, breach hydrograph), composed by
`scenario.py` and exposed to the suite through the frozen
`bond_api.MissionProvider` adapter in `src/goldeneye/mission.py`.

**Verified state, measured 2026-08-05:** `uv run pytest tests/
--cov=src --cov-fail-under=90` → **335 passed, 0 failed, 0 skipped, 99.65%
line+branch coverage** of `src/` (2 statements, 3 branches uncovered). `ruff
check`, `ruff format --check` (47 files), and `mypy src/ scripts/` (23 files)
are all clean; the zero-mock and lineage greps return nothing. All ten findings
in `output/verify/goldeneye.json` were re-checked against the tree this session
and are fixed at source — the open work below is what remains after them.

Live counts live in `docs/_generated/COUNTS.md`; do not retype them elsewhere.

**Closed 2026-08-05 — the reproducibility claim was false.**
`manuscript_variables.py` built a `GENERATION_TIMESTAMP` token from
`datetime.now(timezone.utc)` and rendered it into
`manuscript/05_experimental_setup.md`, so every regeneration wrote different
bytes while `manuscript/06_reproducibility.md` claimed "no wall-clock value in
any persisted analysis artifact". The wall clock is gone: the dated token is now
`GE_MANUSCRIPT_DATE`, read from the committed `paper.date` in
`manuscript/config.yaml`. `06_reproducibility.md` now names the covered artifact
set and the one exclusion (`output/data/arkangel_mission.json`, the run-scoped
provenance record whose `started_at` is a real clock).
`tests/test_reproducibility.py` regenerates the covered set twice per run and
compares bytes — proven able to fail by temporarily reintroducing the clock.
*Command:* `uv run pytest tests/test_reproducibility.py -v`

---

## Round-2 improvement (2026-08-06)

Hostile self-review against the live tree. Baseline was the 2026-08-05 state: **335
passed / 0 failed / 0 skipped, 99.65% line+branch**, `ruff check`/`ruff format`
(47 files)/`mypy` (23 source files) clean, zero-mock and lineage greps clean. After this
round: **344 passed / 0 failed / 0 skipped, 99.65%** (1139 stmts / 2 miss / 3 brpart;
`manuscript_variables` gained statements), `ruff format --check` clean (48 files), `mypy
src/ scripts/` clean (23 files), zero-mock clean. The three coverage residuals are
unchanged and each is now explicitly accounted for in `docs/architecture.md` (D1) and
`docs/_generated/COUNTS.md` (C2).

### Fixes with test evidence

- **F1 — `scenario.py` inlined the vacuum permittivity.** `analyze_arkangel` computed
  `energy_density_nadir_jm3` as `0.5 * 8.8541878128e-12 * nadir**2`, duplicating the
  canonical constant by hand instead of calling the (otherwise dead-in-production)
  `emp_model.energy_density_jm3`. A change to `VACUUM_PERMITTIVITY` would have silently
  desynced the reported energy density. Now it calls `energy_density_jm3(nadir_vm)`
  (`scenario.py:473`). `TestEnergyDensityBindsCanonicalConstant` (3 tests) pins the
  in-place equality, the quadratic-in-field form, and includes a subprocess negative
  control that mutates `VACUUM_PERMITTIVITY` in a fresh interpreter and requires the
  analysis value to track it — this fails on the previous inline copy.
- **F2 — cross-module physical-constant drift guard.** `dam_security.GRAVITY` and
  `emp_model.GRAVITATIONAL_ACCELERATION` (and the two Earth-radius constants) are
  intentionally duplicated across stdlib-only modules (the layer contract forbids the
  import), so nothing previously stopped one from drifting. `TestCrossModuleConstants`
  binds `dam_security.GRAVITY == emp_model.GRAVITATIONAL_ACCELERATION` and
  `emp_model.EARTH_RADIUS_KM*1000 == orbital_mechanics.EARTH_RADIUS_M`; the Ritter
  celerity and the EMP geometry remain mutually consistent.
- **V1 (closed) — `data/claim_ledger.yaml` was bound by nothing.** Its 19 rows restated
  module constants and generated metrics with zero references in `tests/`/`scripts/`.
  Each row now carries a machine-readable `binding` (`module_attr:<mod>.<ATTR>` or
  `analysis_path:<dotted-path>`), and `tests/test_claim_ledger.py` (4 tests) resolves
  every row against `emp_model`/`dam_security`/… or `analyze_arkangel(ARKANGEL)`, with a
  negative control (halving one `value`) that proves the resolver is not inert. All 19
  rows matched the live run before binding, so no value was stale.
- **C2 (closed) — `COUNTS.md` misattributed the third residual.** It read "the max-flow
  loop's non-exiting back-edge (`grid_resilience.py:257->281`)"; line 257 is the Dijkstra
  `while` in `most_reliable_path`, not the max-flow routine (which is fully covered).
  Re-worded to name the Dijkstra loop's unreachable fall-through. No generator script
  exists for `COUNTS.md` (it is hand-maintained despite the header); the numbers were
  refreshed from this run.
- **D1 (closed) — `docs/architecture.md` accounted for two residuals, the run reports
  three.** The "Deliberately unreachable branches" section now documents all three sites
  — the two zero-divide guards plus the `grid_resilience.most_reliable_path` loop-exit —
  so the coverage `Missing` column is fully explained.

### Manuscript deepening (all bound to the live engine, strict regeneration passes)

- **Nadir energy density.** New token `GE_NADIR_ENERGY_DENSITY` (from
  `emp.energy_density_nadir_jm3`) renders in `03_results.md`: the E1 peak
  **{{GE_NADIR_FIELD_VM}}** V/m carries **0.036** J/m³ at nadir. This also makes the F1
  constant binding visible in the paper.
- **Downstream station table.** New per-station tokens
  `GE_STATION_{N}_{NAME,DIST_KM,ARRIVAL_MIN,DEPTH_M,RISK}` render a live station table in
  `03_results.md` (facility / town / bridge with arrival time, peak depth, risk), bound to
  the breach-hydrograph rows. Generating the tokens from a loop (not a hardcoded count)
  means a station-count change drops tokens, which the strict cross-reference gate flags.
- `scripts/z_generate_manuscript_variables.py` re-ran clean in strict mode (9 sections,
  no unresolved tokens); `output/`, figures, and `docs/_generated/COUNTS.md` refreshed.

### Remaining for a future round

C1 (Unicode in default LaTeX render), V2 (a *sourced* page locator for the reflection-loss
numbers — do not fabricate), V4 (kill-radius regime-of-validity guard), V5 (parallel
circuits in the canonical grid), D2 (second opinion on the Ritter rational-factor
exemption), and the E1–E4 extensions (correlated grid failures, friction-aware routing,
a sourced E2 amplitude, non-zenith pass geometry) are still open. The new station-table
severity (all three canonical stations flood at the same 4H/9 peak, differing only in
arrival time) is an honest consequence of the frictionless Ritter asymptote, already
stated in `07_scope_and_related_work.md`.

---

## Open work

### Correctness

**C1 — Three manuscript sections fail a default `pdflatex` render on Unicode
math symbols.** `manuscript/preamble.md` is empty (it is a stub with only
comments), and the sections use bare Unicode operators that the default pandoc
LaTeX engine cannot typeset:

| Char | Codepoint | Site |
| --- | --- | --- |
| `≥` | U+2265 | `manuscript/01_introduction.md:41` |
| `≈` | U+2248 | `manuscript/03_results.md:72` |
| `−` | U+2212 | `manuscript/07_scope_and_related_work.md:71` |

Reproduced 2026-08-05: `pandoc output/manuscript/01_introduction.md -o /tmp/x.pdf`
aborts with `! LaTeX Error: Unicode character ≥ (U+2265)`; the same for the other
two. Under `--pdf-engine=xelatex` the build completes but emits
`Missing character: There is no ≈ (U+2248) in font [lmroman10-regular]` and the
glyph is dropped from the page — `≈684 A` prints as `684 A` with a blank box.
`°` (U+00B0, `05_experimental_setup.md:19-20`), `—` and `–` all render fine and
are not part of this item.
*Done when:* every resolved section renders under the default engine — for all
nine `output/manuscript/[0-9][0-9]_*.md`, `pandoc <file> -o <out>.pdf` exits 0 —
and the `≈` glyph is present in the extracted text of the results PDF. Fix by
either replacing the three characters with math-mode equivalents (`$\ge$`,
`$\approx$`, `$-$`) or by populating `manuscript/preamble.md` with
`\usepackage{newunicodechar}` declarations. Prefer whichever the BOND render
stage will actually consume; note this package has no PDF stage of its own.
*Command:* `for f in output/manuscript/[0-9][0-9]_*.md; do pandoc "$f" -o "/tmp/$(basename "$f" .md).pdf" || echo "FAIL $f"; done`

**C2 — `docs/_generated/COUNTS.md:36-40` misattributes the third uncovered
branch.** It reads "the max-flow loop's non-exiting back-edge
(`grid_resilience.py:257->281`)". Line 257 is
`while len(visited) < len(order):` inside `most_reliable_path`
(`src/goldeneye/grid_resilience.py:237-293`) — the Dijkstra loop, which always
leaves via the `break` at line 262-263 and so never falls through to line 281.
The max-flow routine is `edge_disjoint_path_count`, which starts at line 294 and
is fully covered. A reader chasing this branch is sent to the wrong algorithm.
*Done when:* the sentence names the Dijkstra loop in `most_reliable_path` and
the line reference resolves to that function.
*Command:* `sed -n '236,240p;256,264p;292,296p' src/goldeneye/grid_resilience.py` — the
cited construct must be the loop that COUNTS.md describes.

### Verification

**V1 — `data/claim_ledger.yaml` is not bound by anything.** 19 claim rows
(134 lines) restate module constants and generated metrics — e.g.
`froehlich-coefficient: 0.607`, `breach-width-arkangel: 164.7`,
`grid-served-fraction: 0.284`. Nothing reads the file: `grep -rn claim_ledger
tests/ scripts/ src/ docs/ AGENTS.md README.md` returns zero hits. The values
happen to match today's run (checked against `output/data/manuscript_variables.json`
this session), but a constant change would leave the ledger silently stale — the
exact failure mode `docs/agent_instructions.md` rule 6 and
`tests/test_manuscript_variables.py::TestModelConstantsAreTokenized` exist to
prevent for the manuscript.
*Done when:* a test loads `data/claim_ledger.yaml` and asserts every
`project_source` / `literature_cited` row equals its named module constant and
every `generated_metric` row equals the corresponding value from
`analyze_arkangel(ARKANGEL)` / `generate_variables()`, and perturbing one ledger
value makes that test fail.
*Command:* `uv run pytest tests/ -k claim_ledger -v` (currently collects 0 tests, which is the bug).

**V2 — Reflection-loss reference values are hand-derived, not page-verified.**
[carried from `output/verify/goldeneye.unresolved.json`] `TestReflectionLoss.TEXTBOOK_DB`
(`tests/test_coupling.py:118-136`) pins copper/aluminium/steel reflection loss to
108/88/106/77 dB. Per the docstring at lines 118-124, these are the widely-quoted
copper-at-1-MHz figure plus hand arithmetic in the independent relative-conductivity
form — no table or page was consulted. The corroboration is genuinely independent
of the implementation (two algebraic routes agreeing to 0.2 dB, pinned at
`tests/test_coupling.py:138-143`), but it is not a citation.
*Done when:* each of the four values is replaced by, or confirmed against, a
value read from a named printed table with page number, and the docstring cites
that locator. If a value disagrees, the pin moves and the manuscript follows.
*Command:* `uv run pytest tests/test_coupling.py::TestReflectionLoss -v` plus a
reviewer confirming the docstring names a page, not "no specific table".
*Do not* re-introduce a locator that was not opened — a fabricated
"Ott 2009, Table 6-4" was already removed once in `2cc0f39`.

**V3 — No gate binds the manuscript to a compiled PDF.**
[carried from unresolved] The `\%` fix from `52d881c` was originally verified
only at the markdown level. This session it was confirmed in an actual compiled
PDF: `pandoc output/manuscript/00_abstract.md output/manuscript/03_results.md
--pdf-engine=xelatex -o /tmp/check.pdf` then `pdftotext` shows `100.0%`, `28.4%`
with no stray backslash. That check was manual and nothing repeats it — the same
render also surfaced C1, which no test catches.
*Done when:* a test (or a documented `scripts/` step) renders the resolved
sections and asserts the extracted text contains a bare `%` after each numeric
token and no `\%` or `\textbackslash`, and the test is skipped-with-reason, not
silently passing, when pandoc is absent.
*Command:* `uv run pytest tests/ -k render -v` (currently collects 0 tests).

**V4 — No negative control on the kill-radius envelope's regime of validity.**
`kill_radius_km` (`src/goldeneye/kill_radius.py:135-`) is bisection on the
conservative point-source envelope; the suite (`tests/test_kill_radius.py`, 30
tests) proves self-consistency, monotonicity, the analytic no-absorption limit,
and the horizon cap — but nothing fails when the envelope is evaluated outside
the regime documented in `manuscript/07_scope_and_related_work.md:13-27`.
*Done when:* a test asserts the model refuses or flags inputs outside the
documented regime, and that test fails if the guard is removed.
*Command:* `uv run pytest tests/test_kill_radius.py -v` after deleting the new
guard — the run must go red.

**V5 — Parallel circuits are exercised only by synthetic test grids.**
`edge_disjoint_path_count` counts parallel circuits separately
(`src/goldeneye/grid_resilience.py:294-`, comment at :306) and
`most_reliable_path` collapses them to the most survivable circuit (:218). The
canonical ARKANGEL grid has no parallel pair — its six lines
(`src/goldeneye/scenario.py:165-170`) span six distinct node pairs, confirmed by
inspection this session. So the scenario-level path never runs, only
`tests/test_grid_resilience.py:198-215`.
*Done when:* either the canonical grid gains a parallel pair (and every affected
token and figure is regenerated), or a scenario-level test asserts the analysis
output is correct for a grid variant that has one.
*Command:* `uv run python -c "import sys; sys.path.insert(0,'src'); from goldeneye.scenario import ARKANGEL; p=[tuple(sorted((l.node_a,l.node_b))) for l in ARKANGEL.grid.lines]; print(len(p)!=len(set(p)))"` → must print `True`, or the scenario test must exist.

### Documentation

**D1 — `docs/architecture.md:97-108` accounts for two uncovered branches; the
run reports three.** The section lists `dam_security.expected_detection_time_min`
(`src/goldeneye/dam_security.py:198`) and
`orbital_mechanics._elevation_from_central_angle_deg`
(`src/goldeneye/orbital_mechanics.py:149`), which is correct. It does not
mention the partial branch `grid_resilience.py:257->281` that the coverage run
reports. Someone reconciling the coverage output against this doc finds an
unexplained residue.
*Done when:* the section explains all three residual sites (including why the
Dijkstra loop's fall-through exit is unreachable), and its count matches the
`Missing` column of the coverage run.
*Command:* `uv run pytest tests/ --cov=src --cov-report=term-missing -q | tail -20` — every
site in the `Missing` column must appear in `docs/architecture.md`.

**D2 — Second opinion wanted on the Ritter rational-factor exemption.**
[carried from unresolved] `docs/agent_instructions.md` rule 6 exempts the exact
rational factors inside the Ritter closed form (`1/9g`, `2/3`,
`manuscript/02_methodology.md:67-75`) from tokenization on the grounds that they
are analytic constants of the solution and cannot drift; only the named module
constant `RITTER_DEPTH_COEFFICIENT` (4/9,
`src/goldeneye/dam_security.py:75`) is tokenized and registered in
`tests/test_manuscript_variables.py:218-233`. The reasoning is stated in both
the rule and the manuscript rather than left implicit, but it is a judgment call
made by the author of the code being audited.
*Done when:* a reviewer who is not the implementer records agreement, or the two
factors become registry entries like every other coefficient.
*Command:* `uv run pytest tests/test_manuscript_variables.py::TestModelConstantsAreTokenized -v`
after adding the entries, if the reviewer disagrees.

### Extension

**E1 — Correlated grid failures.** `resilience_report`
(`src/goldeneye/grid_resilience.py:338-372`) sums each critical load's best-path
reliability, assuming independent asset failures (documented at :343 and in
`manuscript/07_scope_and_related_work.md:49-52`). A shared-corridor or
common-mode-field variant would materially change the served fraction. Scoped,
not started. *Done when:* a correlated variant exists alongside the independent
one and the manuscript reports both.

**E2 — Friction-aware flood routing.** `station_inundation_table`
(`src/goldeneye/breach_hydrograph.py:135-`) uses the frictionless Ritter front
speed and the asymptotic depth `4H/9`, so arrival times are lower bounds
(`manuscript/07_scope_and_related_work.md:29-36`). A routing step with bed
friction would turn them into estimates. *Done when:* the station table reports
a routed arrival time and the manuscript stops calling it a lower bound.

**E3 — Source `E2_AMPLITUDE_FRACTION`.** `src/goldeneye/emp_model.py:103` sets
it to 0.05 as an engineering default; IEC 61000-2-9 specifies E1 most strictly
and does not fix this. *Done when:* a sourced value replaces the constant with a
citation, or the manuscript states explicitly that no standard value exists.

**E4 — Non-zenith pass geometry.** `overhead_pass_duration_s`
(`src/goldeneye/orbital_mechanics.py:224-234`) assumes a directly-overhead pass,
so durations are upper bounds (docstring at :225-231). A general ground-track
pass needs the platform inclination and the target's cross-track offset.
*Done when:* the function accepts an off-track offset and the canonical value
comes from the real ARKANGEL geometry.

---

## Known limitations (not bugs)

- **Two defensive branches stay uncovered on purpose.**
  `dam_security.py:198` and `orbital_mechanics.py:149` are zero-divide guards
  unreachable through the public API given invariants that are themselves pinned
  by tests (`SecurityLayer`'s probability range; `central_angle_deg`'s clamp).
  Deleting them to reach 100% would turn a future invariant change into a silent
  zero-divide. Commented at the call sites and listed in `docs/architecture.md`.
  The third residual site (`grid_resilience.py:257->281`) is the same species —
  see D1 for the bookkeeping fix, not a coverage fix.
- **The `bond_api` MissionProvider surface is frozen.** Class name, `film` slug,
  the five method signatures, and the module-level `GADGETS` name are consumed
  across every BOND package. Depth goes inside the package, never into the
  surface (`docs/architecture.md:57-76`, `docs/agent_instructions.md` rule 7).
- **The pure-core isolation test proves "never imports", not "runs where
  absent".** [scope softened after audit] `tests/test_mission.py::TestPureCoreWithoutBondApi`
  installs a `sys.meta_path` finder that raises on any `bond_api`/`bond_utilities`
  import, with a positive control that the blocker fires and a companion negative
  control that `goldeneye.mission` fails under it. The packages remain installed
  in the environment. `AGENTS.md:26-28` states this scope explicitly; earlier
  wording that claimed the packages were "removed" was wrong and is gone.
- **The reflection-loss reference values carry no page citation.** [scope
  softened after audit] See V2. The corroboration is real and independent; the
  claim is deliberately worded as "the well-known copper figure plus hand
  arithmetic", not as a table lookup. Removing that honesty to look tidier would
  be a regression.
- **`GAMMA_YIELD_FRACTION` is documented provenance, not a model input.** It is
  reported in the recon payload and tokenized, but no envelope function reads
  it; `tests/test_emp_model.py::TestGammaFractionIsReportedNotConsumed` proves
  perturbing it changes no computed field, and both
  `manuscript/02_methodology.md:20-25` and `05_experimental_setup.md:35-37` say
  so. Do not "wire it in" — the envelope has no Compton source term.
- **The envelope, thresholds, Froehlich regressions and Ritter solution are
  engineering approximations**, each with its scope stated in
  `manuscript/07_scope_and_related_work.md`. This is mission software, not a
  predictive defence-physics code.
- **This package has no PDF stage.** `scripts/z_generate_manuscript_variables.py`
  resolves tokens into `output/manuscript/`; rendering belongs to the suite. C1
  and V3 are about not shipping markdown that a renderer cannot consume, not
  about adding a render stage here.
- **Tracked at `github.com/docxology/bond-goldeneye` (`origin`, branch `main`).**
  Commit path-scoped inside this repo only (`docs/agent_instructions.md` rule 1),
  and never force-push or rewrite history.

---

## Verification

All five must pass before any change is done. Expected outcomes are what was
measured on `2cc0f39`, 2026-08-05.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
# → 325 passed, 99.65% line+branch, "Required test coverage of 90% reached"

uv run ruff check src/ scripts/ tests/
# → All checks passed!

uv run ruff format --check src/ scripts/ tests/
# → 46 files already formatted

uv run mypy src/ scripts/
# → Success: no issues found in 23 source files

rg -rn "unittest[.]mock|MagicMock|@patch|create_autospec" tests/ || echo Clean
rg -n "template_code_project" . --glob '!uv.lock' --glob '!.git/**' \
   --glob '!output/**' --glob '!.venv/**' || echo Clean
# → both print Clean
```

Regenerate artifacts after any change to the public surface or the scenario
defaults, then refresh `docs/_generated/COUNTS.md` from the real run:

```bash
uv run python scripts/execute.py
uv run python scripts/z_generate_manuscript_variables.py
```
