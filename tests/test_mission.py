"""Tests for the ARKANGEL MissionProvider (goldeneye.mission + bond_api adapter).

Zero-mock: exercises the real provider against the frozen bond-api protocol —
protocol conformance, gadget registration, serialization round-trips, and
bond-api discovery. Also proves the pure domain core imports without bond-api.
"""

from __future__ import annotations

import subprocess
import sys
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
from goldeneye.mission import GADGETS, MissionProvider

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
        assert len(brief.objectives) == 3
        assert len(brief.assets) == 2
        assert len(brief.constraints) >= 2

    def test_recon_shape(self) -> None:
        report = MissionProvider().recon(ReconRequest(goal="test goal"))
        assert isinstance(report, ReconReport)
        assert any(f.label == "goal" and f.detail == "test goal" for f in report.findings)

    def test_plan_shape(self) -> None:
        provider = MissionProvider()
        plan = provider.plan(provider.brief())
        assert isinstance(plan, MissionPlan)
        assert len(plan.steps) == 5
        names = [s.name for s in plan.steps]
        assert names == ["emp", "kill_radius", "dam_security", "flood_risk", "synthesize"]

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
        assert len(debrief.lessons) == 4

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
            "breach_peak_discharge",
            "ritter_depth",
            "cumulative_detection",
        }
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
    def test_pure_core_imports_without_bond_api(self) -> None:
        """The domain core must not pull bond_api transitively."""
        code = (
            "import sys\n"
            "from goldeneye.emp_model import EmpWeapon\n"
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

    def test_mission_import_requires_bond_api_surface(self) -> None:
        # mission.py is the bond_api adapter; importing it pulls the protocol.
        import importlib

        mission = importlib.import_module("goldeneye.mission")
        assert hasattr(mission, "MissionProvider")
