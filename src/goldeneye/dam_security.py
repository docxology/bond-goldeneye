"""Arkangel dam-facility security: access control and breach flood risk.

The ARKANGEL facility (*GoldenEye*, 1995) is hidden inside a large dam (filmed
at the Contra Dam, Verzasca, Switzerland; the story relocates it to the
Siberian Arkangel area). This module models two distinct security surfaces:

1. **Access control (defense-in-depth)** — a layered cascade of security zones
   (outer perimeter, checkpoint, inner perimeter, control room), each with a
   per-pass detection probability and a response time. The probability that an
   intruder is detected at least once, the expected response time to first
   detection, and a composite security score follow directly from the classic
   defense-in-depth formula ``1 - prod(1 - p_i)``.

2. **Breach flood risk** — if the dam is breached, the reservoir releases a
   dam-break flood wave. Peak outflow follows the published Froehlich (1995)
   embankment-dam regression; the downstream flood wave is modelled with the
   classical Ritter (1892) instantaneous-dam-break solution on a dry bed
   (frictionless), giving exact closed-form depth/velocity/arrival-time
   expressions. A facility downstream is assessed for peak inundation depth,
   arrival time, and a flood-risk rating.

All models are deterministic and closed-form; every constant is documented.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "DEFAULT_ACCESS_LAYERS",
    "SecurityLayer",
    "Reservoir",
    "access_corridor",
    "breach_peak_discharge_cms",
    "cumulative_detection_probability",
    "expected_detection_time_min",
    "flood_arrival_time_s",
    "flood_depths_at_distance",
    "flood_risk_rating",
    "lookup_layer",
    "peak_depth_at_distance_m",
    "ritter_celerity_ms",
    "ritter_depth_m",
    "ritter_front_speed_ms",
    "ritter_velocity_ms",
    "security_score",
    "severity_ratio",
]

#: Gravitational acceleration (m/s^2) — matches emp_model.GRAVITATIONAL_ACCELERATION.
GRAVITY = 9.80665

#: Reference detection probability for the security-score numerator.
REFERENCE_DETECTION_PROBABILITY = 1.0

#: Reference response time (min) used to normalize the security score.
REFERENCE_RESPONSE_TIME_MIN = 60.0

#: Upstream / downstream depth muliplier used by ``peak_depth_at_distance_m``:
#: the Ritter solution relaxes to ``4H/9`` at the dam site and asymptotically
#: downstream.
RITTER_DEPTH_COEFFICIENT = 4.0 / 9.0


@dataclass(frozen=True)
class SecurityLayer:
    """A single defense-in-depth layer of the facility access model.

    Attributes:
        name: Machine-readable layer slug.
        detection_probability: Per-pass probability of detecting an intruder
            (0 < p <= 1).
        response_time_min: Time (min) for the layer's response once triggered.
        barrier: Human-readable description of the layer's barrier.
    """

    name: str
    detection_probability: float
    response_time_min: float
    barrier: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("SecurityLayer.name must be non-empty")
        if not (0.0 < self.detection_probability <= 1.0):
            raise ValueError(f"detection_probability must be in (0, 1], got {self.detection_probability!r}")
        if self.response_time_min <= 0:
            raise ValueError(f"response_time_min must be > 0, got {self.response_time_min!r}")


#: Canonical access-control cascade for the ARKANGEL facility.
DEFAULT_ACCESS_LAYERS: tuple[SecurityLayer, ...] = (
    SecurityLayer(
        name="outer_perimeter",
        detection_probability=0.35,
        response_time_min=10.0,
        barrier="patrolled perimeter fence",
    ),
    SecurityLayer(
        name="checkpoint",
        detection_probability=0.60,
        response_time_min=5.0,
        barrier="armed guard post + ID verification",
    ),
    SecurityLayer(
        name="inner_perimeter",
        detection_probability=0.50,
        response_time_min=4.0,
        barrier="camera zone + hardened lock",
    ),
    SecurityLayer(
        name="control_room",
        detection_probability=0.90,
        response_time_min=2.0,
        barrier="biometric access to mission control",
    ),
)

_LAYER_INDEX: dict[str, SecurityLayer] = {l.name: l for l in DEFAULT_ACCESS_LAYERS}


def lookup_layer(name: str) -> SecurityLayer:
    """Return a default access layer by ``name`` or raise ``KeyError``."""
    try:
        return _LAYER_INDEX[name]
    except KeyError:
        raise KeyError(f"unknown access layer {name!r}; expected one of {', '.join(_LAYER_INDEX)}") from None


@dataclass(frozen=True)
class Reservoir:
    """A dam reservoir for the breach-flood model.

    Attributes:
        name: Reservoir identifier.
        volume_m3: Stored water volume (m^3, must be > 0).
        head_m: Water head (height) above the breach invert (m, must be > 0).
    """

    name: str
    volume_m3: float
    head_m: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Reservoir.name must be non-empty")
        if self.volume_m3 <= 0:
            raise ValueError(f"volume_m3 must be > 0, got {self.volume_m3!r}")
        if self.head_m <= 0:
            raise ValueError(f"head_m must be > 0, got {self.head_m!r}")


# --- Access control ----------------------------------------------------------


def cumulative_detection_probability(layers: tuple[SecurityLayer, ...]) -> float:
    """Probability an intruder is detected by at least one layer (defense-in-depth)."""
    p_miss = 1.0
    for layer in layers:
        p_miss *= 1.0 - layer.detection_probability
    return 1.0 - p_miss


def expected_detection_time_min(layers: tuple[SecurityLayer, ...]) -> float:
    """Expected response time (min) to the first layer that detects.

    The detection is observed at the response time of the first layer in the
    cascade that fires; layers before it (which did not detect) do not respond.
    Expectation is conditional on detection happening; if no layer can detect,
    returns the sum of all response times (worst-case bound).
    """
    # Probability of no detection before layer i, times P(detect at i) * t_i.
    p_miss_before = 1.0
    total = 0.0
    p_detect_any = 0.0
    for layer in layers:
        p_first = p_miss_before * layer.detection_probability
        total += p_first * layer.response_time_min
        p_detect_any += p_first
        p_miss_before *= 1.0 - layer.detection_probability
    if p_detect_any <= 0.0:
        # Defensive only: unreachable while SecurityLayer enforces
        # detection_probability in (0, 1], so p_detect_any is always > 0.
        # Retained so relaxing that invariant cannot introduce a zero divide.
        return sum(layer.response_time_min for layer in layers)
    return total / p_detect_any


def security_score(
    layers: tuple[SecurityLayer, ...],
    *,
    ref_detection: float = REFERENCE_DETECTION_PROBABILITY,
    ref_time_min: float = REFERENCE_RESPONSE_TIME_MIN,
) -> float:
    """Composite facility security score in [0, 100].

    ``100 * P_detect * ref_time / (ref_time + E[first detection time])`` —
    a deterministic weighted blend of coverage and responsiveness.
    """
    p = cumulative_detection_probability(layers)
    t = expected_detection_time_min(layers)
    return 100.0 * (p / ref_detection) * (ref_time_min / (ref_time_min + t))


def access_corridor(
    name: str,
    layers: tuple[SecurityLayer, ...] = DEFAULT_ACCESS_LAYERS,
    *,
    extra_names: tuple[str, ...] = (),
) -> tuple[tuple[SecurityLayer, ...], float]:
    """Return a corridor (named layer plus extras, in cascade order) and its
    cumulative detection probability.

    The ``name`` layer must exist in ``layers``; ``extra_names`` are appended
    in the order given and must likewise exist.
    """
    selected: list[SecurityLayer] = []
    pool = {layer.name: layer for layer in layers}
    for n in (name, *extra_names):
        if n not in pool:
            raise KeyError(f"unknown access layer {n!r} in corridor")
        selected.append(pool[n])
    corridor = tuple(selected)
    return corridor, cumulative_detection_probability(corridor)


# --- Breach flood model ------------------------------------------------------


def ritter_celerity_ms(head_m: float) -> float:
    """Shallow-water wave celerity ``c0 = sqrt(g*H)`` (m/s)."""
    return math.sqrt(GRAVITY * float(head_m))


def ritter_front_speed_ms(head_m: float) -> float:
    """Dam-break wave front speed ``2*c0`` (m/s), Ritter instantaneous solution."""
    return 2.0 * ritter_celerity_ms(head_m)


def breach_peak_discharge_cms(volume_m3: float, head_m: float) -> float:
    """Peak breach outflow (m^3/s) — Froehlich (1995) embankment-dam regression.

    ``Q_p = 0.607 * V^0.295 * H^1.24`` (SI units). Froehlich, D.C. (1995),
    "Peak outflow from breached embankment dam," *Journal of Water Resources
    Planning and Management*, 121(1), 90-97.
    """
    if volume_m3 <= 0 or head_m <= 0:
        raise ValueError("volume_m3 and head_m must both be > 0")
    return float(0.607 * float(volume_m3) ** 0.295 * float(head_m) ** 1.24)


def ritter_depth_m(x_m: float, t_s: float, head_m: float) -> float:
    """Water depth (m) at downstream distance ``x`` at time ``t``.

    Ritter (1892) instantaneous dam-break on a dry frictionless bed:

    * ``x/t <= -c0``: undisturbed upstream water, depth = ``H``.
    * ``-c0 < x/t < 2*c0``: ``h = (1/9g) * (2*c0 - x/t)^2``.
    * ``x/t >= 2*c0``: dry bed ahead of the front, depth = 0.

    Requires ``t > 0`` (the solution is singular at ``t = 0``).
    """
    if t_s <= 0:
        raise ValueError(f"t_s must be > 0, got {t_s!r}")
    c0 = ritter_celerity_ms(head_m)
    s = float(x_m) / float(t_s)
    if s <= -c0:
        return float(head_m)
    if s >= 2.0 * c0:
        return 0.0
    return (1.0 / (9.0 * GRAVITY)) * (2.0 * c0 - s) ** 2


def ritter_velocity_ms(x_m: float, t_s: float, head_m: float) -> float:
    """Flow velocity (m/s) in the Ritter dam-break wave.

    ``u = (2/3)*(c0 + x/t)`` inside the wave region; zero upstream and ahead.
    """
    if t_s <= 0:
        raise ValueError(f"t_s must be > 0, got {t_s!r}")
    c0 = ritter_celerity_ms(head_m)
    s = float(x_m) / float(t_s)
    if -c0 <= s <= 2.0 * c0:
        return (2.0 / 3.0) * (c0 + s)
    return 0.0


def flood_arrival_time_s(distance_m: float, head_m: float) -> float:
    """Time (s) for the flood front to reach a downstream distance (Ritter)."""
    return float(distance_m) / ritter_front_speed_ms(head_m)


def peak_depth_at_distance_m(distance_m: float, head_m: float) -> float:
    """Asymptotic peak inundation depth (m) at a downstream distance.

    The frictionless Ritter solution relaxes monotonically toward ``4H/9`` at
    any fixed distance, so the peak depth equals the dam-site plateau depth
    ``4H/9`` (documented simplification; friction and valley geometry would
    lower it).
    """
    _ = float(distance_m)
    return RITTER_DEPTH_COEFFICIENT * float(head_m)


def flood_depths_at_distance(
    distance_m: float,
    head_m: float,
    times_s: tuple[float, ...],
) -> tuple[tuple[float, float], ...]:
    """(time_s, depth_m) pairs at a downstream distance for the given times."""
    return tuple((t, ritter_depth_m(distance_m, t, head_m)) for t in times_s)


def severity_ratio(depth_m: float, facility_elevation_m: float) -> float:
    """Inundation severity: ``depth / facility_elevation`` (0 = dry)."""
    if depth_m < 0:
        raise ValueError(f"depth_m must be >= 0, got {depth_m!r}")
    if facility_elevation_m <= 0:
        raise ValueError(f"facility_elevation_m must be > 0, got {facility_elevation_m!r}")
    return float(depth_m) / float(facility_elevation_m)


def flood_risk_rating(depth_m: float, facility_elevation_m: float) -> str:
    """Qualitative flood-risk rating from the severity ratio.

    Tiers: low (<=0.05), moderate (<=0.2), high (<=0.5), extreme (>0.5).
    """
    ratio = severity_ratio(depth_m, facility_elevation_m)
    if ratio <= 0.05:
        return "low"
    if ratio <= 0.2:
        return "moderate"
    if ratio <= 0.5:
        return "high"
    return "extreme"
