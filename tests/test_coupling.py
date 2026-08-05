"""Tests for EM coupling and shielding (goldeneye.coupling)."""

from __future__ import annotations

import math

import pytest

from goldeneye.coupling import (
    COPPER_REFERENCE_CONDUCTIVITY_SM,
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
    surface_impedance_ohm,
)

MU_0 = 1.25663706212e-6
CU_RHO = 1.68e-8
AL_RHO = 2.65e-8
STEEL_RHO = 1.0e-7
STEEL_MU_R = 200.0


def _tabulated_reflection_db(frequency_hz: float, resistivity_ohm_m: float, mu_r: float = 1.0) -> float:
    """Independent second derivation of the plane-wave reflection loss.

    The handbook form ``R = 168 - 10 log10(mu_r f / sigma_r)`` with ``sigma_r``
    the conductivity *relative to annealed copper*. This shares no code with
    :func:`goldeneye.coupling.plane_wave_reflection_db`, which computes the
    impedance ratio ``20 log10(eta_0 / 4|Z_s|)`` instead — so agreement between
    the two is real corroboration, not a restatement.
    """
    sigma_relative = (1.0 / resistivity_ohm_m) / COPPER_REFERENCE_CONDUCTIVITY_SM
    return 168.0 - 10.0 * math.log10(mu_r * frequency_hz / sigma_relative)


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

    def test_se_is_sum(self) -> None:
        t, f, rho = 1e-3, 1.0e8, AL_RHO
        se = schelkunoff_se_db(t, f, rho, 1.0)
        expected = plane_wave_absorption_db(t, skin_depth_m(f, rho, 1.0)) + plane_wave_reflection_db(f, rho, 1.0)
        assert se == pytest.approx(expected)

    def test_aluminum_se_at_e1(self) -> None:
        # 0.1 mm aluminium at 100 MHz — the shipped ARKANGEL enclosure.
        # Hand-computed against the textbook decomposition:
        #   delta = sqrt(2.65e-8/(pi*1e8*mu0)) = 8.193 um
        #   A     = 8.686 * 1e-4 / 8.193e-6    = 106.0 dB
        #   R     = 20*log10(376.73/(4*sqrt(2*pi*1e8*mu0*2.65e-8))) = 86.3 dB
        se = schelkunoff_se_db(1e-4, E1_REPRESENTATIVE_FREQUENCY_HZ, AL_RHO, 1.0)
        assert se == pytest.approx(192.3, abs=0.5)

    def test_thick_aluminum_se_is_absorption_dominated(self) -> None:
        # 1 mm is 10x thicker, so absorption (linear in t) adds ~954 dB.
        se = schelkunoff_se_db(1e-3, E1_REPRESENTATIVE_FREQUENCY_HZ, AL_RHO, 1.0)
        assert se == pytest.approx(1146.5, abs=1.0)

    def test_shielded_field_reduction(self) -> None:
        field = 10616.8
        se = 100.0
        assert shielded_field_vm(field, se) == pytest.approx(field * 10 ** (-se / 20))

    def test_shielded_field_zero_for_high_se(self) -> None:
        assert shielded_field_vm(10616.8, 192.3) < 1e-5


class TestReflectionLoss:
    """The reflection loss must match the physics, not a units-broken formula.

    A prior revision passed the ABSOLUTE conductivity ``sigma = 1/rho`` (S/m)
    into ``R = 168 - 10 log10(mu_r f / sigma)``, a form that is only defined
    for conductivity relative to annealed copper. That inflated every result by
    ``10 log10(sigma_Cu) ~ 78`` dB, and the old test re-derived its expected
    value from the same broken expression. These tests are anchored on values
    that do not come from the implementation.
    """

    #: Published Schelkunoff plane-wave reflection losses (dB) for good
    #: conductors, from the standard EMC tables (Ott 2009, Table 6-4 family).
    TEXTBOOK_DB = {
        ("copper", 1.0e6): 108.0,
        ("copper", 1.0e8): 88.0,
        ("aluminum", 1.0e6): 106.0,
        ("steel", 1.0e6): 77.0,
    }

    def test_matches_published_table(self) -> None:
        for (material, frequency), expected_db in self.TEXTBOOK_DB.items():
            rho, mu_r = lookup_material(material)
            got = plane_wave_reflection_db(frequency, rho, mu_r)
            assert got == pytest.approx(expected_db, abs=0.5), f"{material} @ {frequency:g} Hz"

    def test_agrees_with_independent_relative_conductivity_derivation(self) -> None:
        for material in sorted(MATERIALS):
            rho, mu_r = lookup_material(material)
            for frequency in (1.0e4, 1.0e6, 1.0e8):
                got = plane_wave_reflection_db(frequency, rho, mu_r)
                assert got == pytest.approx(_tabulated_reflection_db(frequency, rho, mu_r), abs=0.2)

    def test_absolute_conductivity_form_is_rejected(self) -> None:
        """Regression pin: the broken form is ~78 dB high, and we are not it."""
        rho, mu_r = lookup_material("copper")
        broken = 168.0 - 10.0 * math.log10(mu_r * 1.0e6 * rho)
        got = plane_wave_reflection_db(1.0e6, rho, mu_r)
        inflation_db = 10.0 * math.log10(COPPER_REFERENCE_CONDUCTIVITY_SM)  # ~77.6 dB
        assert broken - got == pytest.approx(inflation_db, abs=0.3)
        assert got < 120.0, "reflection loss back in the units-broken band"

    def test_surface_impedance_matches_skin_depth_identity(self) -> None:
        # |Z_s| = rho/delta * sqrt(2) is an independent route to the same value.
        rho, mu_r = lookup_material("steel")
        delta = skin_depth_m(1.0e6, rho, mu_r)
        assert surface_impedance_ohm(1.0e6, rho, mu_r) == pytest.approx(math.sqrt(2.0) * rho / delta, rel=1e-9)

    def test_falls_with_frequency_and_permeability(self) -> None:
        low = plane_wave_reflection_db(1.0e4, CU_RHO)
        high = plane_wave_reflection_db(1.0e8, CU_RHO)
        assert low - high == pytest.approx(40.0, abs=1e-6)  # -10 dB per decade
        assert plane_wave_reflection_db(1.0e6, STEEL_RHO, STEEL_MU_R) < plane_wave_reflection_db(1.0e6, STEEL_RHO)


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


class TestGuardsActuallyFire:
    """Every validation guard must be provably reachable, not decorative."""

    def test_absorption_rejects_non_positive_skin_depth(self) -> None:
        with pytest.raises(ValueError, match="skin_depth_m > 0"):
            plane_wave_absorption_db(0.001, 0.0)

    def test_absorption_rejects_negative_thickness(self) -> None:
        with pytest.raises(ValueError, match="thickness_m >= 0"):
            plane_wave_absorption_db(-1.0, 1e-6)

    def test_reflection_rejects_non_positive_frequency(self) -> None:
        with pytest.raises(ValueError, match="must all be > 0"):
            plane_wave_reflection_db(0.0, 2.65e-8)

    def test_reflection_rejects_non_positive_resistivity(self) -> None:
        with pytest.raises(ValueError, match="must all be > 0"):
            plane_wave_reflection_db(1.0e8, 0.0)

    def test_induced_voltage_rejects_negative_effective_height(self) -> None:
        with pytest.raises(ValueError, match="effective_height_m must be >= 0"):
            induced_voltage_v(1000.0, -0.5)
