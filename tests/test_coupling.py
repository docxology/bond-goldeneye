"""Tests for EM coupling and shielding (goldeneye.coupling)."""

from __future__ import annotations

import math

import pytest

from goldeneye.coupling import (
    E1_REPRESENTATIVE_FREQUENCY_HZ,
    MATERIALS,
    conducted_current_a,
    effective_height_m,
    induced_voltage_v,
    lookup_material,
    plane_wave_absorption_db,
    plane_wave_reflection_db,
    protection_margin_db,
    schelkunoff_se_db,
    shielded_field_vm,
    skin_depth_m,
)

MU_0 = 1.25663706212e-6
CU_RHO = 1.68e-8
AL_RHO = 2.65e-8


class TestSkinDepth:
    def test_copper_at_one_mhz(self) -> None:
        # Known vector: copper skin depth at 1 MHz ~ 66 micrometres.
        delta = skin_depth_m(1.0e6, CU_RHO, 1.0)
        assert delta == pytest.approx(math.sqrt(CU_RHO / (math.pi * 1.0e6 * MU_0)), rel=1e-6)
        assert 5.0e-5 < delta < 8.0e-5

    def test_deeper_at_lower_frequency(self) -> None:
        assert skin_depth_m(1.0e3, CU_RHO) > skin_depth_m(1.0e6, CU_RHO)

    def test_higher_permeability_thins_skin(self) -> None:
        assert skin_depth_m(1.0e6, CU_RHO, 200.0) < skin_depth_m(1.0e6, CU_RHO, 1.0)

    def test_invalid_inputs(self) -> None:
        with pytest.raises(ValueError):
            skin_depth_m(0.0, CU_RHO)
        with pytest.raises(ValueError):
            skin_depth_m(1e6, 0.0)
        with pytest.raises(ValueError):
            skin_depth_m(1e6, CU_RHO, -1.0)


class TestShieldingEffectiveness:
    def test_absorption_is_linear_in_thickness(self) -> None:
        delta = 1e-3
        a1 = plane_wave_absorption_db(1e-3, delta)
        a2 = plane_wave_absorption_db(2e-3, delta)
        assert a2 == pytest.approx(2.0 * a1)

    def test_absorption_formula(self) -> None:
        assert plane_wave_absorption_db(1e-3, 5e-4) == pytest.approx(8.686 * (1e-3 / 5e-4))

    def test_reflection_copper_one_mhz(self) -> None:
        # ~168 - 10*log10(mu_r f / sigma); for Cu sigma=5.95e7 this is ~185 dB.
        refl = plane_wave_reflection_db(1.0e6, CU_RHO, 1.0)
        sigma = 1.0 / CU_RHO
        assert refl == pytest.approx(168.0 - 10.0 * math.log10(1.0e6 / sigma), rel=1e-6)
        assert 170.0 < refl < 200.0

    def test_se_is_sum(self) -> None:
        t, f, rho = 1e-3, 1.0e8, AL_RHO
        se = schelkunoff_se_db(t, f, rho, 1.0)
        expected = plane_wave_absorption_db(t, skin_depth_m(f, rho, 1.0)) + plane_wave_reflection_db(f, rho, 1.0)
        assert se == pytest.approx(expected)

    def test_aluminum_se_at_e1(self) -> None:
        # 1 mm aluminum at 100 MHz -> hundreds of dB (effectively impenetrable).
        se = schelkunoff_se_db(1e-3, E1_REPRESENTATIVE_FREQUENCY_HZ, AL_RHO, 1.0)
        assert se > 200.0

    def test_shielded_field_reduction(self) -> None:
        field = 10616.8
        se = 100.0
        assert shielded_field_vm(field, se) == pytest.approx(field * 10 ** (-se / 20))

    def test_shielded_field_zero_for_high_se(self) -> None:
        assert shielded_field_vm(10616.8, 269.8) < 1e-5


class TestConductorCoupling:
    def test_effective_height_projection(self) -> None:
        # 10 m conductor at 30 deg elevation -> 5 m.
        assert effective_height_m(10.0, 30.0) == pytest.approx(5.0)

    def test_effective_height_nadir(self) -> None:
        assert effective_height_m(10.0, 90.0) == pytest.approx(10.0)

    def test_induced_voltage(self) -> None:
        # V = E * h_eff: 10 kV/m * 3.22 m ~ 32.2 kV.
        assert induced_voltage_v(10000.0, 3.223) == pytest.approx(32230.0)

    def test_conducted_current(self) -> None:
        assert conducted_current_a(34218.0, 50.0) == pytest.approx(684.36)

    def test_protection_margin(self) -> None:
        # 20*log10(withstand/field): 100 vs 10 -> 20 dB.
        assert protection_margin_db(100.0, 10.0) == pytest.approx(20.0)

    def test_negative_margin_when_field_exceeds_withstand(self) -> None:
        assert protection_margin_db(10.0, 100.0) < 0.0

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            effective_height_m(0.0, 30.0)
        with pytest.raises(ValueError):
            effective_height_m(10.0, 120.0)
        with pytest.raises(ValueError):
            induced_voltage_v(-1.0, 3.0)
        with pytest.raises(ValueError):
            conducted_current_a(10.0, 0.0)
        with pytest.raises(ValueError):
            protection_margin_db(0.0, 10.0)
        with pytest.raises(ValueError):
            protection_margin_db(10.0, 0.0)


class TestMaterials:
    def test_names(self) -> None:
        assert set(MATERIALS) == {"aluminum", "copper", "steel"}

    def test_aluminum_parameters(self) -> None:
        rho, mu_r = lookup_material("aluminum")
        assert rho == pytest.approx(2.65e-8)
        assert mu_r == pytest.approx(1.0)

    def test_steel_high_permeability(self) -> None:
        rho, mu_r = lookup_material("steel")
        assert mu_r == pytest.approx(200.0)

    def test_unknown_material_raises(self) -> None:
        with pytest.raises(KeyError):
            lookup_material("lead")
