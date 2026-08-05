"""Orbital platform mechanics — the GoldenEye weapon constellation.

The ARKANGEL weapon is delivered from an orbital platform (*GoldenEye*, 1995).
This module provides the deterministic Keplerian geometry of that platform:

* circular-orbit kinematics — period and speed from the vis-viva equation for
  a circular orbit, plus altitude-from-period inversion;
* spherical Earth geometry — central angle between two surface points, the
  elevation angle of the platform as seen from a ground point, and the slant
  range to it;
* visibility — whether a ground target can see the platform above a minimum
  elevation, and the duration of a directly-overhead pass above that elevation.

Constants follow the published values: Earth gravitational parameter
mu = 3.986004418e14 m^3/s^2 and mean Earth radius 6371 km (Bate, Mueller &
White, *Fundamentals of Astrodynamics*, 1971). All functions are closed-form
(or deterministic bisection) and deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "EARTH_RADIUS_M",
    "MU_EARTH",
    "OrbitGeometry",
    "altitude_from_period_s",
    "central_angle_deg",
    "central_angle_at_elevation_deg",
    "circular_orbit_period_s",
    "circular_orbit_speed_ms",
    "elevation_angle_deg",
    "is_visible",
    "orbital_radius_m",
    "overhead_pass_duration_s",
    "slant_range_m",
]

#: Standard gravitational parameter of the Earth (m^3/s^2).
MU_EARTH = 3.986004418e14

#: Mean Earth radius (m) — WGS-84 mean.
EARTH_RADIUS_M = 6371000.0

#: Bisection iterations for the elevation-angle inversion (deterministic).
_BISECTION_ITERATIONS = 60

#: Elevation-angle solver tolerance (deg).
_ELEVATION_EPSILON_DEG = 1e-9


@dataclass(frozen=True)
class OrbitGeometry:
    """A circular orbit and the ground-target geometry of interest.

    Attributes:
        altitude_km: Platform altitude above the surface (km, > 0).
        nadir_lat_deg / nadir_lon_deg: Sub-platform point (deg).
        target_lat_deg / target_lon_deg: Ground target point (deg).
        min_elevation_deg: Minimum usable elevation angle (deg, in [0, 90]).
    """

    altitude_km: float
    nadir_lat_deg: float
    nadir_lon_deg: float
    target_lat_deg: float
    target_lon_deg: float
    min_elevation_deg: float

    def __post_init__(self) -> None:
        if not (isinstance(self.altitude_km, (int, float)) and self.altitude_km > 0):
            raise ValueError(f"altitude_km must be > 0, got {self.altitude_km!r}")
        for label, value in (
            ("nadir_lat_deg", self.nadir_lat_deg),
            ("target_lat_deg", self.target_lat_deg),
        ):
            if not -90.0 <= float(value) <= 90.0:
                raise ValueError(f"{label} must be in [-90, 90], got {value!r}")
        for label, value in (
            ("nadir_lon_deg", self.nadir_lon_deg),
            ("target_lon_deg", self.target_lon_deg),
        ):
            if not -180.0 <= float(value) <= 180.0:
                raise ValueError(f"{label} must be in [-180, 180], got {value!r}")
        if not 0.0 <= float(self.min_elevation_deg) <= 90.0:
            raise ValueError(f"min_elevation_deg must be in [0, 90], got {self.min_elevation_deg!r}")


def orbital_radius_m(altitude_m: float) -> float:
    """Orbital radius from the Earth's centre (m) for an altitude above the surface."""
    return float(EARTH_RADIUS_M + float(altitude_m))


def circular_orbit_speed_ms(radius_m: float) -> float:
    """Circular-orbit speed (m/s) from the vis-viva equation: sqrt(mu/r)."""
    r = float(radius_m)
    if r <= 0:
        raise ValueError(f"radius_m must be > 0, got {radius_m!r}")
    return float(math.sqrt(MU_EARTH / r))


def circular_orbit_period_s(radius_m: float) -> float:
    """Circular-orbit period (s): 2*pi*sqrt(r^3/mu)."""
    r = float(radius_m)
    if r <= 0:
        raise ValueError(f"radius_m must be > 0, got {radius_m!r}")
    return float(2.0 * math.pi * math.sqrt(r**3 / MU_EARTH))


def altitude_from_period_s(period_s: float) -> float:
    """Altitude above the surface (m) whose circular orbit has the given period."""
    t = float(period_s)
    if t <= 0:
        raise ValueError(f"period_s must be > 0, got {period_s!r}")
    radius = (MU_EARTH * t * t / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
    return float(radius) - EARTH_RADIUS_M


def central_angle_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle central angle (deg) between two surface points.

    Spherical law of cosines; clamped to [0, 180] to absorb rounding at the
    poles and antipodes.
    """
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_lambda = math.radians(float(lon2) - float(lon1))
    cos_gamma = math.sin(phi1) * math.sin(phi2) + math.cos(phi1) * math.cos(phi2) * math.cos(d_lambda)
    gamma = math.acos(max(-1.0, min(1.0, cos_gamma)))
    return float(math.degrees(gamma))


def _elevation_from_central_angle_deg(gamma_deg: float, altitude_m: float) -> float:
    """Elevation angle (deg) of a platform at altitude over central angle gamma."""
    gamma = math.radians(float(gamma_deg))
    r = orbital_radius_m(altitude_m)
    if gamma <= 0.0:
        return 90.0
    ratio = EARTH_RADIUS_M / r
    numerator = math.cos(gamma) - ratio
    denominator = math.sin(gamma)
    if denominator <= 0.0:
        return 90.0
    return float(math.degrees(math.atan(numerator / denominator)))


def elevation_angle_deg(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    altitude_m: float,
) -> float:
    """Elevation angle (deg) of the platform as seen from the ground point.

    ``(lat1, lon1)`` is the observer, ``(lat2, lon2)`` the sub-platform point.
    Negative values mean the platform is below the observer's horizon.
    """
    gamma = central_angle_deg(lat1, lon1, lat2, lon2)
    return _elevation_from_central_angle_deg(gamma, altitude_m)


def slant_range_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    altitude_m: float,
) -> float:
    """Slant range (m) from the ground point to the platform.

    Law of cosines in the plane of the great circle:
    d^2 = r^2 + R^2 - 2*r*R*cos(gamma).
    """
    gamma = math.radians(central_angle_deg(lat1, lon1, lat2, lon2))
    r = orbital_radius_m(altitude_m)
    d2 = r * r + EARTH_RADIUS_M * EARTH_RADIUS_M - 2.0 * r * EARTH_RADIUS_M * math.cos(gamma)
    return float(math.sqrt(max(0.0, d2)))


def is_visible(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    altitude_m: float,
    min_elevation_deg: float = 0.0,
) -> bool:
    """True when the platform is visible from the ground point at or above
    ``min_elevation_deg``."""
    return elevation_angle_deg(lat1, lon1, lat2, lon2, altitude_m) >= float(min_elevation_deg)


def central_angle_at_elevation_deg(altitude_m: float, min_elevation_deg: float) -> float:
    """Maximum central angle (deg) at which the elevation angle stays at or
    above ``min_elevation_deg``.

    Deterministic bisection over the monotone-decreasing elevation profile,
    from 0 (nadir, 90 deg elevation) to the geometric horizon (0 deg).
    """
    r = orbital_radius_m(altitude_m)
    horizon = math.degrees(math.acos(EARTH_RADIUS_M / r))
    target = float(min_elevation_deg)
    if target >= 90.0:
        return 0.0
    if target <= 0.0:
        return horizon
    lo, hi = 0.0, horizon
    for _ in range(_BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        if _elevation_from_central_angle_deg(mid, altitude_m) >= target - _ELEVATION_EPSILON_DEG:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def overhead_pass_duration_s(altitude_m: float, min_elevation_deg: float) -> float:
    """Duration (s) of a directly-overhead pass above ``min_elevation_deg``.

    Approximation: for a zenith (directly-overhead) pass the platform remains
    inside the visibility cone for a central-angle arc of ``2*gamma*`` of its
    full ``2*pi`` orbit, so the duration is ``(2*gamma*/2*pi)*T``. Documented
    approximation — real passes are shorter/varies with geometry.
    """
    gamma_star = math.radians(central_angle_at_elevation_deg(altitude_m, min_elevation_deg))
    period = circular_orbit_period_s(orbital_radius_m(altitude_m))
    return float((2.0 * gamma_star / (2.0 * math.pi)) * period)
