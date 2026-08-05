"""Regional power-network resilience to the EMP strike.

This module models the deterministic resilience of a regional power network
(the Severnaya-area grid serving the Arkangel facility) against the EMP
envelope from :mod:`goldeneye.emp_model`. It combines:

* **Per-asset survival** — every node (substation, plant) and line carries a
  vulnerability class; its survival probability is ``1 - P_damage(E)`` where
  ``E`` is the local envelope field at the asset's position (nadir at the
  origin of the coordinate grid) and ``P_damage`` is the damage-probability
  logistic from :mod:`goldeneye.kill_radius`.
* **Most-reliable path** — deterministic Dijkstra maximising the product of
  survival probabilities along a source-to-load route (equivalently minimising
  the sum of ``-log(survival)``), with insertion-order tie-breaking.
* **Path redundancy** — the number of edge-disjoint source-to-load routes via
  Edmonds-Karp max flow with unit edge capacities (deterministic BFS). Parallel
  circuits between one node pair each contribute their own unit of capacity, so
  they count as separate routes.
* **Resilience report** — per critical load: best-path reliability and
  disjoint-path count; network-level expected served load (the sum of
  ``load * P(best path survives)``, a documented approximation assuming
  independence) and the set of *certainly failed* nodes (damage probability
  >= 0.999).

All graph algorithms are deterministic (insertion-ordered traversal, strict
improvement), so the report is byte-identical run to run.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Any

from goldeneye.emp_model import EmpWeapon, peak_e_field_vm
from goldeneye.kill_radius import damage_probability_vs_field, lookup_class

__all__ = [
    "CERTAIN_FAILURE_PROBABILITY",
    "GridLine",
    "GridNode",
    "PowerGrid",
    "certainly_failed_nodes",
    "edge_disjoint_path_count",
    "line_between",
    "line_field_vm",
    "line_survival_probability",
    "lines_between",
    "most_reliable_path",
    "node_field_vm",
    "node_survival_probability",
    "path_reliability",
    "resilience_report",
]

#: Damage probability at which a node is treated as certainly failed.
CERTAIN_FAILURE_PROBABILITY = 0.999


@dataclass(frozen=True)
class GridNode:
    """A grid node: a plant, substation, or load point.

    Attributes:
        name: Unique node identifier.
        x_km / y_km: Position (km) on the local plane; the EMP burst nadir is
            the origin (0, 0).
        load_mw: Electrical load served at the node (MW, >= 0).
        critical: True when the node is a mission-critical load.
        vulnerability_class: Class slug from ``kill_radius.VULNERABILITY_CLASSES``.
    """

    name: str
    x_km: float
    y_km: float
    load_mw: float
    critical: bool
    vulnerability_class: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("GridNode.name must be non-empty")
        if self.load_mw < 0:
            raise ValueError(f"load_mw must be >= 0, got {self.load_mw!r}")
        lookup_class(self.vulnerability_class)  # raises KeyError for unknown classes


@dataclass(frozen=True)
class GridLine:
    """A transmission line between two nodes.

    Attributes:
        name: Unique line identifier.
        node_a / node_b: Endpoint node names (must differ).
        vulnerability_class: Class slug of the line's protection level.
    """

    name: str
    node_a: str
    node_b: str
    vulnerability_class: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("GridLine.name must be non-empty")
        if self.node_a == self.node_b:
            raise ValueError(f"GridLine {self.name!r} must connect two distinct nodes")
        lookup_class(self.vulnerability_class)


@dataclass(frozen=True)
class PowerGrid:
    """A power network: nodes, lines, and a designated source node."""

    nodes: tuple[GridNode, ...]
    lines: tuple[GridLine, ...]
    source: str

    def __post_init__(self) -> None:
        names = [node.name for node in self.nodes]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate grid node names: {names}")
        if self.source not in names:
            raise ValueError(f"source node {self.source!r} is not in the grid")
        known = set(names)
        line_names = [line.name for line in self.lines]
        if len(set(line_names)) != len(line_names):
            raise ValueError(f"duplicate grid line names: {line_names}")
        for line in self.lines:
            if line.node_a not in known or line.node_b not in known:
                raise ValueError(f"line {line.name!r} references an unknown node")


def _node_by_name(grid: PowerGrid, name: str) -> GridNode:
    for node in grid.nodes:
        if node.name == name:
            return node
    raise KeyError(f"unknown grid node {name!r}")


def node_field_vm(grid: PowerGrid, weapon: EmpWeapon, node_name: str) -> float:
    """E1 envelope field (V/m) at a node (nadir at the grid origin)."""
    node = _node_by_name(grid, node_name)
    range_km = math.hypot(node.x_km, node.y_km)
    return peak_e_field_vm(range_km, weapon.burst_altitude_km, weapon.yield_kt)


def lines_between(grid: PowerGrid, node_a: str, node_b: str) -> tuple[GridLine, ...]:
    """Every line directly connecting ``node_a`` and ``node_b``, in insertion order.

    A node pair may carry more than one line (parallel circuits are ordinary
    transmission redundancy), so callers that reason about connectivity must
    consider all of them rather than only the first.
    """
    found = tuple(line for line in grid.lines if {line.node_a, line.node_b} == {node_a, node_b})
    if not found:
        raise KeyError(f"no grid line connects {node_a!r} and {node_b!r}")
    return found


def line_between(grid: PowerGrid, node_a: str, node_b: str) -> GridLine:
    """The first line directly connecting ``node_a`` and ``node_b`` (or KeyError).

    With parallel circuits this returns only the first in insertion order; use
    :func:`lines_between` when every parallel circuit matters.
    """
    return lines_between(grid, node_a, node_b)[0]


def line_field_vm(grid: PowerGrid, weapon: EmpWeapon, line_name: str) -> float:
    """E1 envelope field (V/m) at a line's midpoint."""
    for line in grid.lines:
        if line.name == line_name:
            a = _node_by_name(grid, line.node_a)
            b = _node_by_name(grid, line.node_b)
            mid_x = 0.5 * (a.x_km + b.x_km)
            mid_y = 0.5 * (a.y_km + b.y_km)
            return peak_e_field_vm(math.hypot(mid_x, mid_y), weapon.burst_altitude_km, weapon.yield_kt)
    raise KeyError(f"unknown grid line {line_name!r}")


def node_survival_probability(grid: PowerGrid, weapon: EmpWeapon, node_name: str) -> float:
    """Probability a node survives the strike: ``1 - P_damage(E)``."""
    node = _node_by_name(grid, node_name)
    field = node_field_vm(grid, weapon, node_name)
    return 1.0 - damage_probability_vs_field(field, node.vulnerability_class)


def line_survival_probability(grid: PowerGrid, weapon: EmpWeapon, line_name: str) -> float:
    """Probability a line survives the strike (evaluated at its midpoint)."""
    for line in grid.lines:
        if line.name == line_name:
            field = line_field_vm(grid, weapon, line_name)
            return 1.0 - damage_probability_vs_field(field, line.vulnerability_class)
    raise KeyError(f"unknown grid line {line_name!r}")


def certainly_failed_nodes(grid: PowerGrid, weapon: EmpWeapon) -> tuple[str, ...]:
    """Nodes whose damage probability is at or above ``CERTAIN_FAILURE_PROBABILITY``.

    Ordered by grid insertion order. This is the deterministic down-set used
    for the report's headline.
    """
    failed: list[str] = []
    for node in grid.nodes:
        field = node_field_vm(grid, weapon, node.name)
        p = damage_probability_vs_field(field, node.vulnerability_class)
        if p >= CERTAIN_FAILURE_PROBABILITY:
            failed.append(node.name)
    return tuple(failed)


def path_reliability(grid: PowerGrid, weapon: EmpWeapon, path: tuple[str, ...]) -> float:
    """Survival probability of a node path: the product of every node's and
    every traversed hop's survival probability (independence assumption).

    Where a hop is served by parallel circuits the most survivable one is used,
    matching the edge relaxation in :func:`most_reliable_path`.
    """
    if not path:
        raise ValueError("path must contain at least one node")
    reliability = 1.0
    for name in path:
        reliability *= node_survival_probability(grid, weapon, name)
    for a, b in zip(path, path[1:]):
        reliability *= max(line_survival_probability(grid, weapon, line.name) for line in lines_between(grid, a, b))
    return float(reliability)


def _log_weight(survival: float) -> float:
    """Deterministic edge weight: ``-log(survival)`` (0 for survival 1)."""
    value: float = -math.log(max(survival, 1e-300))
    return value


def most_reliable_path(
    grid: PowerGrid,
    weapon: EmpWeapon,
    source: str,
    target: str,
) -> tuple[tuple[str, ...], float]:
    """Most-reliable source-to-target path and its survival probability.

    Deterministic O(V^2) Dijkstra maximising the survival-product (minimising
    ``-log`` weights); ties break by insertion order. The source node's own
    survival is included in the path reliability.
    """
    _node_by_name(grid, source)
    _node_by_name(grid, target)
    order = tuple(node.name for node in grid.nodes)
    dist = {name: math.inf for name in order}
    prev: dict[str, str | None] = {name: None for name in order}
    dist[source] = _log_weight(node_survival_probability(grid, weapon, source))
    visited: set[str] = set()

    while len(visited) < len(order):
        # Pick the unvisited node with the smallest distance. The while
        # condition guarantees this list is non-empty, and ``min`` returns the
        # first minimal element, so ties break by grid insertion order.
        current = min((name for name in order if name not in visited), key=lambda name: dist[name])
        if current == target or math.isinf(dist[current]):
            break
        visited.add(current)
        for line in grid.lines:
            neighbor: str | None = None
            if line.node_a == current:
                neighbor = line.node_b
            elif line.node_b == current:
                neighbor = line.node_a
            if neighbor is None or neighbor in visited:
                continue
            weight = _log_weight(
                node_survival_probability(grid, weapon, neighbor) * line_survival_probability(grid, weapon, line.name)
            )
            candidate = dist[current] + weight
            if candidate < dist[target] and candidate < dist[neighbor]:
                dist[neighbor] = candidate
                prev[neighbor] = current

    path: list[str] = []
    step: str | None = target
    while step is not None:
        path.append(step)
        step = prev[step]
    path.reverse()
    if path[0] != source:
        # Unreachable target: no finite path exists.
        return ((), 0.0)
    reliability = math.exp(-dist[target])
    return (tuple(path), float(reliability))


def edge_disjoint_path_count(grid: PowerGrid, source: str, target: str) -> int:
    """Number of edge-disjoint source-to-target paths (Edmonds-Karp max flow
    with unit edge capacities). Deterministic BFS in insertion order.

    Each line contributes one unit of capacity, so parallel circuits between
    the same node pair each count as a separate disjoint route.
    """
    if source == target:
        return 0
    order = tuple(node.name for node in grid.nodes)
    residual: dict[str, dict[str, int]] = {name: {} for name in order}
    for line in grid.lines:
        # Accumulate, never overwrite: parallel circuits add capacity.
        residual[line.node_a][line.node_b] = residual[line.node_a].get(line.node_b, 0) + 1
        residual[line.node_b][line.node_a] = residual[line.node_b].get(line.node_a, 0) + 1

    flow = 0
    while True:
        parent: dict[str, str | None] = {name: None for name in order}
        parent[source] = source
        queue: deque[str] = deque([source])
        found = False
        while queue:
            u = queue.popleft()
            if u == target:
                found = True
                break
            for v in order:
                if parent[v] is None and residual[u].get(v, 0) > 0:
                    parent[v] = u
                    queue.append(v)
        if not found:
            return flow
        # Unit capacities: each augmenting path pushes exactly 1 unit.
        flow += 1
        v = target
        while v != source:
            p = parent[v]
            assert p is not None and p != v
            residual[p][v] -= 1
            residual[v][p] = residual[v].get(p, 0) + 1
            v = p


def resilience_report(grid: PowerGrid, weapon: EmpWeapon) -> dict[str, Any]:
    """Full deterministic resilience assessment for the grid.

    For every critical load: most-reliable path, its survival probability, and
    the edge-disjoint path count. Network aggregates: expected served load
    (``sum(load * best-path reliability)``, documented independence
    approximation), served fraction, minimum reliability, minimum redundancy,
    and the certainly-failed down-set.
    """
    per_load: list[dict[str, Any]] = []
    total_critical = 0.0
    for node in grid.nodes:
        if not node.critical:
            continue
        total_critical += node.load_mw
        if node.name == grid.source:
            path: tuple[str, ...] = (node.name,)
            reliability = 1.0
            disjoint = 0
        else:
            path, reliability = most_reliable_path(grid, weapon, grid.source, node.name)
            disjoint = edge_disjoint_path_count(grid, grid.source, node.name)
        per_load.append(
            {
                "load": node.name,
                "load_mw": node.load_mw,
                "reliability": reliability,
                "disjoint_paths": disjoint,
                "path": path,
            }
        )

    expected_served = sum(row["reliability"] * row["load_mw"] for row in per_load)
    served_fraction = expected_served / total_critical if total_critical > 0 else 0.0
    reliabilities = [row["reliability"] for row in per_load]
    disjoint_counts = [row["disjoint_paths"] for row in per_load]

    return {
        "nodes": tuple(node.name for node in grid.nodes),
        "lines": tuple(line.name for line in grid.lines),
        "source": grid.source,
        "down_nodes": certainly_failed_nodes(grid, weapon),
        "total_critical_mw": total_critical,
        "expected_served_mw": expected_served,
        "served_fraction": served_fraction,
        "min_reliability": min(reliabilities) if reliabilities else 0.0,
        "min_disjoint_paths": min(disjoint_counts) if disjoint_counts else 0,
        "per_load": tuple(per_load),
    }
