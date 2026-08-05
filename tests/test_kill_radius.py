"""Tests for the electronics kill-radius analysis (goldeneye.kill_radius)."""

from __future__ import annotations

import math

import pytest

from goldeneye.emp_model import EmpWeapon, peak_e_field_at_nadir_vm, peak_e_field_vm
from goldeneye.kill_radius import (
    CLASS_INDEX,
    VULNERABILITY_CLASSES,
    VulnerabilityClass,
    altitude_sweep,
    damage_probability_vs_field,
    footprint_sweep,
    kill_area_fraction,
    kill_area_km2,
    kill_radius_km,
    kill_table_for_class,
    lookup_class,
)


#: Canonical ARKANGEL weapon (2 Mt @ 300 km).
WEAPON = EmpWeapon(yield_kt=2000.0, burst_altitude_km=300.0)


class TestRegistry:
    def test_four_classes_present(self) -> None:
        names = [c.name for c in VULNERABILITY_CLASSES]
        assert names == ["unprotected", "commercial", "military", "legacy_tube"]

    def test_class_index_alignment(self) -> None:
        for cls in VULNERABILITY_CLASSES:
            assert CLASS_INDEX[cls.name] is cls

    def test_lookup_by_name(self) -> None:
        assert lookup_class("military").damage_threshold_vm == 50000.0

    def test_lookup_unknown_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            lookup_class("nope")

    def test_class_thresholds_ordered(self) -> None:
        for cls in VULNERABILITY_CLASSES:
            assert 0 < cls.upset_threshold_vm < cls.damage_threshold_vm

    def test_class_validation(self) -> None:
        with pytest.raises(ValueError):
            VulnerabilityClass(
                name="bad",
                label="bad",
                upset_threshold_vm=5.0,
                damage_threshold_vm=2.0,
                description="upset above damage",
            )
        with pytest.raises(ValueError):
            VulnerabilityClass(
                name=" ",
                label="bad",
                upset_threshold_vm=1.0,
                damage_threshold_vm=2.0,
                description="empty name",
            )


class TestKillRadius:
    def test_unprotected_covers_footprint(self) -> None:
        # Nadir ~90 kV/m >> 1 kV/m; the kill radius saturates at the horizon.
        r = kill_radius_km(WEAPON, "unprotected")
        horizon = math.sqrt(2.0 * 6371.0 * 300.0 + 300.0**2)
        assert r == pytest.approx(horizon, rel=1e-3)

    def test_legacy_tube_immune(self) -> None:
        # Nadir ~90 kV/m < 1 MV/m -> no kill radius.
        assert kill_radius_km(WEAPON, "legacy_tube") == 0.0

    def test_radius_ordering_across_classes(self) -> None:
        radii = {c: kill_radius_km(WEAPON, c) for c in CLASS_INDEX}
        assert radii["unprotected"] > radii["commercial"] > radii["military"]
        assert radii["military"] > 0.0

    def test_analytic_no_absorption_limit(self) -> None:
        # At a high burst altitude absorption is negligible, so the radius for
        # threshold T satisfies r ~ h*sqrt(E0_ys/T - 1). Verify both radii
        # bracket that closed form.
        h = 300.0
        ys = peak_e_field_at_nadir_vm(h, 2000.0)
        for name, t in (("commercial", 10000.0), ("military", 50000.0)):
            expected = h * math.sqrt(ys / t - 1.0)
            got = kill_radius_km(EmpWeapon(2000.0, h), name)
            assert got == pytest.approx(expected, rel=0.1)

    def test_zero_radius_when_nadir_below_threshold(self) -> None:
        tiny = EmpWeapon(yield_kt=0.1, burst_altitude_km=30.0)
        assert kill_radius_km(tiny, "military") == 0.0

    def test_accepts_class_object(self) -> None:
        cls = lookup_class("commercial")
        assert kill_radius_km(WEAPON, cls) == kill_radius_km(WEAPON, "commercial")

    def test_uncapped_radius_grows(self) -> None:
        # Without a horizon cap the radius is larger than the capped one.
        capped = kill_radius_km(WEAPON, "unprotected", horizon_cap=True)
        uncapped = kill_radius_km(WEAPON, "unprotected", horizon_cap=False)
        assert uncapped >= capped

    def test_radius_is_deterministic(self) -> None:
        assert kill_radius_km(WEAPON, "commercial") == kill_radius_km(WEAPON, "commercial")


class TestAreaAndFractions:
    def test_area_is_pi_r2(self) -> None:
        assert kill_area_km2(10.0) == pytest.approx(math.pi * 100.0)

    def test_fraction_in_unit_interval(self) -> None:
        for name in CLASS_INDEX:
            f = kill_area_fraction(kill_radius_km(WEAPON, name), WEAPON.burst_altitude_km)
            assert 0.0 <= f <= 1.0

    def test_fraction_full_at_horizon(self) -> None:
        from goldeneye.emp_model import ground_range_to_horizon_km

        horizon = ground_range_to_horizon_km(WEAPON.burst_altitude_km)
        assert kill_area_fraction(horizon, WEAPON.burst_altitude_km) == pytest.approx(1.0)

    def test_fraction_zero(self) -> None:
        assert kill_area_fraction(0.0, WEAPON.burst_altitude_km) == 0.0


class TestTablesAndSweeps:
    def test_footprint_sweep_shape(self) -> None:
        rows = footprint_sweep(WEAPON)
        assert len(rows) == 4
        for row in rows:
            assert row["name"] in CLASS_INDEX
            assert row["radius_km"] >= 0.0
            assert row["area_km2"] >= 0.0
            assert 0.0 <= row["footprint_fraction"] <= 1.0

    def test_kill_table_for_class(self) -> None:
        row = kill_table_for_class(WEAPON, "military")
        assert row["name"] == "military"
        assert row["radius_km"] > 0.0

    def test_altitude_sweep_monotone_for_high_classes(self) -> None:
        rows = altitude_sweep((100.0, 300.0, 600.0), 2000.0)
        com_radii = [row["commercial"] for row in rows]  # type: ignore[index]
        assert com_radii[0] < com_radii[1] < com_radii[2]

    def test_altitude_sweep_yield_passed_through(self) -> None:
        rows = altitude_sweep((300.0,), 2000.0)
        assert len(rows) == 1


class TestDamageProbability:
    def test_at_threshold_is_half(self) -> None:
        cls = lookup_class("commercial")
        assert damage_probability_vs_field(cls.damage_threshold_vm, cls) == pytest.approx(0.5)

    def test_monotone(self) -> None:
        cls = lookup_class("commercial")
        low = damage_probability_vs_field(cls.damage_threshold_vm * 0.1, cls)
        high = damage_probability_vs_field(cls.damage_threshold_vm * 10.0, cls)
        assert low < 0.5 < high

    def test_steepness_widens_steeper(self) -> None:
        cls = lookup_class("commercial")
        near_hi = damage_probability_vs_field(cls.damage_threshold_vm * 1.2, cls, steepness=2.0)
        near_lo = damage_probability_vs_field(cls.damage_threshold_vm * 1.2, cls, steepness=10.0)
        assert near_lo > near_hi  # steeper -> sharper switch

    def test_negative_field_raises(self) -> None:
        with pytest.raises(ValueError):
            damage_probability_vs_field(-1.0, "unprotected")


class TestFieldConsistency:
    def test_radius_consistent_with_envelope(self) -> None:
        # At the computed radius the envelope must sit at/above the threshold
        # (allowing for bisection rounding, ~1e-3 V/m).
        cls = lookup_class("commercial")
        r = kill_radius_km(WEAPON, cls)
        field = peak_e_field_vm(r, WEAPON.burst_altitude_km, WEAPON.yield_kt)
        assert field >= cls.damage_threshold_vm - 1e-3


class TestKillAreaFractionDegenerate:
    def test_zero_burst_altitude_gives_zero_fraction(self) -> None:
        # A zero-altitude burst has no horizon-limited footprint, so the
        # covered fraction is defined as 0 rather than dividing by zero.
        assert kill_area_fraction(10.0, 0.0) == 0.0

    def test_fraction_is_clamped_to_one(self) -> None:
        assert kill_area_fraction(1.0e9, 300.0) == 1.0
