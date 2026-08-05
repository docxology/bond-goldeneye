"""Tests for the orbital EMP weapon model (goldeneye.emp_model).

Zero-mock, real-math tests: geometry exactness, the conservative field
envelope's analytic limits, waveform normalization, and the component registry.
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest

from goldeneye.emp_model import (
    ATTN_REF_ALTITUDE_KM,
    ATTN_REF_LENGTH_KM,
    E1_REFERENCE_VM,
    HEMP_COMPONENTS,
    REFERENCE_YIELD_KT,
    YIELD_SCALING_EXPONENT,
    HempComponent,
    EmpWeapon,
    component_amplitude_vm,
    effective_attenuation_length_km,
    energy_density_jm3,
    ground_range_to_horizon_km,
    hemp_waveform,
    line_of_sight,
    peak_e_field_at_nadir_vm,
    peak_e_field_vm,
    slant_range_km,
    yield_scaling_factor,
)


class TestGeometry:
    def test_slant_range_pythagorean(self) -> None:
        assert slant_range_km(3.0, 4.0) == pytest.approx(5.0)

    def test_slant_range_at_nadir(self) -> None:
        assert slant_range_km(300.0, 0.0) == pytest.approx(300.0)

    def test_horizon_at_nadir_is_zero(self) -> None:
        assert ground_range_to_horizon_km(0.0) == pytest.approx(0.0)

    def test_horizon_increases_with_altitude(self) -> None:
        lo = ground_range_to_horizon_km(100.0)
        hi = ground_range_to_horizon_km(400.0)
        assert hi > lo > 0

    def test_horizon_known_value(self) -> None:
        # sqrt(2*6371*300 + 300^2) for the ARKANGEL burst altitude.
        assert ground_range_to_horizon_km(300.0) == pytest.approx(1978.0, rel=1e-3)

    def test_line_of_sight_boundary_inclusive(self) -> None:
        h = 300.0
        assert line_of_sight(h, ground_range_to_horizon_km(h))
        assert line_of_sight(h, ground_range_to_horizon_km(h) + 1.0) is False


class TestSourceScaling:
    def test_yield_scaling_reference_is_one(self) -> None:
        assert yield_scaling_factor(REFERENCE_YIELD_KT) == pytest.approx(1.0)

    def test_yield_scaling_power_law(self) -> None:
        # (2/1)^0.85
        assert yield_scaling_factor(2.0 * 1.0) / yield_scaling_factor(1.0) == pytest.approx(2.0**YIELD_SCALING_EXPONENT)

    def test_attenuation_length_equals_reference_at_reference_altitude(self) -> None:
        assert effective_attenuation_length_km(ATTN_REF_ALTITUDE_KM) == pytest.approx(ATTN_REF_LENGTH_KM)

    def test_attenuation_length_grows_with_altitude(self) -> None:
        assert effective_attenuation_length_km(300.0) > effective_attenuation_length_km(25.0)


class TestEnvelope:
    def test_nadir_equals_reference_times_scaling(self) -> None:
        nadir = peak_e_field_at_nadir_vm(300.0, REFERENCE_YIELD_KT)
        assert nadir == pytest.approx(E1_REFERENCE_VM)

    def test_nadir_at_scenario(self) -> None:
        # 2 Mt -> (2)^0.85, so ~90.1 kV/m at nadir.
        nadir = peak_e_field_at_nadir_vm(300.0, 2000.0)
        assert nadir == pytest.approx(E1_REFERENCE_VM * 2.0**YIELD_SCALING_EXPONENT)

    def test_field_at_nadir_equals_peak(self) -> None:
        assert peak_e_field_vm(0.0, 300.0, 2000.0) == pytest.approx(peak_e_field_at_nadir_vm(300.0, 2000.0))

    def test_field_monotone_decreasing_in_range(self) -> None:
        h, y = 300.0, 2000.0
        fields = [peak_e_field_vm(r, h, y) for r in (0.0, 100.0, 400.0, 900.0)]
        assert all(a > b for a, b in zip(fields, fields[1:]))

    def test_field_zero_beyond_horizon(self) -> None:
        assert peak_e_field_vm(ground_range_to_horizon_km(300.0) + 10.0, 300.0, 2000.0) == 0.0

    def test_field_positive_inside(self) -> None:
        assert peak_e_field_vm(500.0, 300.0, 2000.0) > 0.0

    def test_low_altitude_absorption_suppresses_field(self) -> None:
        # At 20 km the exponential absorption dramatically cuts a wide field.
        low = peak_e_field_vm(50.0, 22.0, 2000.0)
        high = peak_e_field_vm(50.0, 300.0, 2000.0)
        assert low < high

    def test_negative_range_raises(self) -> None:
        with pytest.raises(ValueError):
            peak_e_field_vm(-1.0, 300.0, 2000.0)

    def test_energy_density_is_quadratic(self) -> None:
        assert energy_density_jm3(2.0) == pytest.approx(4.0 * energy_density_jm3(1.0))
        assert energy_density_jm3(0.0) == 0.0


class TestWeaponValidation:
    def test_nonpositive_yield_raises(self) -> None:
        with pytest.raises(ValueError):
            EmpWeapon(yield_kt=0.0, burst_altitude_km=300.0)
        with pytest.raises(ValueError):
            EmpWeapon(yield_kt=-5.0, burst_altitude_km=300.0)

    def test_nonpositive_altitude_raises(self) -> None:
        with pytest.raises(ValueError):
            EmpWeapon(yield_kt=2000.0, burst_altitude_km=0.0)

    def test_valid_weapon(self) -> None:
        w = EmpWeapon(yield_kt=2000.0, burst_altitude_km=300.0)
        assert w.yield_kt == 2000.0
        assert w.burst_altitude_km == 300.0


class TestWaveform:
    def test_waveform_peak_equals_amplitude(self) -> None:
        comp = HEMP_COMPONENTS[0]  # E1
        t_pk = comp.t_peak_s
        samples = [t_pk + dt for dt in (-1e-9, 0.0, 1e-9)]
        amplitude = 50000.0
        max_amp = max(hemp_waveform(t, comp.name, amplitude) for t in samples)
        # The double-exponential peak reaches (very near) the supplied amplitude.
        assert max_amp == pytest.approx(amplitude, rel=1e-2)

    def test_waveform_nonnegative(self) -> None:
        for t in (0.0, 1e-9, 1e-3, 1.0):
            assert hemp_waveform(t, "E1", 100.0) >= 0.0

    def test_waveform_zero_before_zero(self) -> None:
        assert hemp_waveform(-1.0, "E1", 100.0) == 0.0

    def test_e1_rise_time_about_five_ns(self) -> None:
        comp = next(c for c in HEMP_COMPONENTS if c.name == "E1")
        assert 1e-9 < comp.t_peak_s < 2e-8  # ~5 ns documented rise

    def test_e3_is_slow(self) -> None:
        comp = next(c for c in HEMP_COMPONENTS if c.name == "E3")
        assert 0.5 < comp.t_peak_s < 5.0  # seconds

    def test_unknown_component_raises(self) -> None:
        with pytest.raises(ValueError):
            hemp_waveform(1e-9, "NOPE", 100.0)

    def test_component_normalization_matches_iec(self) -> None:
        # IEC 61000-2-9 uses k ~ 1.3 for the E1 double-exponential.
        comp = next(c for c in HEMP_COMPONENTS if c.name == "E1")
        assert comp.normalization_k == pytest.approx(1.3, rel=0.1)

    def test_component_amplitude_e1_is_local_peak(self) -> None:
        assert component_amplitude_vm("E1", yield_kt=2000.0, e1_peak_vm=90000.0) == pytest.approx(90000.0)

    def test_component_amplitude_e2_is_fraction(self) -> None:
        assert component_amplitude_vm("E2", yield_kt=2000.0, e1_peak_vm=1000.0) == pytest.approx(0.05 * 1000.0)

    def test_component_amplitude_e3_yield_scaled(self) -> None:
        base = component_amplitude_vm("E3", yield_kt=REFERENCE_YIELD_KT, e1_peak_vm=0.0)
        scaled = component_amplitude_vm("E3", yield_kt=4.0 * REFERENCE_YIELD_KT, e1_peak_vm=0.0)
        assert scaled == pytest.approx(base * 2.0)  # ^0.5 with 4x yield

    def test_component_amplitude_unknown_raises(self) -> None:
        with pytest.raises(ValueError):
            component_amplitude_vm("NOPE", yield_kt=2000.0, e1_peak_vm=1.0)


class TestComponentDataclass:
    def test_alpha_lt_beta_enforced(self) -> None:
        with pytest.raises(ValueError):
            HempComponent(name="x", alpha=5.0, beta=1.0, description="bad")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            HempComponent(name=" ", alpha=1.0, beta=2.0, description="bad")

    def test_t_peak_positive(self) -> None:
        comp = next(c for c in HEMP_COMPONENTS if c.name == "E2")
        assert comp.t_peak_s > 0.0


def test_math_consistency_guard() -> None:
    """A deterministic invariant linking the geometry and the horizon."""
    h = 300.0
    r_h = ground_range_to_horizon_km(h)
    d = slant_range_km(h, r_h)
    # At the horizon the slant range must exceed the burst altitude.
    assert d > h
    assert math.isfinite(d)


class TestGammaFractionIsReportedNotConsumed:
    """`GAMMA_YIELD_FRACTION` is documentation, and the docs must say so.

    The manuscript previously listed the prompt-gamma fraction among the
    parameters of the field envelope. It is not one: the envelope is anchored
    empirically at ``E1_REFERENCE_VM``. This test enforces the corrected,
    weaker claim by mutating the constant in a fresh interpreter and showing
    every computed field is byte-identical — and it carries a positive control
    so the mutation harness cannot silently no-op.
    """

    _PROBE = (
        "import goldeneye.emp_model as m\n"
        "probes = lambda: (\n"
        "    m.peak_e_field_at_nadir_vm(300.0, 2000.0),\n"
        "    m.peak_e_field_vm(500.0, 300.0, 2000.0),\n"
        "    m.yield_scaling_factor(2000.0),\n"
        "    m.effective_attenuation_length_km(300.0),\n"
        "    m.component_amplitude_vm('E3', yield_kt=2000.0, e1_peak_vm=1.0),\n"
        ")\n"
        "before = probes()\n"
        "m.GAMMA_YIELD_FRACTION = 0.5\n"
        "assert probes() == before, 'gamma fraction DOES feed the envelope'\n"
        "# Positive control: a constant that IS consumed must move the result.\n"
        "m.E1_REFERENCE_VM = 1.0\n"
        "assert probes() != before, 'mutation harness is inert — gate vacuous'\n"
        "print('gamma-unused-ok')\n"
    )

    def test_mutating_gamma_fraction_changes_no_field(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c", self._PROBE],
            cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "gamma-unused-ok" in proc.stdout

    def test_constant_is_not_read_by_any_module_function(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "src/goldeneye/emp_model.py").read_text(encoding="utf-8")
        # Definition, __all__ entry, and docstring mentions only — no call site.
        code_lines = [
            line for line in source.splitlines() if "GAMMA_YIELD_FRACTION" in line and not line.lstrip().startswith("#")
        ]
        assert code_lines == ['    "GAMMA_YIELD_FRACTION",', "GAMMA_YIELD_FRACTION = 0.003"], code_lines
