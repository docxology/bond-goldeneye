"""ARKANGEL — GoldenEye mission provider (thin ``bond_api`` adapter).

This is the only module in :mod:`goldeneye` that imports the BOND protocol
layer. It implements the frozen :class:`~bond_api.protocol.MissionProvider`
contract (``brief``, ``recon``, ``plan``, ``execute``, ``debrief``) over the
pure, infrastructure-free domain core (:mod:`goldeneye.scenario`), and
registers the mission's analytical gadgets with
:class:`~bond_api.registry.GadgetRegistry` under the ``goldeneye`` slug.

Discovery contract: a film package is a top-level module named by its slug
exposing ``mission.MissionProvider`` at module level. bond-api's
:func:`~bond_api.discovery.load_provider` imports ``goldeneye.mission`` and
instantiates this class. The public shape (class name, the five methods, the
module-level ``GADGETS`` registry) is stable across package versions so the
suite's orchestrator and coordinator can rely on it.
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
from goldeneye import (
    breach_hydrograph,
    coupling,
    dam_security,
    emp_model,
    grid_resilience,
    kill_radius,
    orbital_mechanics,
)
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
        "circular_orbit_period_s": orbital_mechanics.circular_orbit_period_s,
        "elevation_angle_deg": orbital_mechanics.elevation_angle_deg,
        "overhead_pass_duration_s": orbital_mechanics.overhead_pass_duration_s,
        "skin_depth_m": coupling.skin_depth_m,
        "schelkunoff_se_db": coupling.schelkunoff_se_db,
        "induced_voltage_v": coupling.induced_voltage_v,
        "protection_margin_db": coupling.protection_margin_db,
        "node_survival_probability": grid_resilience.node_survival_probability,
        "most_reliable_path": grid_resilience.most_reliable_path,
        "edge_disjoint_path_count": grid_resilience.edge_disjoint_path_count,
        "breach_peak_discharge": dam_security.breach_peak_discharge_cms,
        "ritter_depth": dam_security.ritter_depth_m,
        "cumulative_detection": dam_security.cumulative_detection_probability,
        "breach_average_width_m": breach_hydrograph.breach_average_width_m,
        "triangular_hydrograph": breach_hydrograph.triangular_hydrograph,
    },
)


class MissionProvider:
    """Deterministic GoldenEye (ARKANGEL) mission implementation.

    The class name is fixed by the discovery contract.
    """

    film = "goldeneye"

    def brief(self) -> MissionBrief:
        """Declare the ARKANGEL mission: five objectives over the deep core."""
        return MissionBrief(
            film=self.film,
            codename="ARKANGEL",
            objectives=(
                "model the orbital EMP threat envelope and the orbital platform geometry",
                "assess electronics kill radii by vulnerability class",
                "assess EM coupling and shielding on sensitive infrastructure",
                "assess regional power-network resilience to the strike",
                "evaluate Arkangel dam-facility security and breach-flood hydrograph",
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
                Constraint(kind="protocol", detail="frozen bond_api MissionProvider surface"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the threat, the platform, and the infrastructure."""
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
                    label="platform",
                    detail=(
                        f"orbital platform at {ARKANGEL.orbit.altitude_km:g} km; "
                        f"target elevation {ARKANGEL.orbit.min_elevation_deg:g} deg minimum"
                    ),
                ),
                Finding(
                    label="infrastructure",
                    detail=(
                        f"regional grid with {len(ARKANGEL.grid.nodes)} nodes and "
                        f"{len(ARKANGEL.grid.lines)} lines; facility "
                        f"{ARKANGEL.facility_distance_km:g} km downstream of the dam"
                    ),
                ),
                Finding(label="method", detail="closed-form physics; deterministic analysis"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the nine deterministic stages of the analysis."""
        _ = brief
        return MissionPlan(
            steps=(
                Step(name="emp", action="model_threat_envelope", params={"yield_kt": ARKANGEL.weapon.yield_kt}),
                Step(name="kill_radius", action="assess_vulnerability_classes", params={"count": 4}),
                Step(
                    name="orbit", action="assess_platform_geometry", params={"altitude_km": ARKANGEL.orbit.altitude_km}
                ),
                Step(
                    name="coupling",
                    action="assess_coupling_shielding",
                    params={"material": ARKANGEL.coupling.shield_material},
                ),
                Step(name="grid", action="assess_grid_resilience", params={"nodes": len(ARKANGEL.grid.nodes)}),
                Step(name="dam_security", action="evaluate_access_control", params={"layers": 4}),
                Step(name="flood_risk", action="assess_breach_flood", params={"head_m": ARKANGEL.reservoir.head_m}),
                Step(name="hydrograph", action="assess_breach_hydrograph", params={"stations": len(ARKANGEL.stations)}),
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
        access = outcome.results.get("access", {})
        grid = outcome.results.get("grid", {})
        coupling_r = outcome.results.get("coupling", {})
        hydro = outcome.results.get("hydrograph", {})
        reservoir = outcome.results.get("dam", {})
        return Debrief(
            outcome=outcome,
            lessons=(
                "unprotected microelectronics die over the whole visible footprint; "
                "hardened (MIL-STD-188-125) and legacy-tube electronics largely survive",
                f"the over-the-nadir field couples ~{coupling_r.get('induced_voltage_v', 0) / 1000:.0f} kV "
                f"onto a {coupling_r.get('effective_height_m', 0):.1f} m effective antenna, but "
                f"{coupling_r.get('se_db', 0):.0f} dB of shielding reduces the penetrated field to ~0",
                f"the regional grid serves ~{grid.get('served_fraction', 0) * 100:.0f}% of critical load; "
                f"the mission-critical facility survives with P={_facility_reliability(outcome):.2f}",
                f"the breach hydrograph releases the {reservoir.get('volume_m3', 0) / 1e6:.0f} Mm^3 reservoir "
                f"over ~{hydro.get('duration_min', 0):.0f} min at a mean of ~{hydro.get('mean_outflow_cms', 0):.0f} m^3/s",
                f"defense-in-depth detection is P={access.get('detection_probability', 0):.3f} "
                f"with a security score of {access.get('security_score', 0):.1f}",
                "deterministic closed-form models keep the analysis reproducible",
            ),
        )


def _facility_reliability(outcome: MissionOutcome) -> float:
    """Survival probability of the mission-critical facility load (grid report)."""
    for row in outcome.results.get("grid", {}).get("per_load", ()):
        if row["load"] == "facility_sub":
            return float(row["reliability"])
    return 0.0
