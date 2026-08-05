"""Electromagnetic coupling and shielding — infrastructure vulnerability.

The EMP threat reaches electronics through two paths: directly coupled fields
on conductors (antennas, cables, overhead lines) and penetration through
enclosures. This module implements the deterministic classical tools:

* **Skin depth** — ``delta = sqrt(rho / (pi f mu0 mu_r))``, the standard
  field-penetration length in a conductor;
* **Schelkunoff shielding effectiveness** — plane-wave absorption loss
  ``A = 8.686 t/delta`` dB plus plane-wave reflection loss
  ``R = 20 log10(|eta_0| / (4 |Z_s|))`` dB, with the free-space wave impedance
  ``eta_0`` and the conductor surface impedance magnitude
  ``|Z_s| = sqrt(2 pi f mu0 mu_r rho)`` (neglecting the multiple-reflection
  correction, which is negligible for thick shields);
* **Conductor coupling** — induced open-circuit voltage ``V = E * h_eff``
  where the effective height is the conductor length projected onto the
  incident field direction (``h_eff = L sin(elevation)``);
* **Protection margin** — ``20 log10(withstand/field)`` dB.

The reflection loss is written in its primitive impedance-ratio form rather
than the tabulated shortcut ``R = 168 - 10 log10(mu_r f / sigma)``. That
shortcut is only valid when ``sigma`` is the conductivity **relative to
annealed copper** (dimensionless, ~1 for copper, ~0.65 for aluminium); feeding
it an absolute conductivity in S/m inflates the result by
``10 log10(sigma_Cu) ~ 78`` dB. Both forms agree to ~0.15 dB — see
``tests/test_coupling.py::TestReflectionLoss``, which cross-checks them and
pins the textbook value (copper at 1 MHz: ~108 dB, not ~186 dB).

Constants and forms follow the classical EMC literature: Ott,
*Electromagnetic Compatibility Engineering*, 2009, and Vance, *Coupling to
Shielded Cables*, 1978. All functions are closed-form and deterministic.
"""

from __future__ import annotations

import math

__all__ = [
    "ABSORPTION_DB_PER_SKIN_DEPTH",
    "COPPER_REFERENCE_CONDUCTIVITY_SM",
    "E1_REPRESENTATIVE_FREQUENCY_HZ",
    "FREE_SPACE_IMPEDANCE_OHM",
    "MATERIALS",
    "conducted_current_a",
    "effective_height_m",
    "induced_voltage_v",
    "lookup_material",
    "plane_wave_absorption_db",
    "plane_wave_reflection_db",
    "protection_margin_db",
    "schelkunoff_se_db",
    "shielded_field_vm",
    "skin_depth_m",
    "surface_impedance_ohm",
]

#: Vacuum permeability (H/m).
MU_0 = 1.25663706212e-6

#: Free-space (plane-wave) impedance eta_0 = sqrt(mu_0/eps_0), in ohm. This is
#: the wave impedance ``|Z_w|`` in the Schelkunoff reflection-loss ratio.
FREE_SPACE_IMPEDANCE_OHM = 376.730313412

#: dB per skin depth of absorption loss: ``20/ln(10) = 8.686``.
ABSORPTION_DB_PER_SKIN_DEPTH = 8.686

#: Conductivity of annealed copper (S/m, the IACS reference). Used *only* to
#: express the tabulated relative-conductivity form of the reflection loss;
#: the shipped implementation does not need it.
COPPER_REFERENCE_CONDUCTIVITY_SM = 5.8e7

#: Representative E1 spectral frequency (Hz) — the early-time pulse's energy
#: is concentrated around tens-to-hundreds of MHz; 100 MHz is the canonical
#: engineering reference (IEC 61000-2-9 spectral content).
E1_REPRESENTATIVE_FREQUENCY_HZ = 1.0e8

#: Shield materials: name -> (resistivity Ohm*m, relative permeability).
MATERIALS: dict[str, tuple[float, float]] = {
    "aluminum": (2.65e-8, 1.0),
    "copper": (1.68e-8, 1.0),
    "steel": (1.0e-7, 200.0),
}


def lookup_material(name: str) -> tuple[float, float]:
    """Return ``(resistivity_ohm_m, relative_permeability)`` for a material."""
    try:
        return MATERIALS[name]
    except KeyError:
        raise KeyError(f"unknown shield material {name!r}; expected one of {', '.join(sorted(MATERIALS))}") from None


def skin_depth_m(frequency_hz: float, resistivity_ohm_m: float, relative_permeability: float = 1.0) -> float:
    """Conductor skin depth (m): sqrt(rho / (pi f mu0 mu_r))."""
    f = float(frequency_hz)
    rho = float(resistivity_ohm_m)
    mu_r = float(relative_permeability)
    if f <= 0 or rho <= 0 or mu_r <= 0:
        raise ValueError("frequency_hz, resistivity_ohm_m, relative_permeability must all be > 0")
    return float(math.sqrt(rho / (math.pi * f * MU_0 * mu_r)))


def plane_wave_absorption_db(thickness_m: float, skin_depth_m_value: float) -> float:
    """Schelkunoff plane-wave absorption loss (dB): 8.686 * t / delta."""
    t = float(thickness_m)
    delta = float(skin_depth_m_value)
    if t < 0 or delta <= 0:
        raise ValueError(f"thickness_m >= 0 and skin_depth_m > 0 required, got {t!r}/{delta!r}")
    return float(ABSORPTION_DB_PER_SKIN_DEPTH * t / delta)


def surface_impedance_ohm(frequency_hz: float, resistivity_ohm_m: float, relative_permeability: float = 1.0) -> float:
    """Magnitude of the conductor surface impedance (ohm/square).

    ``Z_s = (1+j) sqrt(pi f mu rho)``, so ``|Z_s| = sqrt(2 pi f mu0 mu_r rho)``.
    This is the good-conductor limit used by the Schelkunoff reflection loss.
    """
    f = float(frequency_hz)
    rho = float(resistivity_ohm_m)
    mu_r = float(relative_permeability)
    if f <= 0 or rho <= 0 or mu_r <= 0:
        raise ValueError("frequency_hz, resistivity_ohm_m, relative_permeability must all be > 0")
    return float(math.sqrt(2.0 * math.pi * f * MU_0 * mu_r * rho))


def plane_wave_reflection_db(
    frequency_hz: float, resistivity_ohm_m: float, relative_permeability: float = 1.0
) -> float:
    """Schelkunoff plane-wave reflection loss (dB): ``20 log10(eta_0 / (4 |Z_s|))``.

    Equivalent (to ~0.15 dB) to the tabulated ``168 - 10 log10(mu_r f/sigma_r)``
    with ``sigma_r`` the conductivity *relative to annealed copper*. The
    impedance-ratio form is used here because it carries its units explicitly:
    the tabulated form silently inflates the loss by ~78 dB if handed an
    absolute conductivity in S/m.
    """
    z_s = surface_impedance_ohm(frequency_hz, resistivity_ohm_m, relative_permeability)
    return float(20.0 * math.log10(FREE_SPACE_IMPEDANCE_OHM / (4.0 * z_s)))


def schelkunoff_se_db(
    thickness_m: float,
    frequency_hz: float,
    resistivity_ohm_m: float,
    relative_permeability: float = 1.0,
) -> float:
    """Total plane-wave shielding effectiveness (dB): absorption + reflection.

    The multiple-reflection correction is neglected (documented: negligible
    for shields several skin depths thick).
    """
    delta = skin_depth_m(frequency_hz, resistivity_ohm_m, relative_permeability)
    absorption = plane_wave_absorption_db(thickness_m, delta)
    reflection = plane_wave_reflection_db(frequency_hz, resistivity_ohm_m, relative_permeability)
    return float(absorption + reflection)


def shielded_field_vm(field_vm: float, se_db: float) -> float:
    """Field (V/m) behind a shield of effectiveness ``se_db``."""
    return float(float(field_vm) * 10.0 ** (-float(se_db) / 20.0))


def effective_height_m(conductor_length_m: float, elevation_angle_deg: float) -> float:
    """Effective height (m) of a conductor of length ``L`` in a field arriving
    at elevation ``elevation_angle_deg``: ``L * sin(elevation)``."""
    length = float(conductor_length_m)
    if length <= 0:
        raise ValueError(f"conductor_length_m must be > 0, got {length!r}")
    if not 0.0 <= float(elevation_angle_deg) <= 90.0:
        raise ValueError(f"elevation_angle_deg must be in [0, 90], got {elevation_angle_deg!r}")
    return float(length * math.sin(math.radians(float(elevation_angle_deg))))


def induced_voltage_v(field_vm: float, effective_height_m_value: float) -> float:
    """Open-circuit voltage (V) induced on a conductor: ``E * h_eff``."""
    if field_vm < 0:
        raise ValueError(f"field_vm must be >= 0, got {field_vm!r}")
    if effective_height_m_value < 0:
        raise ValueError(f"effective_height_m must be >= 0, got {effective_height_m_value!r}")
    return float(field_vm) * float(effective_height_m_value)


def conducted_current_a(voltage_v: float, impedance_ohm: float) -> float:
    """Conducted current (A) into a load of ``impedance_ohm``: ``V / Z``."""
    z = float(impedance_ohm)
    if z <= 0:
        raise ValueError(f"impedance_ohm must be > 0, got {z!r}")
    return float(voltage_v) / z


def protection_margin_db(withstand_vm: float, field_vm: float) -> float:
    """Protection margin (dB): ``20 log10(withstand/field)``.

    Positive margins mean the device withstands the local field; negative
    margins mean the field exceeds the withstand level.
    """
    w = float(withstand_vm)
    f = float(field_vm)
    if w <= 0 or f <= 0:
        raise ValueError("withstand_vm and field_vm must both be > 0")
    return float(20.0 * math.log10(w / f))
