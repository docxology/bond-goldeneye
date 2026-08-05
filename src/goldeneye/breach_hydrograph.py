"""Dam-breach outflow hydrograph and downstream inundation stations.

Extends the Arkangel breach-flood model (:mod:`goldeneye.dam_security`) with
the time dimension of the flood:

* **Average breach width** — the Froehlich (2008) embankment-dam regression
  ``B_avg = 0.27 * K0 * V^0.32 * H^0.04`` (``K0 = 1.4`` for overtopping,
  ``1.0`` for piping failure);
* **Triangular outflow hydrograph** — a volume-conserving linear recession
  from the peak outflow (Froehlich 1995, see ``dam_security``) to zero over
  ``t_d = 2V/Q_p``, so the area under the hydrograph equals the released
  volume;
* **Downstream station table** — arrival time (Ritter front speed), asymptotic
  peak depth (``4H/9``), and flood-risk rating at each named station.

Sources: Froehlich, D.C. (2008), "Embankment dam breach parameters and their
uncertainties," *Journal of Hydraulic Engineering* 134(12). All functions are
closed-form and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from goldeneye.dam_security import (
    breach_peak_discharge_cms,
    flood_arrival_time_s,
    flood_risk_rating,
    peak_depth_at_distance_m,
)

__all__ = [
    "FROEHLICH_OVERTTOPING_FACTOR",
    "FROEHLICH_PIPING_FACTOR",
    "Station",
    "breach_average_width_m",
    "breach_hydrograph_report",
    "hydrograph_duration_s",
    "mean_outflow_cms",
    "station_inundation_table",
    "triangular_hydrograph",
]

#: Froehlich (2008) breach-width factors: overtopping vs piping failure.
FROEHLICH_OVERTTOPING_FACTOR = 1.4
FROEHLICH_PIPING_FACTOR = 1.0


@dataclass(frozen=True)
class Station:
    """A downstream inundation station.

    Attributes:
        name: Station identifier.
        distance_km: Distance downstream of the dam (km, > 0).
        elevation_m: Ground elevation above the riverbed (m, > 0).
    """

    name: str
    distance_km: float
    elevation_m: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Station.name must be non-empty")
        if self.distance_km <= 0:
            raise ValueError(f"distance_km must be > 0, got {self.distance_km!r}")
        if self.elevation_m <= 0:
            raise ValueError(f"elevation_m must be > 0, got {self.elevation_m!r}")


def breach_average_width_m(volume_m3: float, head_m: float, overtopping: bool = True) -> float:
    """Average breach width (m) — Froehlich (2008):
    ``B_avg = 0.27 * K0 * V^0.32 * H^0.04``."""
    if volume_m3 <= 0 or head_m <= 0:
        raise ValueError("volume_m3 and head_m must both be > 0")
    k0 = FROEHLICH_OVERTTOPING_FACTOR if overtopping else FROEHLICH_PIPING_FACTOR
    return float(0.27 * k0 * float(volume_m3) ** 0.32 * float(head_m) ** 0.04)


def hydrograph_duration_s(volume_m3: float, peak_q_cms: float) -> float:
    """Triangular-hydrograph duration (s): ``t_d = 2V / Q_p`` — chosen so the
    triangle's area (``0.5 * Q_p * t_d``) equals the released volume."""
    if volume_m3 <= 0 or peak_q_cms <= 0:
        raise ValueError("volume_m3 and peak_q_cms must both be > 0")
    return float(2.0 * float(volume_m3) / float(peak_q_cms))


def mean_outflow_cms(volume_m3: float, duration_s: float) -> float:
    """Mean outflow (m^3/s) over the hydrograph: ``V / t_d``."""
    if volume_m3 <= 0 or duration_s <= 0:
        raise ValueError("volume_m3 and duration_s must both be > 0")
    return float(volume_m3) / float(duration_s)


def triangular_hydrograph(
    volume_m3: float,
    peak_q_cms: float,
    n_steps: int,
) -> tuple[tuple[float, float], ...]:
    """(time_s, discharge_cms) samples of the volume-conserving triangular
    hydrograph: ``Q(t) = Q_p * (1 - t/t_d)`` on ``[0, t_d]``.

    ``n_steps`` interior points (>= 1); the endpoints are always included.
    """
    if n_steps < 1:
        raise ValueError(f"n_steps must be >= 1, got {n_steps!r}")
    t_d = hydrograph_duration_s(volume_m3, peak_q_cms)
    times = [0.0]
    times.extend(t_d * i / (n_steps + 1) for i in range(1, n_steps + 1))
    times.append(t_d)
    return tuple((t, peak_q_cms * (1.0 - t / t_d)) for t in times)


def station_inundation_table(
    head_m: float,
    stations: tuple[Station, ...],
) -> tuple[dict[str, Any], ...]:
    """Downstream inundation rows: arrival (min), peak depth (m), risk rating.

    Arrival uses the Ritter front speed ``2*sqrt(g*H)``; peak depth is the
    asymptotic ``4H/9`` plateau (both from :mod:`goldeneye.dam_security`).
    """
    rows: list[dict[str, Any]] = []
    for station in stations:
        distance_m = station.distance_km * 1000.0
        arrival_s = flood_arrival_time_s(distance_m, head_m)
        depth_m = peak_depth_at_distance_m(distance_m, head_m)
        rows.append(
            {
                "name": station.name,
                "distance_km": station.distance_km,
                "arrival_time_s": arrival_s,
                "arrival_time_min": arrival_s / 60.0,
                "peak_depth_m": depth_m,
                "risk_rating": flood_risk_rating(depth_m, station.elevation_m),
            }
        )
    return tuple(rows)


def breach_hydrograph_report(
    volume_m3: float,
    head_m: float,
    stations: tuple[Station, ...],
    n_steps: int = 20,
    overtopping: bool = True,
) -> dict[str, Any]:
    """Full breach-flood summary: peak outflow, breach width, hydrograph
    duration/mean, sampled hydrograph, and the downstream station table."""
    peak_q = breach_peak_discharge_cms(volume_m3, head_m)
    t_d = hydrograph_duration_s(volume_m3, peak_q)
    return {
        "peak_discharge_cms": peak_q,
        "breach_width_m": breach_average_width_m(volume_m3, head_m, overtopping),
        "duration_s": t_d,
        "duration_min": t_d / 60.0,
        "mean_outflow_cms": mean_outflow_cms(volume_m3, t_d),
        "hydrograph": triangular_hydrograph(volume_m3, peak_q, n_steps),
        "stations": station_inundation_table(head_m, stations),
    }
