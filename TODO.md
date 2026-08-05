# TODO — goldeneye (ARKANGEL)

`goldeneye` is the BOND-suite film package for *GoldenEye* (1995), mission
codename **ARKANGEL**. It models the film's coupled threat surfaces as
deterministic closed-form physics across seven pure-core modules (orbital EMP
weapon and platform, electronics kill radius, EM coupling and shielding,
regional grid resilience, dam access control, breach hydrograph), composed by
`scenario.py` and exposed to the suite through the frozen
`bond_api.MissionProvider` adapter in `src/goldeneye/mission.py`.

**Verified state, measured 2026-08-05 on `2cc0f39`:** `uv run pytest tests/
--cov=src --cov-fail-under=90` → **325 passed, 0 failed, 0 skipped, 99.65%
line+branch coverage** of `src/` (2 statements, 3 branches uncovered). `ruff
check`, `ruff format --check` (46 files), and `mypy src/ scripts/` (23 files)
are all clean; the zero-mock and lineage greps return nothing. All ten findings
in `output/verify/goldeneye.json` were re-checked against the tree this session
and are fixed at source — the open work below is what remains after them.

Live counts live in `docs/_generated/COUNTS.md`; do not retype them elsewhere.

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
- **Local-only tree.** No remote; never push. Commit path-scoped inside this
  repo only (`docs/agent_instructions.md` rule 1).

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
