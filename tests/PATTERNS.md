# tests/ — patterns

- **Real data, no mocks**: assert exact known vectors (e.g. `4H/9` Ritter dam
  site depth, `test_dam_security.py::TestRitterWave`), analytic limits (kill
  radius `h*sqrt(E0_ys/T - 1)` in the no-absorption regime,
  `test_kill_radius.py::TestKillRadius::test_analytic_no_absorption_limit`),
  and determinism (byte-identical two-run,
  `test_scenario.py::TestAnalysis::test_analysis_is_deterministic`).
- **Boundary/error branches**: every `ValueError`/`KeyError` path is exercised
  (e.g. `test_emp_model.py::TestWaveform::test_unknown_component_raises`,
  `test_dam_security.py::TestAccessControl::test_layer_validation`).
- **Subprocess isolation**: the pure-core-without-`bond_api` gate and CLI smoke
  run real subprocesses with `sys.executable` (venv python) and `cwd` at the
  package root; asserts `'bond_api' not in sys.modules` after importing the
  pure core.
- **Figures**: render to `tmp_path` real PNGs and assert the PNG magic header
  and a minimum size.
- **Manuscript**: the live cross-reference test scans `manuscript/[0-9][0-9]_*.md`
  only, so literal double-brace examples in guide files are safe.
