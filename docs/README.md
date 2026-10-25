# docs/

Agent-facing rulebook for the **GoldenEye: ARKANGEL** BOND film package. These
documents are hard constraints for anyone — human or agent — changing this
package. They describe *this* package specifically; none of it is exemplar
boilerplate.

## What is in here

| File | Read it when | Contains |
| --- | --- | --- |
| `agent_instructions.md` | **First, always** — before touching any file. | The eight hard rules: scope, pure-core purity, thin orchestrators, zero mocks, determinism, manuscript tokens, the frozen protocol, and the gates that must pass before you call anything done. |
| `architecture.md` | Before changing a `src/` or `scripts/` boundary, or adding a module. | The layer topology; a per-module table of what each of the seven pure-core modules computes and what it imports; how `mission.py` implements the frozen `bond_api` MissionProvider surface row by row; dependency rules; forbidden patterns; the three deliberately unreachable branches. |
| `testing_philosophy.md` | Before writing or editing any test. | The zero-mock policy and why substitution is pointless here; determinism guarantees; the "gates must be falsifiable" convention and its positive controls; a per-file table of what each of the fourteen test files covers. |
| `AGENTS.md` | For the file inventory and the quick audits. | This directory's index, the read-first protocol, and the three one-line verification commands. |
| `_generated/COUNTS.md` | To quote a test count or coverage figure. | Live measured totals from the last full run. **Generated — never hand-edit, and never hardcode these numbers anywhere else.** |

## The short version

The package is a deterministic, closed-form model of the coupled threat surfaces
of *GoldenEye* (1995): an orbital EMP weapon and its Keplerian platform, the
electronics kill radius it imposes, how the field couples past shielding, what
the regional power network retains, and the Arkangel dam's access control and
breach flood. Seven pure-core modules do the mathematics and import nothing from
the BOND suite. One thin adapter (`src/goldeneye/mission.py`) implements the
frozen protocol. Scripts orchestrate and never compute.

Three mistakes account for nearly every failed change here: importing a BOND
layer into the pure core, hand-authoring a metric in the manuscript instead of
adding a token, and altering the frozen MissionProvider shape.
`agent_instructions.md` covers all three.

## Verification

```bash
# run from the repository root
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```
