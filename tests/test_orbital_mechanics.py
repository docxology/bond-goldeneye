"""Tests for the orbital platform mechanics (goldeneye.orbital_mechanics)."""

from __future__ import annotations

import math

import pytest

from goldeneye.orbital_mechanics import (
    EARTH_RADIUS_M,
    MU_EARTH,
    OrbitGeometry,
    altitude_from_period_s,
    central_angle_at_elevation_deg,
    central_angle_deg,
    circular_orbit_period_s,
    circular_orbit_speed_ms,
    elevation_angle_deg,
    is_visible,
    orbital_radius_m,
    overhead_pass_duration_s,
    slant_range_m,
)


class TestOrbitKinematics:
    def test_orbital_radius_adds_altitude(self) -> None:
        assert orbital_radius_m(400000.0) == pytest.approx(EARTH_RADIUS_M + 400000.0)

    def test_iss_period(self) -> None:
        # ISS-class orbit (~400 km): period ~92.4 min (5544 s).
        period = circular_orbit_period_s(orbital_radius_m(400000.0))
        assert 5400.0 < period < 5700.0
        assert period == pytest.approx(2.0 * math.pi * math.sqrt((6.771e6) ** 3 / MU_EARTH), rel=1e-6)

    def test_iss_speed(self) -> None:
        # ~7.67 km/s at 400 km.
        speed = circular_orbit_speed_ms(orbital_radius_m(400000.0))
        assert 7500.0 < speed < 7900.0

    def test_altitude_from_period_round_trip(self) -> None:
        radius = orbital_radius_m(300000.0)
        period = circular_orbit_period_s(radius)
        assert altitude_from_period_s(period) == pytest.approx(300000.0, rel=1e-6)

    def test_invalid_radius(self) -> None:
        with pytest.raises(ValueError):
            circular_orbit_period_s(0.0)
        with pytest.raises(ValueError):
            circular_orbit_speed_ms(-1.0)

    def test_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            altitude_from_period_s(0.0)


class TestSphericalGeometry:
    def test_central_angle_zero_at_same_point(self) -> None:
        assert central_angle_deg(53.5, 108.0, 53.5, 108.0) == pytest.approx(0.0)

    def test_central_angle_ninety(self) -> None:
        assert central_angle_deg(0.0, 0.0, 0.0, 90.0) == pytest.approx(90.0)

    def test_central_angle_antipodal(self) -> None:
        assert central_angle_deg(0.0, 0.0, 0.0, 180.0) == pytest.approx(180.0)

    def test_arcangel_target_central_angle(self) -> None:
        # Nadir (60N,108E) -> target (53.5N,108E) is ~6.5 deg of latitude.
        gamma = central_angle_deg(60.0, 108.0, 53.5, 108.0)
        assert gamma == pytest.approx(6.5, rel=1e-3)

    def test_elevation_at_nadir_is_ninety(self) -> None:
        assert elevation_angle_deg(53.5, 108.0, 53.5, 108.0, 300000.0) == pytest.approx(90.0)

    def test_elevation_at_horizon_is_zero(self) -> None:
        alt = 300000.0
        gamma_h = central_angle_at_elevation_deg(alt, 0.0)
        # Two points separated by the horizon central angle should show ~0 deg elevation.
        elev = elevation_angle_deg(0.0, 0.0, gamma_h, 0.0, alt)
        assert abs(elev) < 0.5

    def test_elevation_decreases_with_central_angle(self) -> None:
        alt = 300000.0
        near = elevation_angle_deg(0.0, 0.0, 2.0, 0.0, alt)
        far = elevation_angle_deg(0.0, 0.0, 12.0, 0.0, alt)
        assert near > far > 0

    def test_slant_range_at_nadir_is_altitude(self) -> None:
        assert slant_range_m(53.5, 108.0, 53.5, 108.0, 300000.0) == pytest.approx(300000.0)

    def test_slant_range_exceeds_altitude_off_nadir(self) -> None:
        slant = slant_range_m(0.0, 0.0, 10.0, 0.0, 300000.0)
        assert slant > 300000.0

    def test_visibility(self) -> None:
        # Overhead (nadir) is always visible; far below the elevation floor is not.
        assert is_visible(0.0, 0.0, 0.0, 0.0, 300000.0, min_elevation_deg=10.0)
        assert is_visible(0.0, 0.0, 0.0, 0.0, 300000.0, min_elevation_deg=90.0)


class TestPassDuration:
    def test_pass_duration_bounded_by_period(self) -> None:
        alt = 300000.0
        period = circular_orbit_period_s(orbital_radius_m(alt))
        duration = overhead_pass_duration_s(alt, 10.0)
        assert 0.0 < duration < period

    def test_pass_duration_increases_with_altitude(self) -> None:
        lo = overhead_pass_duration_s(200000.0, 10.0)
        hi = overhead_pass_duration_s(800000.0, 10.0)
        assert hi > lo > 0

    def test_higher_min_elevation_shortens_pass(self) -> None:
        strict = overhead_pass_duration_s(300000.0, 45.0)
        lax = overhead_pass_duration_s(300000.0, 10.0)
        assert strict < lax


class TestOrbitGeometryValidation:
    def test_bad_altitude(self) -> None:
        with pytest.raises(ValueError):
            OrbitGeometry(0.0, 60.0, 108.0, 53.5, 108.0, 10.0)

    def test_bad_latitude(self) -> None:
        with pytest.raises(ValueError):
            OrbitGeometry(300.0, 120.0, 108.0, 53.5, 108.0, 10.0)

    def test_bad_longitude(self) -> None:
        with pytest.raises(ValueError):
            OrbitGeometry(300.0, 60.0, 200.0, 53.5, 108.0, 10.0)

    def test_bad_min_elevation(self) -> None:
        with pytest.raises(ValueError):
            OrbitGeometry(300.0, 60.0, 108.0, 53.5, 108.0, 120.0)

    def test_valid(self) -> None:
        g = OrbitGeometry(300.0, 60.0, 108.0, 53.5, 108.0, 10.0)
        assert g.altitude_km == 300.0
