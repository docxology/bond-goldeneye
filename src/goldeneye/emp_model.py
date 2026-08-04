"""Orbital EMP weapon model — detonation-to-ground effects.

This is one of the three deep-core concept modules of the ARKANGEL mission
(*GoldenEye*, 1995). It models the ground-level electromagnetic field produced
by a high-altitude nuclear burst: geometric propagation from the burst point,
atmospheric absorption of the prompt gamma flux that drives the Compton
electron current, yield scaling, and the canonical E1/E2/E3 HEMP waveform.

The physics is deliberately a *documented conservative envelope*, not a
full distributed-source HEMP field code: the ground field is treated as a
point-source geometry with an exponential absorption term, which produces
a smaller (hence conservative) damage footprint than detailed codes. Every
constant is named and sourced so the model is auditable.

References for the constants and forms:
  * Glasstone & Dolan, *The Effects of Nuclear Weapons*, 3rd ed., 1977
    (prompt-gamma fraction, slow-pulse / E3 amplitudes).
  * IEC 61000-2-9 / MIL-STD-461 early-time (E1) double-exponential waveform.
  * Standard engineering HEMP assessments (50 kV/m E1 reference amplitude at
    megaton-class yield; empirical yield-scaling exponent ~0.85).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "ATMOSPHERE_SCALE_HEIGHT_KM",
    "ATTN_REF_ALTITUDE_KM",
    "ATTN_REF_LENGTH_KM",
    "E1_REFERENCE_VM",
    "E2_AMPLITUDE_FRACTION",
    "E3_REFERENCE_VM",
    "EARTH_RADIUS_KM",
    "EmpWeapon",
    "GAMMA_YIELD_FRACTION",
    "GRAVITATIONAL_ACCELERATION",
    "HEMP_COMPONENTS",
    "HempComponent",
    "REFERENCE_YIELD_KT",
    "VACUUM_PERMITTIVITY",
    "YIELD_SCALING_EXPONENT",
    "component_amplitude_vm",
    "effective_attenuation_length_km",
    "energy_density_jm3",
    "ground_range_to_horizon_km",
    "hemp_waveform",
    "line_of_sight",
    "peak_e_field_at_nadir_vm",
    "peak_e_field_vm",
    "slant_range_km",
    "yield_scaling_factor",
]

# --- Physical constants -------------------------------------------------

#: Mean Earth radius (km) — WGS-84 mean. Used for line-of-sight / horizon.
EARTH_RADIUS_KM = 6371.0

#: Standard gravitational acceleration at Earth's surface (m/s^2).
GRAVITATIONAL_ACCELERATION = 9.80665

#: Vacuum permittivity (F/m) — for field-to-energy-density conversion.
VACUUM_PERMITTIVITY = 8.8541878128e-12

#: Prompt-gamma fraction of total fission yield (~0.3%, Glasstone & Dolan).
GAMMA_YIELD_FRACTION = 0.003

#: Reference yield (kt) at which ``E1_REFERENCE_VM`` is the E1 peak. Starfish
#: Prime (1964, ~1.4 MT at 400 km altitude) measured E1 of tens of kV/m over
#: wide areas; 1000 kt is a clean reference anchor.
REFERENCE_YIELD_KT = 1000.0

#: E1 peak amplitude (V/m) at the reference yield (standard HEMP figure: ~50 kV/m).
E1_REFERENCE_VM = 50000.0

#: Empirical yield-scaling exponent for E1 amplitude.
YIELD_SCALING_EXPONENT = 0.85

#: Reference gamma attenuation length (km) at ``ATTN_REF_ALTITUDE_KM`` —
#: the effective absorption length of the prompt gamma flux in the
#: deposition region (~2 km at ~20 km altitude).
ATTN_REF_LENGTH_KM = 2.0

#: Reference altitude (km) for ``ATTN_REF_LENGTH_KM``.
ATTN_REF_ALTITUDE_KM = 20.0

#: Atmospheric density scale height (km) used to grow the effective
#: attenuation length with burst altitude (thinner air -> less absorption).
ATMOSPHERE_SCALE_HEIGHT_KM = 8.5

#: Intermediate-time (E2) amplitude as a fraction of the local E1 amplitude
#: (representative engineering fraction, documented in the module docstring).
E2_AMPLITUDE_FRACTION = 0.05

#: Late-time magnetohydrodynamic (E3) amplitude reference (V/m) at the
#: reference yield. Glasstone & Dolan report slow-pulse amplitudes of the
#: order of tens of volts per metre.
E3_REFERENCE_VM = 40.0

#: E3 amplitude scales with yield ~ (Y/Y_ref)^0.5 (weak, MHD mechanism).
E3_YIELD_EXPONENT = 0.5


@dataclass(frozen=True)
class EmpWeapon:
    """A high-altitude nuclear EMP weapon.

    Attributes:
        yield_kt: Total weapon yield in kilotons (must be > 0).
        burst_altitude_km: Detonation altitude above the ground (km, must be > 0).
    """

    yield_kt: float
    burst_altitude_km: float

    def __post_init__(self) -> None:
        if not (isinstance(self.yield_kt, (int, float)) and self.yield_kt > 0):
            raise ValueError(f"yield_kt must be > 0, got {self.yield_kt!r}")
        if not (isinstance(self.burst_altitude_km, (int, float)) and self.burst_altitude_km > 0):
            raise ValueError(f"burst_altitude_km must be > 0, got {self.burst_altitude_km!r}")


@dataclass(frozen=True)
class HempComponent:
    """A HEMP pulse component (E1/E2/E3) as a normalized double-exponential.

    The waveform is ``k*(exp(-alpha*t) - exp(-beta*t))`` with ``k`` chosen so
    the peak equals the supplied amplitude. ``alpha``/``beta`` are documented
    per component; ``t_peak_s``/``k`` are derived analytically.
    """

    name: str
    alpha: float
    beta: float
    description: str

    def __post_init__(self) -> None:
        if not (0 < self.alpha < self.beta):
            raise ValueError(f"HEMP component needs 0 < alpha < beta, got {self.alpha}/{self.beta}")
        if not self.name.strip():
            raise ValueError("HEMP component name must be non-empty")

    @property
    def t_peak_s(self) -> float:
        """Time of peak amplitude (s), from ``d/dt`` of the double-exponential."""
        return math.log(self.beta / self.alpha) / (self.beta - self.alpha)

    @property
    def normalization_k(self) -> float:
        """Amplitude normalization so the waveform peak equals the amplitude."""
        tp = self.t_peak_s
        return 1.0 / (math.exp(-self.alpha * tp) - math.exp(-self.beta * tp))


#: The canonical HEMP pulse components. E1 alpha/beta follow IEC 61000-2-9
#: (rise ~5 ns, decay ~50 ns); E2 and E3 are representative intermediate- and
#: late-time pulses (documented in the module docstring).
HEMP_COMPONENTS: tuple[HempComponent, ...] = (
    HempComponent(
        name="E1",
        alpha=4.0e7,
        beta=6.0e8,
        description="early-time pulse (IEC 61000-2-9 parameters, rise ~5 ns)",
    ),
    HempComponent(
        name="E2",
        alpha=1.0e3,
        beta=1.0e5,
        description="intermediate-time pulse (representative)",
    ),
    HempComponent(
        name="E3",
        alpha=0.5,
        beta=1.5,
        description="late-time magnetohydrodynamic pulse (representative)",
    ),
)


def _component(name: str) -> HempComponent:
    for comp in HEMP_COMPONENTS:
        if comp.name == name:
            return comp
    raise ValueError(f"unknown HEMP component {name!r}; expected one of {', '.join(c.name for c in HEMP_COMPONENTS)}")


# --- Geometry --------------------------------------------------------------


def slant_range_km(burst_altitude_km: float, ground_range_km: float) -> float:
    """Slant (line-of-sight) distance from burst to a ground point (km)."""
    return math.hypot(burst_altitude_km, ground_range_km)


def ground_range_to_horizon_km(burst_altitude_km: float) -> float:
    """Ground range (km) to the geometric horizon for a burst at altitude ``h``."""
    h = float(burst_altitude_km)
    return math.sqrt(2.0 * EARTH_RADIUS_KM * h + h * h)


def line_of_sight(burst_altitude_km: float, ground_range_km: float) -> bool:
    """True when the ground point is within line of sight of the burst."""
    return ground_range_km <= ground_range_to_horizon_km(burst_altitude_km)


# --- Source scaling ---------------------------------------------------------


def yield_scaling_factor(yield_kt: float) -> float:
    """Field scaling vs reference yield: ``(Y/Y_ref)**0.85`` (empirical)."""
    return float((float(yield_kt) / REFERENCE_YIELD_KT) ** YIELD_SCALING_EXPONENT)


def effective_attenuation_length_km(burst_altitude_km: float) -> float:
    """Effective gamma attenuation length (km) at a given burst altitude.

    Grows exponentially with altitude (thinner air -> less absorption), so
    high-altitude bursts lose little of the prompt flux along the vacuum path
    between the burst and the atmosphere.
    """
    h = float(burst_altitude_km)
    return ATTN_REF_LENGTH_KM * math.exp((h - ATTN_REF_ALTITUDE_KM) / ATMOSPHERE_SCALE_HEIGHT_KM)


# --- Ground field envelope ---------------------------------------------------


def peak_e_field_at_nadir_vm(burst_altitude_km: float, yield_kt: float) -> float:
    """Peak early-time field (V/m) directly under the burst (nadir)."""
    return E1_REFERENCE_VM * yield_scaling_factor(yield_kt)


def peak_e_field_vm(
    ground_range_km: float,
    burst_altitude_km: float,
    yield_kt: float,
) -> float:
    """Conservative early-time (E1) peak field (V/m) at a ground range.

    Envelope: ``E(r) = E0 * (Y/Y_ref)^0.85 * (h/d)^2 * exp(-(d-h)/lambda(h))``
    with ``d`` the slant range, ``h`` the burst altitude, and ``lambda`` the
    effective attenuation length. Returns ``0.0`` beyond line of sight.
    """
    h = float(burst_altitude_km)
    r = float(ground_range_km)
    if r < 0:
        raise ValueError(f"ground_range_km must be >= 0, got {r!r}")
    if not line_of_sight(h, r):
        return 0.0
    d = slant_range_km(h, r)
    # (h/d)^2 == sin^2(elevation angle): point-source geometric projection.
    geometric = (h / d) ** 2
    lam = effective_attenuation_length_km(h)
    absorption = math.exp(-(d - h) / lam) if lam > 0 else 0.0
    return E1_REFERENCE_VM * yield_scaling_factor(yield_kt) * geometric * absorption


def energy_density_jm3(field_vm: float) -> float:
    """Electromagnetic energy density (J/m^3) for a peak field: 0.5*eps0*E^2."""
    return 0.5 * VACUUM_PERMITTIVITY * float(field_vm) ** 2


# --- HEMP waveform ------------------------------------------------------------


def component_amplitude_vm(
    component: str,
    *,
    yield_kt: float,
    e1_peak_vm: float,
) -> float:
    """Default peak amplitude (V/m) for a pulse component at a location.

    * E1 -> the local envelope peak field (``e1_peak_vm``).
    * E2 -> a fixed fraction of the local E1 peak.
    * E3 -> a weakly yield-scaled late-time amplitude (MHD mechanism).
    """
    if component == "E1":
        return e1_peak_vm
    if component == "E2":
        return E2_AMPLITUDE_FRACTION * e1_peak_vm
    if component == "E3":
        return float(E3_REFERENCE_VM * (float(yield_kt) / REFERENCE_YIELD_KT) ** E3_YIELD_EXPONENT)
    _component(component)  # raises for unknown names
    raise AssertionError("unreachable")


def hemp_waveform(t_s: float, component: str, peak_vm: float) -> float:
    """Double-exponential HEMP waveform amplitude (V/m) at time ``t``.

    ``E(t) = peak * k * (exp(-alpha*t) - exp(-beta*t))`` for ``t >= 0``, else 0.
    ``k`` is chosen so the waveform peak equals ``peak_vm``.
    """
    comp = _component(component)
    if t_s < 0:
        return 0.0
    k = comp.normalization_k
    return float(peak_vm) * k * (math.exp(-comp.alpha * t_s) - math.exp(-comp.beta * t_s))
