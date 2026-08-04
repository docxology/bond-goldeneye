# docs/ — Agent-facing documentation

Technical guide for `projects/working/bond/goldeneye/docs/`. Every document is
a hard constraint for agents working in this package.

## File inventory

| File | Purpose |
| --- | --- |
| `README.md` | Navigation + entry points |
| `AGENTS.md` | This index |
| `agent_instructions.md` | Read-first behavioral rules (scope, purity, mocks, determinism, tokens, gates) |
| `architecture.md` | Layer boundaries, dependency rules, forbidden patterns |
| `testing_philosophy.md` | Zero-mock policy, coverage mechanics, test-file inventory |
| `_generated/COUNTS.md` | Live test count + measured coverage (generated, not hand-edited) |

## Read-first protocol

Start with `agent_instructions.md`. Skipping it is the most common source of
errors: importing a BOND layer into the pure core, writing math in `scripts/`,
introducing a mock, or hardcoding a manuscript metric.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
rg -rn "unittest[.]mock|Magic[M]ock|@pat[ch]|create_auto[s]pec" tests/ || echo Clean
rg -n "^(from|import) (bond_|infrastructure)" src/goldeneye/ || echo Clean
```
