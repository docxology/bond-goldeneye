"""Figure generation for the GoldenEye: ARKANGEL mission.

Three concept figures are produced, all deterministic (headless Agg backend,
fixed input grids, no RNG):

* ``emp_footprint`` — the EMP threat envelope and kill-radius analysis:
  radial field profiles, kill radius vs burst altitude per vulnerability
  class, the damage-probability transition, and the kill-area fraction vs
  weapon yield.
* ``flood_wave`` — the Ritter dam-break flood: downstream depth profiles at
  several times and the inundation depth / arrival time at the facility.
* ``grid_resilience`` — the regional power network's resilience: node survival
  probabilities on a map and per-critical-load reliability / redundancy.

Artifacts are regenerable and gitignored under ``output/figures/``.
"""

from __future__ import annotations

__all__ = ["emp_footprint", "flood_wave", "grid_resilience"]
