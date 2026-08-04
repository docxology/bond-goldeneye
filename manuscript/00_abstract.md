# Abstract

**GoldenEye: ARKANGEL** (film identity **{{GE_IDENTITY}}**, mission codename
**{{GE_CODENAME}}**) is a deterministic special-agent mission software package that
models three coupled threat surfaces from the 1995 film *GoldenEye*: an orbital
electromagnetic-pulse (EMP) weapon, the electronics kill-radius it imposes on
surface assets, and the security and breach-flood risk of the Arkangel dam
facility.

The threat envelope is a documented conservative point-source model of a
high-altitude nuclear burst (**{{GE_YIELD_KT}}** kt at **{{GE_BURST_ALTITUDE_KM}}** km),
producing a nadir early-time field of **{{GE_NADIR_FIELD_VM}}** V/m across a
line-of-sight footprint of radius **{{GE_HORIZON_RANGE_KM}}** km
(**{{GE_HORIZON_AREA_KM2}}** km^2). Four electronics vulnerability classes
(**{{GE_NUM_CLASSES}}** in total: **{{GE_CLASS_NAMES}}**) are assessed: unprotected
microelectronics are destroyed over essentially the entire visible footprint
(**{{GE_RADIUS_UNPROTECTED_KM}}** km, **{{GE_FRACTION_UNPROTECTED}}**\% of it), while
MIL-STD-188-125-hardened and legacy vacuum-tube electronics require ever-higher
fields and survive to within **{{GE_RADIUS_MILITARY_KM}}** km of the burst or are
immune (**{{GE_RADIUS_LEGACY_TUBE_KM}}** km).

For the Arkangel dam, the report combines the published Froehlich (1995)
breach-outflow regression with the Ritter (1892) instantaneous dam-break
solution. Given a reservoir of **{{GE_RESERVOIR_VOLUME_M3}}** m^3 behind a
**{{GE_DAM_HEAD_M}}** m head, peak outflow reaches **{{GE_PEAK_DISCHARGE_CMS}}** m^3/s
with a wave front moving at **{{GE_FRONT_SPEED_MS}}** m/s; the facility
**{{GE_FACILITY_DISTANCE_KM}}** km downstream faces a **{{GE_FLOOD_DEPTH_M}}** m peak
inundation within **{{GE_FLOOD_ARRIVAL_MIN}}** min — an overall **{{GE_FLOOD_RISK}}**
risk. Defense-in-depth access control yields a **{{GE_ACCESS_DETECT_PROB}}**
detection probability and a **{{GE_SECURITY_SCORE}}** composite security score.

All results are closed-form, deterministic, and regenerable from source;
figures, data, and manuscript variables are produced by thin orchestration
scripts under `scripts/`.
