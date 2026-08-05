"""Tests for the ARKANGEL MissionProvider (goldeneye.mission + bond_api adapter).

Zero-mock: exercises the real provider against the frozen bond-api protocol —
protocol conformance, gadget registration, serialization round-trips, and
bond-api discovery. Also proves the pure domain core imports without bond-api.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from bond_api.protocol import (
    Debrief,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    MissionProvider as MissionProviderProtocol,
    Provenance,
    ReconReport,
    ReconRequest,
    run_mission,
)
from bond_api.registry import GadgetRegistry
from bond_api.serialization import from_json, to_json
from goldeneye.mission import GADGETS, MissionProvider, _facility_reliability

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestProtocolConformance:
    def test_is_runtime_checkable_provider(self) -> None:
        assert isinstance(MissionProvider(), MissionProviderProtocol)

    def test_film_slug(self) -> None:
        assert MissionProvider().film == "goldeneye"

    def test_brief_shape(self) -> None:
        brief = MissionProvider().brief()
        assert isinstance(brief, MissionBrief)
        assert brief.film == "goldeneye"
        assert brief.codename == "ARKANGEL"
        assert len(brief.objectives) == 5
        assert len(brief.assets) == 2
        assert len(brief.constraints) == 3

    def test_recon_shape(self) -> None:
        report = MissionProvider().recon(ReconRequest(goal="test goal"))
        assert isinstance(report, ReconReport)
        assert any(f.label == "goal" and f.detail == "test goal" for f in report.findings)

    def test_plan_shape(self) -> None:
        provider = MissionProvider()
        plan = provider.plan(provider.brief())
        assert isinstance(plan, MissionPlan)
        assert len(plan.steps) == 9
        names = [s.name for s in plan.steps]
        assert names == [
            "emp",
            "kill_radius",
            "orbit",
            "coupling",
            "grid",
            "dam_security",
            "flood_risk",
            "hydrograph",
            "synthesize",
        ]

    def test_execute_outcome(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        assert isinstance(outcome, MissionOutcome)
        assert outcome.success is True
        assert isinstance(outcome.results, dict)
        assert isinstance(outcome.provenance, Provenance)
        assert outcome.provenance.seed == 0

    def test_debrief_shape(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        debrief = provider.debrief(outcome)
        assert isinstance(debrief, Debrief)
        assert len(debrief.lessons) == 6

    def test_run_mission_full_flow_order(self) -> None:
        debrief = run_mission(MissionProvider(), ReconRequest(goal="assess"))
        assert isinstance(debrief, Debrief)
        assert debrief.outcome.success is True

    def test_execute_deterministic(self) -> None:
        provider = MissionProvider()
        plan = provider.plan(provider.brief())
        first = provider.execute(plan).results
        second = provider.execute(plan).results
        assert first == second


class TestGadgets:
    def test_registry_has_goldeneye(self) -> None:
        assert GADGETS.films() == ("goldeneye",)

    def test_registered_gadgets(self) -> None:
        registered = set(GADGETS.gadgets_for("goldeneye"))
        expected = {
            "emp_envelope_field",
            "hemp_waveform",
            "vulnerability_classes",
            "kill_radius_km",
            "damage_probability",
            "circular_orbit_period_s",
            "elevation_angle_deg",
            "overhead_pass_duration_s",
            "skin_depth_m",
            "schelkunoff_se_db",
            "induced_voltage_v",
            "protection_margin_db",
            "node_survival_probability",
            "most_reliable_path",
            "edge_disjoint_path_count",
            "breach_peak_discharge",
            "ritter_depth",
            "cumulative_detection",
            "breach_average_width_m",
            "triangular_hydrograph",
        }
        assert len(registered) == 20
        assert expected <= registered

    def test_gadget_callables_work(self) -> None:
        from goldeneye.emp_model import EmpWeapon

        kill = GADGETS.lookup("goldeneye", "kill_radius_km")
        assert kill(EmpWeapon(2000.0, 300.0), "commercial") > 0

        field = GADGETS.lookup("goldeneye", "emp_envelope_field")
        assert field(0.0, 300.0, 2000.0) > 0

    def test_registry_is_gadget_registry_type(self) -> None:
        assert isinstance(GADGETS, GadgetRegistry)

    def test_unknown_gadget_raises(self) -> None:
        with pytest.raises(KeyError):
            GADGETS.lookup("goldeneye", "nope")


class TestSerialization:
    def test_outcome_round_trip(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        text = to_json(outcome)
        restored = from_json(text)
        assert isinstance(restored, MissionOutcome)
        assert restored.results == outcome.results
        assert restored.provenance == outcome.provenance

    def test_serialization_has_bond_type_tag(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        assert '"__bond_type__": "MissionOutcome"' in to_json(outcome)


class TestDiscovery:
    def test_bond_api_discovery_finds_goldeneye(self) -> None:
        from bond_api.discovery import load_provider

        provider = load_provider("goldeneye")
        assert provider.film == "goldeneye"
        assert isinstance(provider, MissionProviderProtocol)


class TestPureCoreWithoutBondApi:
    #: Installed into ``sys.meta_path`` in the child interpreter so that *any*
    #: attempt to import a BOND layer raises, rather than merely being absent
    #: from ``sys.modules`` afterwards. Without this the check was passive: a
    #: lazily-imported ``bond_api`` inside a core function would have gone
    #: unnoticed, and both packages remained fully importable.
    _BLOCKER = (
        "import sys\n"
        "class _BondLayerBlocker:\n"
        "    BLOCKED = ('bond_api', 'bond_utilities')\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in self.BLOCKED:\n"
        "            raise ImportError('layer-contract test blocked import of ' + name)\n"
        "        return None\n"
        "sys.meta_path.insert(0, _BondLayerBlocker())\n"
        "for _blocked in ('bond_api', 'bond_utilities'):\n"
        "    try:\n"
        "        __import__(_blocked)\n"
        "    except ImportError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('blocker inert for ' + _blocked + ' — gate would be vacuous')\n"
    )

    def test_pure_core_imports_without_bond_api(self) -> None:
        """The domain core must not pull bond_api, even lazily.

        The child interpreter installs a meta-path finder that raises on any
        ``bond_api``/``bond_utilities`` import (self-verified by a positive
        control), then exercises the core. Any BOND-layer import anywhere in
        the core — at module scope or inside a called function — fails the run.
        """
        code = (
            self._BLOCKER + "from goldeneye.emp_model import EmpWeapon\n"
            "from goldeneye.kill_radius import kill_radius_km, VULNERABILITY_CLASSES\n"
            "from goldeneye.dam_security import Reservoir, ritter_depth_m\n"
            "from goldeneye.scenario import ARKANGEL, analyze_arkangel\n"
            "assert 'bond_api' not in sys.modules\n"
            "assert 'bond_utilities' not in sys.modules\n"
            "assert len(VULNERABILITY_CLASSES) == 4\n"
            "assert kill_radius_km(EmpWeapon(2000.0, 300.0), 'military') > 0\n"
            "assert ritter_depth_m(0.0, 100.0, 75.0) > 0\n"
            "assert analyze_arkangel(ARKANGEL)['codename'] == 'ARKANGEL'\n"
            "print('pure-core-ok')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "pure-core-ok" in proc.stdout

    def test_blocker_actually_blocks_the_adapter(self) -> None:
        """Negative control: mission.py DOES need bond_api, so it must fail.

        This proves the blocker has teeth. If it were inert, this subprocess
        would exit 0 and the isolation test above would prove nothing.
        """
        proc = subprocess.run(
            [sys.executable, "-c", self._BLOCKER + "import goldeneye.mission\n"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0
        assert "layer-contract test blocked import of bond_api" in proc.stderr

    def test_mission_import_requires_bond_api_surface(self) -> None:
        # mission.py is the bond_api adapter; importing it pulls the protocol.
        import importlib

        mission = importlib.import_module("goldeneye.mission")
        assert hasattr(mission, "MissionProvider")


class TestDeepenedResults:
    def test_results_include_new_sections(self) -> None:
        provider = MissionProvider()
        results = provider.execute(provider.plan(provider.brief())).results
        assert set(results) >= {"orbit", "coupling", "grid", "hydrograph"}
        assert results["steps_completed"] == 9

    def test_grid_results_present(self) -> None:
        results = MissionProvider().execute(MissionProvider().plan(MissionProvider().brief())).results
        assert results["grid"]["down_nodes"] == ("town_a", "relay")
        assert results["grid"]["min_disjoint_paths"] >= 2

    def test_debrief_mentions_grid(self) -> None:
        provider = MissionProvider()
        debrief = provider.debrief(provider.execute(provider.plan(provider.brief())))
        assert any("grid" in lesson for lesson in debrief.lessons)

    def test_execute_deterministic_still(self) -> None:
        provider = MissionProvider()
        plan = provider.plan(provider.brief())
        assert provider.execute(plan).results == provider.execute(plan).results


class TestPureCoreDeepened:
    def test_all_new_modules_import_without_bond_api(self) -> None:
        code = (
            "import sys\n"
            "from goldeneye.orbital_mechanics import circular_orbit_period_s, orbital_radius_m\n"
            "from goldeneye.coupling import skin_depth_m, schelkunoff_se_db\n"
            "from goldeneye.grid_resilience import GridNode, GridLine, PowerGrid\n"
            "from goldeneye.breach_hydrograph import Station, breach_hydrograph_report\n"
            "from goldeneye.scenario import analyze_arkangel, ARKANGEL\n"
            "assert 'bond_api' not in sys.modules\n"
            "assert 'bond_utilities' not in sys.modules\n"
            "assert circular_orbit_period_s(orbital_radius_m(300000.0)) > 4000\n"
            "assert skin_depth_m(1e6, 1.68e-8) > 0\n"
            "assert analyze_arkangel(ARKANGEL)['grid']['min_disjoint_paths'] >= 1\n"
            "print('deep-core-ok')\n"
        )
        import subprocess

        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "deep-core-ok" in proc.stdout


class TestFacilityReliabilityFallback:
    """The debrief's facility-reliability lookup must degrade honestly."""

    def test_returns_facility_row_reliability(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        expected = next(
            row["reliability"] for row in outcome.results["grid"]["per_load"] if row["load"] == "facility_sub"
        )
        assert _facility_reliability(outcome) == pytest.approx(expected)

    def test_returns_zero_when_no_facility_load_is_present(self) -> None:
        # A grid report with critical loads but no facility_sub row: the lookup
        # falls through rather than raising, so the debrief still renders.
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        stripped = dict(outcome.results)
        stripped["grid"] = {"per_load": ({"load": "town_a", "reliability": 0.5},)}
        assert _facility_reliability(replace(outcome, results=stripped)) == 0.0

    def test_returns_zero_when_grid_section_is_absent(self) -> None:
        provider = MissionProvider()
        outcome = provider.execute(provider.plan(provider.brief()))
        stripped = {k: v for k, v in outcome.results.items() if k != "grid"}
        assert _facility_reliability(replace(outcome, results=stripped)) == 0.0
