# Introduction

**{{GE_TITLE}}** (**{{GE_SUBTITLE}}**) is a BOND-suite film package for *GoldenEye*
(1995), the film in which a captured space-based weapon — a
**{{GE_YIELD_KT}}** kt nuclear device detonated at
**{{GE_BURST_ALTITUDE_KM}}** km altitude — demonstrates the catastrophic coupling
between an electromagnetic pulse and the electronics of an entire region. The
package re-casts that event as a rigorous, deterministic engineering analysis:
the orbital platform that carries the weapon, the field it lays down, how that
field couples into and past infrastructure shielding, and what the regional
power network retains afterwards. It then extends the analysis to the second
mission-critical system from the same film — the Arkangel dam facility, whose
defensive layers, catastrophic-failure flood risk, and downstream breach
hydrograph are modelled explicitly.

## Reader's guide

The package is organised around a clean separation of concerns:

- **Pure domain core** — seven infrastructure-free, closed-form modules:
  `emp_model.py` (the burst-to-ground E1 envelope and the E1/E2/E3 waveform),
  `orbital_mechanics.py` (the Keplerian delivery platform and its pass
  geometry), `kill_radius.py` (per-vulnerability-class kill radii),
  `coupling.py` (skin depth, Schelkunoff shielding, conductor coupling),
  `grid_resilience.py` (per-asset survival, most-reliable routing, edge-disjoint
  redundancy), `dam_security.py` (defense-in-depth access control and
  breach-flood risk), and `breach_hydrograph.py` (breach width, the
  volume-conserving outflow hydrograph, and the downstream station table).
  All seven can be imported in any Python environment with no BOND layer
  present.
- **Scenario composition** — `src/goldeneye/scenario.py` binds the seven models
  into the canonical ARKANGEL scenario and exposes the deterministic analysis
  dictionary and a canonical input hash.
- **Protocol adapter** — `src/goldeneye/mission.py` implements the frozen
  `bond_api.MissionProvider` contract (brief/recon/plan/execute/debrief) and
  registers the mission's analytical gadgets with the `bond_api.GadgetRegistry`.
- **Thin orchestrators** — `scripts/` expose the five mission phases plus a
  manuscript-variable hydrator. Business logic never lives in a script.

This design keeps the mathematical core testable in isolation (a per-module
suite with no mocks, ≥90% line-and-branch coverage) while leaving the BOND
protocol integration as a thin, inspectable adapter — the pattern used by every
film package in the suite.

## What this manuscript covers

`02_methodology.md` states the physics and the closed-form models.
`03_results.md` reports the ARKANGEL run. `04_conclusion.md` summarises the
deliverable. `05_experimental_setup.md` and `06_reproducibility.md` document
the scenario parameters, environment, and regeneration contract.
`07_scope_and_related_work.md` delimits the model's assumptions and situates it
in the HEMP-damage and dam-break literature.
