# Agent Instructions (read first)

GoldenEye: ARKANGEL — BOND film package. These are hard constraints, not
suggestions. Read this file before modifying any project file.

## Rules

1. **Scope = `projects/working/bond/goldeneye/` exactly.** Never touch sibling
   packages, bond root files, or the template repo. This is a local-only tree;
   there is no remote and it must never be pushed.

2. **Pure core stays pure.** All seven concept modules — `emp_model.py`,
   `orbital_mechanics.py`, `kill_radius.py`, `coupling.py`,
   `grid_resilience.py`, `dam_security.py`, `breach_hydrograph.py` — plus their
   composition in `scenario.py` must not import `bond_api`, `bond_utilities`,
   or any BOND layer; they must be importable in any Python environment.
   `src/goldeneye/mission.py` is the single allowed `bond_api` adapter. Verify
   with `rg -n "^(from|import) (bond_|infrastructure)" src/goldeneye/`, and note
   that `tests/test_mission.py::TestPureCoreWithoutBondApi` proves it in a
   subprocess.

3. **Thin orchestrators.** `scripts/` coordinate; they never implement math.
   Business logic lives in `src/goldeneye/`.

4. **No mock framework.** No `Magic[M]ock`, `mocker.patch`, `unittest[.]mock` in
   tests. Real data + closed-form computation only. Verify:
   `rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo Clean`.

5. **Deterministic.** Fixed scenario parameters (declared in
   `manuscript/config.yaml`), a fixed seed of 0, no untracked RNG, and no
   wall-clock value in any artifact covered by the byte-identity claim in
   `manuscript/06_reproducibility.md` (the outcome JSON, the token map, the
   resolved sections, the figures). Never call `datetime.now`, `utcnow`, or
   `time.time` in `manuscript_variables.py` or anything it reaches — a
   generation timestamp makes every regeneration differ, which is exactly the
   breach that `tests/test_reproducibility.py` now catches by regenerating the
   covered set twice and comparing bytes. Real timestamps belong only in the
   run-scoped provenance record `output/data/arkangel_mission.json`, which the
   claim explicitly excludes.

6. **Manuscript tokens.** Every number in prose — result, model constant, or
   scenario input — uses a `{{TOKEN}}` from `generate_variables()`. Never
   hand-author a metric. To state a new quantity, add the variable to
   `src/goldeneye/manuscript_variables.py` first, then reference the token. The
   live cross-reference test in `tests/test_manuscript_variables.py` fails on
   any numbered-section token missing from the map, and strict mode refuses a
   map containing a non-finite number. Do not put literal double-brace examples
   inside numbered `NN_*.md` sections. Model constants belong to the module that
   defines them: tokenize them rather than retyping the value in prose, so a
   constant change cannot leave the manuscript stale. This is now enforced, not
   advisory — `tests/test_manuscript_variables.py::TestModelConstantsAreTokenized`
   holds a registry of empirical model constants and fails if any registered
   token is missing from the map, is never referenced in prose, or has its
   literal value retyped into a section. Adding a new empirical coefficient
   means adding it to that registry too. The exception, stated explicitly: exact
   rational factors internal to a closed-form solution (Ritter's `1/9g`, `2/3`)
   are not model constants — they cannot change, so there is nothing to keep in
   sync. Anything a future edit could plausibly retune is a model constant.

7. **Frozen protocol.** `src/goldeneye/mission.py` implements the frozen
   `bond_api.MissionProvider` surface verbatim. Do not invent your own protocol
   types; do not change the class name, the `film` slug, the five method
   signatures, or the module-level `GADGETS` name. bond-cli, the coordinator
   reconcile and the orchestrator consume all of these across packages. Deepen
   *inside* the package — new pure-core modules, richer `execute` internals,
   additional gadget entries — never by reshaping the surface.
   `docs/architecture.md` has the row-by-row contract.

8. **Gates before done.** Run all of: pytest `--cov-fail-under=90`, `ruff
   check`, `ruff format --check`, `mypy` on `src/`+`scripts/`, zero-mock audit,
   and lineage `rg template[_]code_project` (aim zero). Commit path-scoped inside
   this repo only.

## Before submitting

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo "Clean"
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo "Clean"
```
