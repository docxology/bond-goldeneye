# Results

Run via the ARKANGEL mission software against the canonical scenario
(`scripts/execute.py`), all figures and values below are the deterministic
output of the pure domain core.

## EMP threat envelope

For the canonical weapon (**{{GE_YIELD_KT}}** kt at **{{GE_BURST_ALTITUDE_KM}}** km),
the E1 peak field directly under the burst is **{{GE_NADIR_FIELD_VM}}** V/m. The
illuminated footprint is bounded by the geometric horizon at
**{{GE_HORIZON_RANGE_KM}}** km radius, an area of **{{GE_HORIZON_AREA_KM2}}** km^2.
Because the prompt-flux absorption is negligible along the vacuum path at this
altitude, the field decays with the squared geometric projection $\sin^2\psi$
across the footprint.

![EMP threat envelope and kill radii](output/figures/emp_footprint.png){#fig:emp_footprint width=100%}

## Kill radius by vulnerability class

Across the **{{GE_NUM_CLASSES}}** vulnerability classes
(**{{GE_CLASS_NAMES}}**), kill radii span the full spectrum of the footprint:

| Class | Kill radius (km) |
|---|---|
| Unprotected microelectronics | **{{GE_RADIUS_UNPROTECTED_KM}}** |
| Commercial / semi-hardened | **{{GE_RADIUS_COMMERCIAL_KM}}** |
| MIL-STD-188-125 hardened | **{{GE_RADIUS_MILITARY_KM}}** |
| Legacy vacuum-tube / relay | **{{GE_RADIUS_LEGACY_TUBE_KM}}** |

Unprotected microelectronics are destroyed over essentially the entire visible
footprint (**{{GE_FRACTION_UNPROTECTED}}**\% of it); hardened facilities retain a
modest survival zone; legacy vacuum-tube electronics, with their
**{{GE_RADIUS_LEGACY_TUBE_KM}}** km radius, are immune at every realistic range in
this scenario — a direct consequence of their orders-of-magnitude higher
threshold. The figure above shows how these radii trade off against burst
altitude and yield, and the damage-probability transition for each class.

## Arkangel dam breach flood

Given a reservoir of **{{GE_RESERVOIR_VOLUME_M3}}** m^3 behind a
**{{GE_DAM_HEAD_M}}** m head, the Froehlich (1995) regression gives a peak breach
outflow of **{{GE_PEAK_DISCHARGE_CMS}}** m^3/s. The Ritter wave front advances at
**{{GE_FRONT_SPEED_MS}}** m/s, reaching the facility **{{GE_FACILITY_DISTANCE_KM}}** km
downstream in **{{GE_FLOOD_ARRIVAL_MIN}}** min with an asymptotic peak inundation
of **{{GE_FLOOD_DEPTH_M}}** m — a severity ratio of **{{GE_FLOOD_SEVERITY}}** against
the facility elevation, rated **{{GE_FLOOD_RISK}}**.

![Ritter dam-break flood wave](output/figures/flood_wave.png){#fig:flood_wave width=100%}

## Access-control posture

The **{{GE_NUM_LAYERS}}** layered defense-in-depth cascade yields a
**{{GE_ACCESS_DETECT_PROB}}** probability of detecting an intruder at least once,
an expected response time of **{{GE_ACCESS_EXPECTED_TIME_MIN}}** min, and a
composite security score of **{{GE_SECURITY_SCORE}}** (out of 100).
