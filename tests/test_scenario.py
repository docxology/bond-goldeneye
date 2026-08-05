"""Tests for the ARKANGEL scenario composition (goldeneye.scenario)."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldeneye.scenario import (
    CouplingParams,
    ARKANGEL,
    ArkangelScenario,
    analyze_arkangel,
    input_hash,
    load_scenario_config,
    scenario_input_dict,
)
from goldeneye.emp_model import EmpWeapon
from goldeneye.dam_security import Reservoir


class TestDefaults:
    def test_default_weapon(self) -> None:
        assert ARKANGEL.weapon.yield_kt == 2000.0
        assert ARKANGEL.weapon.burst_altitude_km == 300.0

    def test_default_reservoir(self) -> None:
        assert ARKANGEL.reservoir.name == "arkangel"
        assert ARKANGEL.reservoir.head_m == 75.0

    def test_codename(self) -> None:
        assert ARKANGEL.codename == "ARKANGEL"

    def test_invalid_facility_distance(self) -> None:
        with pytest.raises(ValueError):
            ArkangelScenario(
                weapon=ARKANGEL.weapon,
                reservoir=ARKANGEL.reservoir,
                facility_distance_km=0.0,
                facility_elevation_m=10.0,
            )


class TestAnalysis:
    def test_analysis_is_deterministic(self) -> None:
        assert analyze_arkangel(ARKANGEL) == analyze_arkangel(ARKANGEL)

    def test_analysis_keys_present(self) -> None:
        a = analyze_arkangel(ARKANGEL)
        assert set(a) == {
            "name",
            "codename",
            "input_hash",
            "emp",
            "kill_radius",
            "orbit",
            "coupling",
            "grid",
            "dam",
            "flood",
            "hydrograph",
            "access",
        }

    def test_analysis_json_serializable(self) -> None:
        import json

        json.dumps(analyze_arkangel(ARKANGEL))

    def test_emp_metrics(self) -> None:
        emp = analyze_arkangel(ARKANGEL)["emp"]
        assert emp["yield_kt"] == 2000.0
        assert emp["burst_altitude_km"] == 300.0
        assert emp["nadir_field_vm"] > 80000.0

    def test_kill_radius_rows(self) -> None:
        rows = analyze_arkangel(ARKANGEL)["kill_radius"]
        assert len(rows) == 4
        names = [r["name"] for r in rows]
        assert names == ["unprotected", "commercial", "military", "legacy_tube"]

    def test_custom_scenario_alters_analysis(self) -> None:
        sc = ArkangelScenario(
            weapon=EmpWeapon(yield_kt=100.0, burst_altitude_km=100.0),
            reservoir=Reservoir("small", 1e7, 30.0),
            facility_distance_km=3.0,
            facility_elevation_m=5.0,
        )
        a = analyze_arkangel(sc)
        assert a["emp"]["yield_kt"] == 100.0
        assert a["flood"]["peak_depth_m"] == pytest.approx(4.0 / 9.0 * 30.0)


class TestHashing:
    def test_input_hash_stable(self) -> None:
        assert input_hash(ARKANGEL) == input_hash(ARKANGEL)

    def test_input_hash_changes_with_scenario(self) -> None:
        other = ArkangelScenario(
            weapon=EmpWeapon(yield_kt=100.0, burst_altitude_km=100.0),
            reservoir=ARKANGEL.reservoir,
            facility_distance_km=ARKANGEL.facility_distance_km,
            facility_elevation_m=ARKANGEL.facility_elevation_m,
        )
        assert input_hash(other) != input_hash(ARKANGEL)

    def test_input_hash_is_hex64(self) -> None:
        assert len(input_hash(ARKANGEL)) == 64
        int(input_hash(ARKANGEL), 16)  # must parse as hex

    def test_scenario_input_dict_flat(self) -> None:
        d = scenario_input_dict(ARKANGEL)
        assert d["codename"] == "ARKANGEL"
        assert len(d["access_layers"]) == 4


class TestConfigLoading:
    def test_load_default_config(self) -> None:
        sc = load_scenario_config()
        assert sc.weapon.yield_kt == ARKANGEL.weapon.yield_kt

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_scenario_config(tmp_path / "nope.yaml")

    def test_load_non_mapping_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text("just a string\n", encoding="utf-8")
        with pytest.raises(ValueError, match="top-level mapping"):
            load_scenario_config(cfg)

    def test_full_config_override(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "scenario:\n"
            "  name: custom\n"
            "  weapon:\n"
            "    yield_kt: 500.0\n"
            "    burst_altitude_km: 150.0\n"
            "  reservoir:\n"
            "    volume_m3: 5.0e7\n"
            "    head_m: 40.0\n"
            "  facility:\n"
            "    distance_km: 5.0\n"
            "    elevation_m: 8.0\n"
            "  access:\n"
            "    layers:\n"
            "      - {name: 'p', detection_probability: 0.5, response_time_min: 3.0, barrier: 'x'}\n",
            encoding="utf-8",
        )
        sc = load_scenario_config(cfg)
        assert sc.name == "custom"
        assert sc.weapon.yield_kt == 500.0
        assert sc.weapon.burst_altitude_km == 150.0
        assert sc.reservoir.head_m == 40.0
        assert sc.facility_distance_km == 5.0
        assert len(sc.access_layers) == 1
        assert sc.access_layers[0].detection_probability == 0.5

    def test_scenario_bad_non_mapping(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text("scenario: [1, 2]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="'scenario' section"):
            load_scenario_config(cfg)


class TestDeepenedAnalysis:
    def test_new_sections_present(self) -> None:
        a = analyze_arkangel(ARKANGEL)
        assert set(a) >= {"orbit", "coupling", "grid", "hydrograph"}

    def test_orbit_metrics(self) -> None:
        orbit = analyze_arkangel(ARKANGEL)["orbit"]
        assert orbit["period_min"] > 80.0
        assert 7.0 < orbit["speed_kms"] < 8.0
        assert orbit["visible"] is True
        assert 0 < orbit["elevation_angle_deg"] < 90

    def test_coupling_metrics(self) -> None:
        c = analyze_arkangel(ARKANGEL)["coupling"]
        assert c["induced_voltage_v"] > 10000.0
        # 0.1 mm aluminium at 100 MHz: 106.0 dB absorption + 86.3 dB
        # reflection. Pinned to the hand-computed physics; a units-broken
        # reflection loss would land ~78 dB high and fail here.
        assert c["absorption_db"] == pytest.approx(106.0, abs=0.5)
        assert c["reflection_db"] == pytest.approx(86.3, abs=0.5)
        assert c["se_db"] == pytest.approx(192.3, abs=0.5)
        assert c["shielded_field_vm"] < 1e-3
        assert c["protection_margin_db_military"] > 10.0

    def test_grid_metrics(self) -> None:
        g = analyze_arkangel(ARKANGEL)["grid"]
        assert g["down_nodes"] == ("town_a", "relay")
        assert g["min_disjoint_paths"] >= 2
        assert 0 < g["served_fraction"] < 1

    def test_hydrograph_metrics(self) -> None:
        h = analyze_arkangel(ARKANGEL)["hydrograph"]
        # Froehlich (2008), K0 = 1.3: 0.27*1.3*(1.3e8)^0.32*75^0.04 = 164.73 m.
        assert h["breach_width_m"] == pytest.approx(164.73, abs=0.05)
        assert len(h["stations"]) == 3
        assert h["stations"][-1]["distance_km"] > h["stations"][0]["distance_km"]

    def test_analysis_full_determinism(self) -> None:
        assert analyze_arkangel(ARKANGEL) == analyze_arkangel(ARKANGEL)


class TestConfigDeepened:
    def test_orbit_coupling_override(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "scenario:\n"
            "  orbit:\n"
            "    altitude_km: 500.0\n"
            "    min_elevation_deg: 20.0\n"
            "  coupling:\n"
            "    conductor_length_m: 25.0\n"
            "    shield_material: copper\n",
            encoding="utf-8",
        )
        sc = load_scenario_config(cfg)
        assert sc.orbit.altitude_km == 500.0
        assert sc.orbit.min_elevation_deg == 20.0
        assert sc.coupling.conductor_length_m == 25.0
        assert sc.coupling.shield_material == "copper"

    def test_bad_coupling_material(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text("scenario:\n  coupling:\n    shield_material: lead\n", encoding="utf-8")
        with pytest.raises(KeyError):
            load_scenario_config(cfg)


class TestCouplingParamsGuards:
    """CouplingParams rejects every physically meaningless input."""

    def _params(self, **overrides: object) -> None:
        kwargs: dict[str, object] = {
            "conductor_length_m": 10.0,
            "shield_material": "aluminum",
            "shield_thickness_mm": 0.1,
            "e1_frequency_hz": 1.0e8,
            "impedance_ohm": 50.0,
        }
        kwargs.update(overrides)
        CouplingParams(**kwargs)  # type: ignore[arg-type]

    def test_rejects_non_positive_conductor_length(self) -> None:
        with pytest.raises(ValueError, match="conductor_length_m must be > 0"):
            self._params(conductor_length_m=0.0)

    def test_rejects_unknown_shield_material(self) -> None:
        with pytest.raises(KeyError, match="unknown shield material"):
            self._params(shield_material="unobtainium")

    def test_rejects_non_positive_thickness(self) -> None:
        with pytest.raises(ValueError, match="shield_thickness_mm must be > 0"):
            self._params(shield_thickness_mm=-1.0)

    def test_rejects_non_positive_frequency(self) -> None:
        with pytest.raises(ValueError, match="e1_frequency_hz must be > 0"):
            self._params(e1_frequency_hz=0.0)

    def test_rejects_non_positive_impedance(self) -> None:
        with pytest.raises(ValueError, match="impedance_ohm must be > 0"):
            self._params(impedance_ohm=0.0)

    def test_scenario_rejects_non_positive_facility_elevation(self) -> None:
        with pytest.raises(ValueError, match="facility_elevation_m must be > 0"):
            ArkangelScenario(
                weapon=EmpWeapon(yield_kt=2000.0, burst_altitude_km=300.0),
                reservoir=Reservoir(name="r", volume_m3=1.0e8, head_m=75.0),
                facility_distance_km=8.0,
                facility_elevation_m=0.0,
            )

    def test_config_access_layer_must_be_a_mapping(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        config = tmp_path / "config.yaml"
        config.write_text(
            "scenario:\n  access:\n    layers:\n      - not_a_mapping\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="each access layer must be a mapping"):
            load_scenario_config(config)


class TestOrbitAndCouplingSectionKeys:
    """Keys added for manuscript tokens must stay present and correct."""

    def test_orbit_section_reports_radius_and_inputs(self) -> None:
        orbit = analyze_arkangel(ARKANGEL)["orbit"]
        assert orbit["radius_km"] == pytest.approx(6371.0 + ARKANGEL.orbit.altitude_km)
        assert orbit["min_elevation_deg"] == ARKANGEL.orbit.min_elevation_deg
        assert orbit["nadir_lat_deg"] == ARKANGEL.orbit.nadir_lat_deg
        assert orbit["target_lat_deg"] == ARKANGEL.orbit.target_lat_deg

    def test_coupling_section_echoes_its_inputs(self) -> None:
        coupling = analyze_arkangel(ARKANGEL)["coupling"]
        assert coupling["conductor_length_m"] == ARKANGEL.coupling.conductor_length_m
        assert coupling["shield_material"] == ARKANGEL.coupling.shield_material
        assert coupling["frequency_mhz"] == pytest.approx(ARKANGEL.coupling.e1_frequency_hz / 1e6)
        assert coupling["impedance_ohm"] == ARKANGEL.coupling.impedance_ohm
        assert coupling["military_withstand_vm"] > 0.0
