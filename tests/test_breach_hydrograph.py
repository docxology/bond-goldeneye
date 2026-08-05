"""Tests for the dam-breach hydrograph model (goldeneye.breach_hydrograph)."""

from __future__ import annotations

import pytest

from goldeneye.breach_hydrograph import (
    FROEHLICH_OVERTOPPING_FACTOR,
    FROEHLICH_PIPING_FACTOR,
    Station,
    breach_average_width_m,
    breach_hydrograph_report,
    hydrograph_duration_s,
    mean_outflow_cms,
    station_inundation_table,
    triangular_hydrograph,
)

V = 1.3e8
H = 75.0
Q_P = 0.607 * V**0.295 * H**1.24  # Froehlich peak discharge (~31.8k m^3/s)


class TestBreachWidth:
    def test_froehlich_2008_overtopping(self) -> None:
        width = breach_average_width_m(V, H, overtopping=True)
        assert width == pytest.approx(0.27 * FROEHLICH_OVERTOPPING_FACTOR * V**0.32 * H**0.04)

    def test_overtopping_wide_than_piping(self) -> None:
        assert breach_average_width_m(V, H, overtopping=True) > breach_average_width_m(V, H, overtopping=False)

    def test_piping_factor(self) -> None:
        assert breach_average_width_m(V, H, overtopping=False) == pytest.approx(
            0.27 * FROEHLICH_PIPING_FACTOR * V**0.32 * H**0.04
        )

    def test_arkangel_width_is_realistic(self) -> None:
        assert 100.0 < breach_average_width_m(V, H) < 300.0

    def test_invalid(self) -> None:
        with pytest.raises(ValueError):
            breach_average_width_m(0.0, H)
        with pytest.raises(ValueError):
            breach_average_width_m(V, 0.0)


class TestHydrograph:
    def test_duration_is_2v_over_q(self) -> None:
        assert hydrograph_duration_s(V, Q_P) == pytest.approx(2.0 * V / Q_P)

    def test_mean_outflow(self) -> None:
        t_d = hydrograph_duration_s(V, Q_P)
        assert mean_outflow_cms(V, t_d) == pytest.approx(V / t_d)

    def test_triangular_endpoints(self) -> None:
        graph = triangular_hydrograph(V, Q_P, 10)
        assert graph[0] == pytest.approx((0.0, Q_P))
        assert graph[-1][1] == pytest.approx(0.0, abs=1e-6)
        assert graph[-1][0] == pytest.approx(2.0 * V / Q_P)

    def test_triangular_conserves_volume(self) -> None:
        n = 200
        graph = triangular_hydrograph(V, Q_P, n)
        area = sum(0.5 * (b[0] - a[0]) * (a[1] + b[1]) for a, b in zip(graph, graph[1:]))
        assert area == pytest.approx(V, rel=0.02)

    def test_n_steps_guard(self) -> None:
        with pytest.raises(ValueError):
            triangular_hydrograph(V, Q_P, 0)

    def test_duration_guard(self) -> None:
        with pytest.raises(ValueError):
            hydrograph_duration_s(0.0, Q_P)
        with pytest.raises(ValueError):
            hydrograph_duration_s(V, 0.0)


class TestStations:
    def _stations(self) -> tuple[Station, ...]:
        return (Station("facility", 8.0, 10.0), Station("town", 12.0, 8.0), Station("bridge", 20.0, 6.0))

    def test_arrival_times_use_ritter(self) -> None:
        from goldeneye.dam_security import ritter_front_speed_ms

        front = ritter_front_speed_ms(H)
        rows = station_inundation_table(H, self._stations())
        assert rows[0]["arrival_time_s"] == pytest.approx(8000.0 / front)

    def test_arrival_increases_with_distance(self) -> None:
        rows = station_inundation_table(H, self._stations())
        times = [row["arrival_time_min"] for row in rows]
        assert times[0] < times[1] < times[2]

    def test_peak_depth_is_four_ninths_head(self) -> None:
        rows = station_inundation_table(H, self._stations())
        assert all(row["peak_depth_m"] == pytest.approx(4.0 / 9.0 * H) for row in rows)

    def test_facility_station(self) -> None:
        rows = station_inundation_table(H, self._stations())
        facility = rows[0]
        assert facility["name"] == "facility"
        assert facility["arrival_time_min"] == pytest.approx(2.46, rel=0.02)
        assert facility["risk_rating"] == "extreme"

    def test_station_validation(self) -> None:
        with pytest.raises(ValueError):
            Station("x", 0.0, 10.0)
        with pytest.raises(ValueError):
            Station("x", 8.0, 0.0)
        with pytest.raises(ValueError):
            Station(" ", 8.0, 10.0)


class TestReport:
    def test_report_structure(self) -> None:
        stations = (Station("facility", 8.0, 10.0),)
        report = breach_hydrograph_report(V, H, stations)
        assert report["peak_discharge_cms"] == pytest.approx(Q_P)
        assert report["breach_width_m"] > 0
        assert report["duration_min"] == pytest.approx(2.0 * V / Q_P / 60.0)
        assert report["mean_outflow_cms"] == pytest.approx(Q_P / 2.0)
        assert len(report["stations"]) == 1
        assert len(report["hydrograph"]) >= 3

    def test_report_deterministic(self) -> None:
        stations = (Station("facility", 8.0, 10.0),)
        assert breach_hydrograph_report(V, H, stations) == breach_hydrograph_report(V, H, stations)

    def test_report_json_serializable(self) -> None:
        import json

        json.dumps(breach_hydrograph_report(V, H, (Station("facility", 8.0, 10.0),)))


class TestMeanOutflowGuards:
    def test_rejects_non_positive_duration(self) -> None:
        with pytest.raises(ValueError, match="must both be > 0"):
            mean_outflow_cms(1.0e8, 0.0)

    def test_rejects_non_positive_volume(self) -> None:
        with pytest.raises(ValueError, match="must both be > 0"):
            mean_outflow_cms(0.0, 100.0)
