# Experimental setup

## Scenario parameters

All parameters are declared in `manuscript/config.yaml` and loaded by
`src/goldeneye/scenario.py::load_scenario_config`. The canonical ARKANGEL
mission uses:

| Parameter | Value |
|---|---|
| Weapon yield | **{{GE_YIELD_KT}}** kt |
| Burst altitude | **{{GE_BURST_ALTITUDE_KM}}** km |
| Reservoir volume | **{{GE_RESERVOIR_VOLUME_M3}}** m^3 |
| Dam head | **{{GE_DAM_HEAD_M}}** m |
| Facility downstream distance | **{{GE_FACILITY_DISTANCE_KM}}** km |
| Access-control layers | **{{GE_NUM_LAYERS}}** |

The EMP envelope constants (reference amplitude **{{GE_NADIR_FIELD_VM}}** anchored
to a 50 kV/m megaton-class reference, 0.3% prompt-gamma fraction, empirical
yield exponent) are fixed in `src/goldeneye/emp_model.py`; the four
vulnerability-class thresholds are fixed in `src/goldeneye/kill_radius.py`.

## Software environment

The package is tested under Python **{{PYTHON_VERSION}}** with NumPy
**{{NUMPY_VERSION}}** and matplotlib; bond-api and bond-utilities are installed as
local path dependencies. Execution environment snapshot was generated at
**{{GENERATION_TIMESTAMP}}**.

## Verification gates

The enforced gates are `uv run pytest tests/ --cov=src --cov-fail-under=90`
(line and branch), `uv run ruff check` and `uv run ruff format`, `uv run mypy
src/ scripts/`, a zero-mock audit of `tests/`, and a live cross-reference test
that every manuscript token (the double-brace variables in the numbered
sections) is produced by `generate_variables()`.
