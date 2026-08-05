"""Tests for the regional power-network resilience model (goldeneye.grid_resilience)."""

from __future__ import annotations

import pytest

from goldeneye.emp_model import EmpWeapon
from goldeneye.grid_resilience import (
    GridLine,
    GridNode,
    PowerGrid,
    certainly_failed_nodes,
    edge_disjoint_path_count,
    line_between,
    line_field_vm,
    line_survival_probability,
    lines_between,
    most_reliable_path,
    node_survival_probability,
    path_reliability,
    resilience_report,
)

WEAPON = EmpWeapon(yield_kt=2000.0, burst_altitude_km=300.0)


def _military(name: str, x: float, y: float, *, critical: bool = False, load: float = 0.0) -> GridNode:
    return GridNode(name, x, y, load, critical, "military")


class TestPowerGridValidation:
    def test_duplicate_node_names(self) -> None:
        nodes = (GridNode("a", 0.0, 0.0, 0.0, False, "military"), GridNode("a", 1.0, 1.0, 0.0, False, "military"))
        lines: tuple[GridLine, ...] = ()
        with pytest.raises(ValueError, match="duplicate"):
            PowerGrid(nodes, lines, source="a")

    def test_self_loop_line(self) -> None:
        with pytest.raises(ValueError, match="two distinct"):
            GridLine("l", "a", "a", "military")

    def test_unknown_source(self) -> None:
        nodes = (GridNode("a", 0.0, 0.0, 0.0, False, "military"),)
        lines: tuple[GridLine, ...] = ()
        with pytest.raises(ValueError, match="source"):
            PowerGrid(nodes, lines, source="zzz")

    def test_line_unknown_node(self) -> None:
        nodes = (GridNode("a", 0.0, 0.0, 0.0, False, "military"),)
        lines = (GridLine("l", "a", "b", "military"),)
        with pytest.raises(ValueError, match="unknown node"):
            PowerGrid(nodes, lines, source="a")

    def test_unknown_class_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            GridNode("a", 0.0, 0.0, 0.0, False, "nope")

    def test_negative_load_raises(self) -> None:
        with pytest.raises(ValueError):
            GridNode("a", 0.0, 0.0, -1.0, False, "military")


class TestSurvival:
    def _pair(self) -> PowerGrid:
        return PowerGrid(
            (
                _military("src", 0.0, 850.0),
                _military("load", 100.0, 850.0, critical=True, load=10.0),
            ),
            (GridLine("sl", "src", "load", "military"),),
            source="src",
        )

    def test_node_survival_high_for_military_off_nadir(self) -> None:
        grid = self._pair()
        assert 0.9 < node_survival_probability(grid, WEAPON, "src") < 1.0

    def test_node_survival_low_at_nadir_unprotected(self) -> None:
        grid = PowerGrid(
            (GridNode("src", 0.0, 0.0, 0.0, False, "unprotected"),),
            (),
            source="src",
        )
        assert node_survival_probability(grid, WEAPON, "src") < 1e-3

    def test_line_survival_at_midpoint(self) -> None:
        grid = self._pair()
        assert 0.0 < line_survival_probability(grid, WEAPON, "sl") <= 1.0

    def test_path_reliability_is_product(self) -> None:
        grid = self._pair()
        prod = (
            node_survival_probability(grid, WEAPON, "src")
            * line_survival_probability(grid, WEAPON, "sl")
            * node_survival_probability(grid, WEAPON, "load")
        )
        assert path_reliability(grid, WEAPON, ("src", "load")) == pytest.approx(prod)

    def test_unknown_node_raises(self) -> None:
        grid = self._pair()
        with pytest.raises(KeyError):
            node_survival_probability(grid, WEAPON, "zzz")
        with pytest.raises(KeyError):
            line_survival_probability(grid, WEAPON, "nope")

    def test_certainly_failed(self) -> None:
        grid = PowerGrid(
            (
                GridNode("up", 0.0, 850.0, 0.0, False, "military"),
                GridNode("dead", 0.0, 700.0, 0.0, False, "unprotected"),
            ),
            (),
            source="up",
        )
        failed = certainly_failed_nodes(grid, WEAPON)
        assert failed == ("dead",)


class TestPaths:
    def _diamond(self) -> PowerGrid:
        return PowerGrid(
            (
                _military("A", 0.0, 850.0),
                _military("B", 100.0, 850.0, critical=True, load=10.0),
                _military("C", 50.0, 820.0),
                _military("D", 50.0, 880.0),
            ),
            (
                GridLine("AC", "A", "C", "military"),
                GridLine("CB", "C", "B", "military"),
                GridLine("AD", "A", "D", "military"),
                GridLine("DB", "D", "B", "military"),
            ),
            source="A",
        )

    def test_edge_disjoint_count_diamond(self) -> None:
        assert edge_disjoint_path_count(self._diamond(), "A", "B") == 2

    def test_edge_disjoint_single_path(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (GridLine("AB", "A", "B", "military"),),
            source="A",
        )
        assert edge_disjoint_path_count(grid, "A", "B") == 1

    def test_edge_disjoint_disconnected(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (),
            source="A",
        )
        assert edge_disjoint_path_count(grid, "A", "B") == 0

    def test_edge_disjoint_same_node(self) -> None:
        assert edge_disjoint_path_count(self._diamond(), "A", "A") == 0

    def test_most_reliable_path_prefers_shortcut(self) -> None:
        # Two routes: a direct hardened link vs a long unprotected detour.
        grid = PowerGrid(
            (
                GridNode("src", 0.0, 850.0, 0.0, False, "military"),
                GridNode("load", 100.0, 850.0, 10.0, True, "military"),
                GridNode("detour", 50.0, 800.0, 0.0, False, "unprotected"),
            ),
            (
                GridLine("direct", "src", "load", "military"),
                GridLine("leg1", "src", "detour", "unprotected"),
                GridLine("leg2", "detour", "load", "unprotected"),
            ),
            source="src",
        )
        path, rel = most_reliable_path(grid, WEAPON, "src", "load")
        assert path == ("src", "load")
        assert rel > 0.5

    def test_most_reliable_path_reliability_matches(self) -> None:
        grid = self._diamond()
        path, rel = most_reliable_path(grid, WEAPON, "A", "B")
        assert path_reliability(grid, WEAPON, path) == pytest.approx(rel)

    def test_unreachable_returns_empty(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (),
            source="A",
        )
        path, rel = most_reliable_path(grid, WEAPON, "A", "B")
        assert path == ()
        assert rel == 0.0


class TestParallelCircuits:
    """Parallel circuits between one node pair are ordinary transmission
    redundancy; each must count as its own edge-disjoint route."""

    def _parallel(self, second_class: str = "military") -> PowerGrid:
        return PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0, critical=True, load=10.0)),
            (
                GridLine("AB_1", "A", "B", "military"),
                GridLine("AB_2", "A", "B", second_class),
            ),
            source="A",
        )

    def test_two_parallel_circuits_count_as_two_routes(self) -> None:
        # Regression: capacities were overwritten, collapsing both circuits to one.
        assert edge_disjoint_path_count(self._parallel(), "A", "B") == 2

    def test_three_parallel_circuits_count_as_three(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            tuple(GridLine(f"AB_{i}", "A", "B", "military") for i in range(3)),
            source="A",
        )
        assert edge_disjoint_path_count(grid, "A", "B") == 3

    def test_lines_between_returns_every_circuit(self) -> None:
        grid = self._parallel()
        names = [line.name for line in lines_between(grid, "A", "B")]
        assert names == ["AB_1", "AB_2"]
        # line_between keeps its documented first-match behaviour.
        assert line_between(grid, "A", "B").name == "AB_1"

    def test_lines_between_unknown_pair_raises(self) -> None:
        grid = self._parallel()
        with pytest.raises(KeyError):
            lines_between(grid, "A", "Z")

    def test_path_reliability_uses_most_survivable_circuit(self) -> None:
        # A hardened circuit in parallel with a fragile one must not be dragged
        # down by the fragile one: Dijkstra relaxes on the best edge, so
        # path_reliability must agree with it.
        grid = self._parallel(second_class="unprotected")
        hardened = line_survival_probability(grid, WEAPON, "AB_1")
        fragile = line_survival_probability(grid, WEAPON, "AB_2")
        assert hardened > fragile  # the test is only meaningful if they differ
        path, rel = most_reliable_path(grid, WEAPON, "A", "B")
        assert path == ("A", "B")
        assert path_reliability(grid, WEAPON, path) == pytest.approx(rel)
        expected = (
            node_survival_probability(grid, WEAPON, "A") * node_survival_probability(grid, WEAPON, "B") * hardened
        )
        assert path_reliability(grid, WEAPON, path) == pytest.approx(expected)


class TestResilienceReport:
    def test_source_node_that_is_itself_critical(self) -> None:
        # The canonical grid's source is not a critical load, so this branch is
        # otherwise unexercised: a critical source is served with certainty and
        # needs no route to itself.
        grid = PowerGrid(
            (
                _military("A", 0.0, 850.0, critical=True, load=25.0),
                _military("B", 100.0, 850.0, critical=True, load=5.0),
            ),
            (GridLine("AB", "A", "B", "military"),),
            source="A",
        )
        report = resilience_report(grid, WEAPON)
        source_row = next(row for row in report["per_load"] if row["load"] == "A")
        assert source_row["reliability"] == 1.0
        assert source_row["disjoint_paths"] == 0
        assert source_row["path"] == ("A",)
        assert report["total_critical_mw"] == pytest.approx(30.0)

    def test_report_with_no_critical_loads_is_zeroed_not_undefined(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (GridLine("AB", "A", "B", "military"),),
            source="A",
        )
        report = resilience_report(grid, WEAPON)
        assert report["per_load"] == ()
        assert report["total_critical_mw"] == 0.0
        assert report["served_fraction"] == 0.0
        assert report["min_reliability"] == 0.0
        assert report["min_disjoint_paths"] == 0

    def test_deterministic(self) -> None:
        grid = _canonical()
        assert resilience_report(grid, WEAPON) == resilience_report(grid, WEAPON)

    def test_report_bounds(self) -> None:
        report = resilience_report(_canonical(), WEAPON)
        assert 0.0 <= report["served_fraction"] <= 1.0
        assert report["expected_served_mw"] <= report["total_critical_mw"]
        assert report["min_reliability"] >= 0.0
        assert report["min_disjoint_paths"] >= 0

    def test_report_has_all_critical_loads(self) -> None:
        report = resilience_report(_canonical(), WEAPON)
        loads = [row["load"] for row in report["per_load"]]
        assert set(loads) == {"facility_sub", "town_a"}

    def test_report_json_serializable(self) -> None:
        import json

        json.dumps(resilience_report(_canonical(), WEAPON))


def _canonical():
    from goldeneye.scenario import ARKANGEL

    return ARKANGEL.grid


class TestValidationGuards:
    """Each constructor guard must be provably reachable."""

    def test_node_name_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError, match="GridNode.name must be non-empty"):
            GridNode("   ", 0.0, 0.0, 0.0, False, "military")

    def test_line_name_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError, match="GridLine.name must be non-empty"):
            GridLine(" ", "A", "B", "military")

    def test_duplicate_line_names_rejected(self) -> None:
        with pytest.raises(ValueError, match="duplicate grid line names"):
            PowerGrid(
                (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0), _military("C", 50.0, 850.0)),
                (GridLine("dup", "A", "B", "military"), GridLine("dup", "B", "C", "military")),
                source="A",
            )

    def test_line_survival_unknown_line_raises(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (GridLine("AB", "A", "B", "military"),),
            source="A",
        )
        with pytest.raises(KeyError, match="unknown grid line"):
            line_survival_probability(grid, WEAPON, "ghost")

    def test_path_reliability_rejects_empty_path(self) -> None:
        with pytest.raises(ValueError, match="at least one node"):
            path_reliability(_canonical(), WEAPON, ())

    def test_line_field_unknown_line_raises(self) -> None:
        grid = PowerGrid(
            (_military("A", 0.0, 850.0), _military("B", 100.0, 850.0)),
            (GridLine("AB", "A", "B", "military"),),
            source="A",
        )
        with pytest.raises(KeyError, match="unknown grid line"):
            line_field_vm(grid, WEAPON, "ghost")
