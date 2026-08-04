# scripts/ — Conventions

- **Thin only**: no business logic, no math, no scenario construction in a
  script. Import from `src/goldeneye/`.
- **Bootstrap**: each script inserts `PROJECT_ROOT` and `PROJECT_ROOT/src` into
  `sys.path` immediately after the stdlib imports; downstream imports carry
  `# noqa: E402` (ruff E402 does not auto-cover 4-level-deep BOND script paths).
- **Exit codes**: `0` success; `1` explicit error; `2` argparse usage error.
- **Determinism**: no RNG, no `datetime.now()` in a script — defer to the core.
- **Artifacts**: write only under `output/` (gitignored).
- **Style**: type hints + docstrings on every function; match `ruff format`.
