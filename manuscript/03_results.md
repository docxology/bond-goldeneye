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

## Orbital platform

The weapon rides a circular orbit of radius **{{GE_ORBIT_RADIUS_KM}}** km
(**{{GE_ORBIT_ALTITUDE_KM}}** km altitude) with a period of
**{{GE_ORBIT_PERIOD_MIN}}** min and speed **{{GE_ORBIT_SPEED_KMS}}** km/s. From the
target, the platform stands at a **{{GE_ORBIT_ELEVATION_DEG}}**-degree elevation
over a **{{GE_ORBIT_CENTRAL_ANGLE_DEG}}**-degree central angle
(**{{GE_ORBIT_SLANT_RANGE_KM}}** km slant range) and remains above a
**{{GE_ORBIT_PASS_DURATION_MIN}}**-minute usable pass — the detonation window.

## Coupling and shielding

At the facility the envelope field reaches **{{GE_COUPLING_FACILITY_FIELD_VM}}**
V/m. A **{{GE_COUPLING_EFFECTIVE_HEIGHT_M}}** m effective antenna couples
**{{GE_COUPLING_INDUCED_V}}** V (≈**{{GE_COUPLING_CONDUCTED_A}}** A into a
**{{GE_COUPLING_IMPEDANCE_OHM}}** Ohm load) — a kilovolt-class conducted threat.
In contrast, the skin depth at the representative
**{{GE_COUPLING_FREQUENCY_MHZ}}** MHz E1 frequency is only
**{{GE_COUPLING_SKIN_DEPTH_MM}}** mm in the
**{{GE_COUPLING_SHIELD_MATERIAL}}** shield; a
**{{GE_COUPLING_SHIELD_THICKNESS_MM}}** mm enclosure provides
**{{GE_COUPLING_SE_DB}}** dB of
shielding, reducing the penetrated field to **{{GE_COUPLING_SHIELDED_FIELD_VM}}**
V/m and leaving a **{{GE_COUPLING_MARGIN_DB}}** dB protection margin against the
military withstand level.

## Regional power-network resilience

![Regional grid resilience](output/figures/grid_resilience.png){#fig:grid_resilience width=100%}

The **{{GE_GRID_NUM_NODES}}**-node, **{{GE_GRID_NUM_LINES}}**-line regional network
loses the nodes **{{GE_GRID_DOWN_NODES}}** to certain failure. It serves an
expected **{{GE_GRID_EXPECTED_SERVED_MW}}** MW of the
**{{GE_GRID_TOTAL_CRITICAL_MW}}** MW critical load (**{{GE_GRID_SERVED_FRACTION}}**\\%),
with a worst-case load reliability of **{{GE_GRID_MIN_RELIABILITY}}** and a
minimum of **{{GE_GRID_MIN_DISJOINT_PATHS}}** redundant routes per critical load.
The mission-critical facility keeps a **{{GE_FACILITY_RELIABILITY}}** survival
probability over **{{GE_FACILITY_DISJOINT_PATHS}}** edge-disjoint paths — the
hardened hydro source and a redundant interconnection are what keep it on the
board.

## Breach outflow hydrograph

A breach **{{GE_BREACH_WIDTH_M}}** m wide releases the reservoir as a
volume-conserving triangular hydrograph lasting **{{GE_HYDROGRAPH_DURATION_MIN}}**
min at a mean outflow of **{{GE_MEAN_OUTFLOW_CMS}}** m^3/s. The flood sweeps all
**{{GE_NUM_STATIONS}}** monitored stations; the farthest,
**{{GE_FARTHEST_STATION_KM}}** km downstream, is reached in
**{{GE_FARTHEST_ARRIVAL_MIN}}** min.
