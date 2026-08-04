# Agent Instructions (read first)

GoldenEye: ARKANGEL — BOND film package. These are hard constraints, not
suggestions. Read this file before modifying any project file.

## Rules

1. **Scope = `projects/working/bond/goldeneye/` exactly.** Never touch sibling
   packages, bond root files, or the template repo. This is a local-only tree;
   there is no remote and it must never be pushed.

2. **Pure core stays pure.** `src/goldeneye/emp_model.py`, `kill_radius.py`,
   `dam_security.py`, and `scenario.py` must not import `bond_api`,
   `bond_utilities`, or any BOND layer — they must be importable in any Python
   environment. `src/goldeneye/mission.py` is the single allowed `bond_api`
   adapter. Verify with `rg -n "^(from|import) (bond_|infrastructure)" src/goldeneye/`.

3. **Thin orchestrators.** `scripts/` coordinate; they never implement math.
   Business logic lives in `src/goldeneye/`.

4. **No mock framework.** No `Magic[M]ock`, `mocker.patch`, `unittest[.]mock` in
   tests. Real data + closed-form computation only. Verify:
   `rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo Clean`.

5. **Deterministic.** Fixed scenario parameters (declared in
   `manuscript/config.yaml`), a fixed seed of 0, no untracked RNG, and no
   wall-clock value in persisted analysis artifacts. Two runs of
   `analyze_arkangel(ARKANGEL)` must be byte-identical (tested).

6. **Manuscript tokens.** Every numeric result in prose uses a
   `{{TOKEN}}` from `generate_variables()`; never hand-author metrics. The
   live cross-reference test in `tests/test_manuscript_variables.py` fails on
   any numbered-section token missing from the map. Do not put literal
   double-brace examples inside numbered `NN_*.md` sections.

7. **Frozen protocol.** `src/goldeneye/mission.py` implements the frozen
   `bond_api.MissionProvider` surface verbatim. Do not invent your own protocol
   types; do not change the class name or the five method signatures.

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
