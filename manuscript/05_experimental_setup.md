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

The orbital-platform geometry (burst nadir at
**{{GE_ORBIT_NADIR_LAT_DEG}}**° N, **{{GE_ORBIT_NADIR_LON_DEG}}**° E; target at
**{{GE_ORBIT_TARGET_LAT_DEG}}**° N; platform altitude
**{{GE_ORBIT_ALTITUDE_KM}}** km; minimum usable elevation
**{{GE_ORBIT_MIN_ELEVATION_DEG}}**°), the coupling inputs
(**{{GE_COUPLING_CONDUCTOR_LENGTH_M}}** m conductor,
**{{GE_COUPLING_SHIELD_THICKNESS_MM}}** mm **{{GE_COUPLING_SHIELD_MATERIAL}}**
enclosure, **{{GE_COUPLING_FREQUENCY_MHZ}}** MHz reference frequency,
**{{GE_COUPLING_IMPEDANCE_OHM}}** Ohm load), the canonical
**{{GE_GRID_NUM_NODES}}**-node regional grid, and the
**{{GE_NUM_STATIONS}}** downstream stations are declared in
`manuscript/config.yaml` (the `orbit` and `coupling` blocks) and
`src/goldeneye/scenario.py` (the grid and stations).

The EMP envelope constants are fixed in `src/goldeneye/emp_model.py`: an
amplitude anchor of **{{GE_E1_REFERENCE_VM}}** V/m at the
**{{GE_REFERENCE_YIELD_KT}}** kt reference yield, a
**{{GE_GAMMA_FRACTION_PCT}}**\% prompt-gamma fraction, and an empirical yield
exponent of **{{GE_YIELD_EXPONENT}}**. (The **{{GE_NADIR_FIELD_VM}}** V/m nadir
field reported in the results is *computed* from those constants at the
scenario yield, not itself a constant.) The **{{GE_NUM_CLASSES}}**
vulnerability-class thresholds are fixed in `src/goldeneye/kill_radius.py`,
and the **{{GE_MILITARY_WITHSTAND_VM}}** V/m military withstand level used for
the protection margin is declared in `src/goldeneye/scenario.py`.

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
