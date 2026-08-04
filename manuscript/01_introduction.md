# Introduction

**{{GE_TITLE}}** (**{{GE_SUBTITLE}}**) is a BOND-suite film package for *GoldenEye*
(1995), the film in which a captured space-based weapon — a two-kiloton-class
nuclear device detonated at altitude — demonstrates the catastrophic coupling
between an electromagnetic pulse and the electronics of an entire region. The
package re-casts that event as a rigorous, deterministic engineering analysis,
and extends it with a second mission-critical system from the same film: the
Arkangel dam facility, whose defensive layers and catastrophic-failure flood
risk are modelled explicitly.

## Reader's guide

The package is organised around a clean separation of concerns:

- **Pure domain core** — `src/goldeneye/emp_model.py`, `kill_radius.py`, and
  `dam_security.py` implement the three concept models as infrastructure-free,
  closed-form mathematics. They can be imported in any Python environment with
  no BOND layer present.
- **Scenario composition** — `src/goldeneye/scenario.py` binds the three models
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
