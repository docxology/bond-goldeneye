"""Tests for the Arkangel dam-facility security model (goldeneye.dam_security)."""

from __future__ import annotations

import pytest

from goldeneye.dam_security import (
    DEFAULT_ACCESS_LAYERS,
    Reservoir,
    SecurityLayer,
    access_corridor,
    breach_peak_discharge_cms,
    cumulative_detection_probability,
    expected_detection_time_min,
    flood_arrival_time_s,
    flood_depths_at_distance,
    flood_risk_rating,
    lookup_layer,
    peak_depth_at_distance_m,
    ritter_celerity_ms,
    ritter_depth_m,
    ritter_front_speed_ms,
    ritter_velocity_ms,
    security_score,
    severity_ratio,
)
from goldeneye.scenario import ARKANGEL

G = 9.80665


class TestAccessControl:
    def test_single_layer_detection(self) -> None:
        layers = (SecurityLayer("p", 0.5, 5.0, "fence"),)
        assert cumulative_detection_probability(layers) == pytest.approx(0.5)

    def test_two_layer_union(self) -> None:
        layers = (
            SecurityLayer("a", 0.5, 5.0, "fence"),
            SecurityLayer("b", 0.5, 5.0, "guard"),
        )
        # 1 - (0.5 * 0.5) = 0.75
        assert cumulative_detection_probability(layers) == pytest.approx(0.75)

    def test_default_posture_is_high(self) -> None:
        p = cumulative_detection_probability(DEFAULT_ACCESS_LAYERS)
        assert 0.9 < p <= 1.0
        assert p == pytest.approx(0.987)

    def test_no_detection_gives_zero(self) -> None:
        # Can't build a p=0 layer (validation forbids), so use tiny p.
        layers = tuple(SecurityLayer(f"l{i}", 0.0 + 1e-9, 1.0, "x") for i in range(3))
        assert cumulative_detection_probability(layers) > 0.0
        assert cumulative_detection_probability(layers) < 1e-6

    def test_expected_time_matches_hand_computation(self) -> None:
        layers = (
            SecurityLayer("a", 0.5, 10.0, "fence"),
            SecurityLayer("b", 0.5, 20.0, "guard"),
        )
        # E[t] = (0.5*10 + 0.5*0.5*20) / 0.75
        expected = expected_detection_time_min(layers)
        assert expected == pytest.approx((0.5 * 10 + 0.5 * 0.5 * 20) / 0.75)

    def test_expected_time_default(self) -> None:
        t = expected_detection_time_min(DEFAULT_ACCESS_LAYERS)
        assert 0 < t < 10

    def test_security_score_in_range(self) -> None:
        s = security_score(DEFAULT_ACCESS_LAYERS)
        assert 0 < s <= 100

    def test_security_score_improves_with_more_layers(self) -> None:
        one = (DEFAULT_ACCESS_LAYERS[0],)
        s_one = security_score(one)
        s_all = security_score(DEFAULT_ACCESS_LAYERS)
        assert s_all > s_one

    def test_access_corridor_selection(self) -> None:
        corridor, p = access_corridor("checkpoint", DEFAULT_ACCESS_LAYERS, extra_names=("control_room",))
        assert [l.name for l in corridor] == ["checkpoint", "control_room"]
        assert p == pytest.approx(1 - (1 - 0.6) * (1 - 0.9))

    def test_access_corridor_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            access_corridor("nope", DEFAULT_ACCESS_LAYERS)

    def test_lookup_layer(self) -> None:
        assert lookup_layer("control_room").detection_probability == pytest.approx(0.9)

    def test_lookup_layer_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            lookup_layer("nope")

    def test_layer_validation(self) -> None:
        with pytest.raises(ValueError):
            SecurityLayer("x", 0.0, 5.0, "fence")
        with pytest.raises(ValueError):
            SecurityLayer("x", 1.5, 5.0, "fence")
        with pytest.raises(ValueError):
            SecurityLayer("x", 0.5, 0.0, "fence")
        with pytest.raises(ValueError):
            SecurityLayer(" ", 0.5, 5.0, "fence")


class TestReservoirValidation:
    def test_valid(self) -> None:
        r = Reservoir("arkangel", 1.3e8, 75.0)
        assert r.volume_m3 == 1.3e8

    def test_nonpositive_volume_raises(self) -> None:
        with pytest.raises(ValueError):
            Reservoir("arkangel", 0.0, 75.0)

    def test_nonpositive_head_raises(self) -> None:
        with pytest.raises(ValueError):
            Reservoir("arkangel", 1.3e8, 0.0)


class TestRitterWave:
    def test_celerity(self) -> None:
        assert ritter_celerity_ms(75.0) == pytest.approx((G * 75.0) ** 0.5)

    def test_front_speed(self) -> None:
        assert ritter_front_speed_ms(75.0) == pytest.approx(2.0 * (G * 75.0) ** 0.5)

    def test_upstream_depth_is_head(self) -> None:
        # Deep upstream (x/t <= -c0) the water is undisturbed at depth H.
        assert ritter_depth_m(-100000.0, 100.0, 75.0) == pytest.approx(75.0)

    def test_dry_bed_ahead_of_front(self) -> None:
        # Far downstream before the front arrives, depth is 0.
        assert ritter_depth_m(100000.0, 0.01, 75.0) == 0.0

    def test_dam_site_depth_is_four_ninths_head(self) -> None:
        # At x=0 the depth collapses instantly to 4H/9 (Ritter result).
        assert ritter_depth_m(0.0, 100.0, 75.0) == pytest.approx(4.0 / 9.0 * 75.0)

    def test_velocity_at_dam_site(self) -> None:
        c0 = ritter_celerity_ms(75.0)
        assert ritter_velocity_ms(0.0, 100.0, 75.0) == pytest.approx((2.0 / 3.0) * c0)

    def test_depth_rises_toward_distance(self) -> None:
        # As t grows at fixed x, depth -> 4H/9 (Ritter asymptotic plateau).
        depths = [ritter_depth_m(8000.0, t, 75.0) for t in (200, 2000, 20000, 200000)]
        assert depths[0] < depths[1] < depths[2] < depths[3]
        assert depths[-1] == pytest.approx(4.0 / 9.0 * 75.0, rel=0.005)

    def test_arrival_time(self) -> None:
        assert flood_arrival_time_s(8000.0, 75.0) == pytest.approx(8000.0 / (2 * (G * 75.0) ** 0.5))

    def test_arrival_time_arkangel(self) -> None:
        # ARKANGEL facility is 8 km downstream.
        arrival = flood_arrival_time_s(ARKANGEL.facility_distance_km * 1000.0, ARKANGEL.reservoir.head_m)
        assert 100 < arrival < 300  # ~2.5 minutes

    def test_peak_depth_at_distance(self) -> None:
        assert peak_depth_at_distance_m(8000.0, 75.0) == pytest.approx(4.0 / 9.0 * 75.0)

    def test_flood_depths_at_distance_pairs(self) -> None:
        pairs = flood_depths_at_distance(8000.0, 75.0, (2000.0, 20000.0))
        assert len(pairs) == 2
        assert all(isinstance(t, float) and isinstance(d, float) for t, d in pairs)
        assert pairs[0][1] < pairs[1][1]

    def test_negative_time_raises(self) -> None:
        with pytest.raises(ValueError):
            ritter_depth_m(0.0, 0.0, 75.0)


class TestFroehlichRegression:
    def test_peak_discharge_known_vector(self) -> None:
        # Froehlich (1995) SI regression: Q_p = 0.607 * V^0.295 * H^1.24.
        assert breach_peak_discharge_cms(1.0e7, 30.0) == pytest.approx(0.607 * (1.0e7) ** 0.295 * 30.0**1.24)

    def test_peak_discharge_scales_with_volume_and_head(self) -> None:
        q_a = breach_peak_discharge_cms(1.3e8, 75.0)
        q_b = breach_peak_discharge_cms(2.6e8, 75.0)
        assert q_b > q_a > 0
        assert q_a > 10000.0  # ~31,700 m^3/s for ARKANGEL

    def test_invalid_inputs_raise(self) -> None:
        with pytest.raises(ValueError):
            breach_peak_discharge_cms(0.0, 75.0)
        with pytest.raises(ValueError):
            breach_peak_discharge_cms(1.3e8, -1.0)


class TestFloodRisk:
    def test_severity_ratio(self) -> None:
        assert severity_ratio(5.0, 10.0) == pytest.approx(0.5)

    def test_rating_tiers(self) -> None:
        assert flood_risk_rating(0.1, 10.0) == "low"
        assert flood_risk_rating(1.0, 10.0) == "moderate"
        assert flood_risk_rating(4.0, 10.0) == "high"
        assert flood_risk_rating(9.0, 10.0) == "extreme"

    def test_arkangel_is_extreme(self) -> None:
        depth = peak_depth_at_distance_m(ARKANGEL.facility_distance_km * 1000.0, ARKANGEL.reservoir.head_m)
        assert severity_ratio(depth, ARKANGEL.facility_elevation_m) > 0.5
        assert flood_risk_rating(depth, ARKANGEL.facility_elevation_m) == "extreme"

    def test_invalid_depth_raises(self) -> None:
        with pytest.raises(ValueError):
            severity_ratio(-1.0, 10.0)
        with pytest.raises(ValueError):
            severity_ratio(1.0, 0.0)
