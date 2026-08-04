"""ARKANGEL — GoldenEye mission provider (thin ``bond_api`` adapter).

This is the only module in :mod:`goldeneye` that imports the BOND protocol
layer. It implements the frozen :class:`~bond_api.protocol.MissionProvider`
contract (``brief``, ``recon``, ``plan``, ``execute``, ``debrief``) over the
pure, infrastructure-free domain core (:mod:`goldeneye.scenario` and the three
concept modules), and registers the mission's analytical gadgets with
:class:`~bond_api.registry.GadgetRegistry` under the ``goldeneye`` slug.

Discovery contract: a film package is a top-level module named by its slug
exposing ``mission.MissionProvider`` at module level. bond-api's
:func:`~bond_api.discovery.load_provider`` imports ``goldeneye.mission`` and
instantiates this class.
"""

from __future__ import annotations

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry
from goldeneye import dam_security, emp_model, kill_radius
from goldeneye.scenario import ARKANGEL, analyze_arkangel, input_hash

__all__ = ["GADGETS", "MissionProvider", "PACKAGE_VERSION", "SEED"]

PACKAGE_VERSION = "0.1.0"
SEED = 0  # fully deterministic — no random draws anywhere in the analysis


GADGETS = GadgetRegistry()
GADGETS.register(
    "goldeneye",
    {
        "emp_envelope_field": emp_model.peak_e_field_vm,
        "hemp_waveform": emp_model.hemp_waveform,
        "vulnerability_classes": kill_radius.VULNERABILITY_CLASSES,
        "kill_radius_km": kill_radius.kill_radius_km,
        "damage_probability": kill_radius.damage_probability_vs_field,
        "breach_peak_discharge": dam_security.breach_peak_discharge_cms,
        "ritter_depth": dam_security.ritter_depth_m,
        "cumulative_detection": dam_security.cumulative_detection_probability,
    },
)


class MissionProvider:  # noqa: N801 - class name is fixed by the discovery contract
    """Deterministic GoldenEye (ARKANGEL) mission implementation."""

    film = "goldeneye"

    def brief(self) -> MissionBrief:
        """Declare the ARKANGEL mission: three objectives over the deep core."""
        return MissionBrief(
            film=self.film,
            codename="ARKANGEL",
            objectives=(
                "model the orbital EMP threat envelope (detonation to ground effects)",
                "assess electronics kill radii by vulnerability class",
                "evaluate Arkangel dam-facility security and breach flood risk",
            ),
            assets=(
                Asset(kind="scenario", name="arkangel", payload=ARKANGEL.name),
                Asset(
                    kind="model",
                    name="emp_envelope",
                    payload={
                        "reference_vm": emp_model.E1_REFERENCE_VM,
                        "gamma_fraction": emp_model.GAMMA_YIELD_FRACTION,
                    },
                ),
            ),
            constraints=(
                Constraint(kind="determinism", detail="fixed seed, closed-form physics, no RNG"),
                Constraint(kind="protection", detail="conservative point-source EMP envelope"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the threat envelope, and the facility."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="weapon",
                    detail=(
                        f"yield {ARKANGEL.weapon.yield_kt:g} kt at "
                        f"{ARKANGEL.weapon.burst_altitude_km:g} km burst altitude"
                    ),
                ),
                Finding(
                    label="facility",
                    detail=(
                        f"Arkangel dam, H = {ARKANGEL.reservoir.head_m:g} m, "
                        f"facility {ARKANGEL.facility_distance_km:g} km downstream"
                    ),
                ),
                Finding(label="method", detail="closed-form physics; deterministic analysis"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the five deterministic stages of the analysis."""
        _ = brief
        return MissionPlan(
            steps=(
                Step(name="emp", action="model_threat_envelope", params={"yield_kt": ARKANGEL.weapon.yield_kt}),
                Step(name="kill_radius", action="assess_vulnerability_classes", params={"count": 4}),
                Step(name="dam_security", action="evaluate_access_control", params={"layers": 4}),
                Step(name="flood_risk", action="assess_breach_flood", params={"head_m": ARKANGEL.reservoir.head_m}),
                Step(name="synthesize", action="compile_report", params={"codename": "ARKANGEL"}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the full deterministic analysis and return a provenance-carrying outcome."""
        analysis = analyze_arkangel(ARKANGEL)
        results = dict(analysis)
        results["steps_completed"] = len(plan.steps)
        results["outputs"] = tuple(step.name for step in plan.steps)
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=PACKAGE_VERSION,
                seed=SEED,
                input_hash=input_hash(ARKANGEL),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the outcome and record the mission's standing lessons."""
        flood = outcome.results.get("flood", {})
        access = outcome.results.get("access", {})
        return Debrief(
            outcome=outcome,
            lessons=(
                "unprotected microelectronics die over the whole visible footprint; "
                "hardened (MIL-STD-188-125) and legacy-tube electronics largely survive",
                f"the Arkangel flood risk is {flood.get('risk_rating', 'n/a')} "
                f"(peak depth ~{flood.get('peak_depth_m', 0):g} m)",
                f"defense-in-depth detection is P={access.get('detection_probability', 0):.3f} "
                f"with a security score of {access.get('security_score', 0):.1f}",
                "deterministic closed-form models keep the analysis reproducible",
            ),
        )
