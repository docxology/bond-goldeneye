# STYLE

Source style for `src/goldeneye/`:

1. **Type hints + docstrings** on every public function and dataclass.
2. **Ruff formatting** (88-col default alignment) — `uv run ruff format`.
3. **Deterministic math**: prefer `math.*` in the pure core; numpy/matplotlib
   only in `figures/` and `manuscript_variables.py`.
4. **Named constants**: physical/engineering constants are module-level
   `UPPER_SNAKE` with a docstring note on provenance.
5. **Validation**: frozen dataclasses raise `ValueError` with actionable
   messages in `__post_init__`; guard invalid inputs at the boundary.
6. **No BOND imports** outside `mission.py`.
