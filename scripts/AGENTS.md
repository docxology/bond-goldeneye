# scripts/ — Thin orchestrators

One thin CLI per ARKANGEL mission phase, plus the manuscript-variable hydrator.
Scripts coordinate business logic in `src/goldeneye/`; they never implement
math. Each self-inserts the package `src/` onto `sys.path` so `uv run python
scripts/<name>.py` works from the package root.

| Script | Mission phase | Behavior |
| --- | --- | --- |
| `brief.py` | 1/5 BRIEF | Prints the frozen `MissionBrief` |
| `recon.py [goal]` | 2/5 RECON | Runs `recon(ReconRequest(goal))`, prints findings |
| `plan.py` | 3/5 PLAN | Prints the deterministic `MissionPlan` steps |
| `execute.py` | 4/5 EXECUTE | Runs the analysis, persists outcome + provenance to `output/data/` |
| `debrief.py` | 5/5 DEBRIEF | Loads the persisted outcome, prints lessons |
| `z_generate_manuscript_variables.py` | hydration | Writes variables JSON, renders figures, resolves sections into `output/manuscript/` |

## Conventions

- Exit code 0 on success; `argparse` errors exit 2; `debrief.py` exits 1 when
  the outcome artifact is absent (guidance points to `execute.py`).
- `execute.py` persists via `bond_api.serialization.to_json` and
  `bond_utilities.mission_io.record_provenance_outcome`.
- `z_generate_manuscript_variables.py` is strict by default (unresolved tokens
  or empty analysis fail); `--allow-draft` relaxes.
- All artifacts land under `output/` (gitignored, regenerable).

See `CONVENTIONS.md` for the shell/format conventions.
