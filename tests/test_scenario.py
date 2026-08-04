"""Tests for the ARKANGEL scenario composition (goldeneye.scenario)."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldeneye.scenario import (
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
        assert set(a) == {"name", "codename", "input_hash", "emp", "kill_radius", "dam", "flood", "access"}

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
