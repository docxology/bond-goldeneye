"""Claim-ledger binding: every row of ``data/claim_ledger.yaml`` must equal its
named module constant or the live ``analyze_arkangel`` output.

The ledger is the human-facing evidence registry for claims that are sourced
from code or generated reports. It was previously unbound (V1): a scenario or
constant change left it silently stale. Each row now carries a machine-readable
``binding`` (``module_attr:<mod>.<ATTR>`` or ``analysis_path:<dotted>``); this
test resolves every row against source and fails if any value has drifted. A
negative control proves a perturbed ledger value is caught.

Zero mock: real computation + the committed ledger file."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from goldeneye.scenario import ARKANGEL, analyze_arkangel

LEDGER_PATH = Path(__file__).resolve().parents[1] / "data" / "claim_ledger.yaml"

#: Relative tolerance for ``generated_metric`` rows (ledger numbers are rounded
#: to a few significant figures); module constants are pinned tight.
_TOL = {"generated_metric": 2e-2}


def _resolve_module_attr(spec: str) -> float:
    module_name, _, attr = spec.partition(".")
    import importlib

    module = importlib.import_module(f"goldeneye.{module_name}")
    return float(getattr(module, attr))


def _resolve_analysis_path(spec: str) -> float:
    analysis = analyze_arkangel(ARKANGEL)
    value: object = analysis
    for segment in spec.split("."):
        if segment.lstrip("-").isdigit():
            value = value[int(segment)]  # type: ignore[index]
        else:
            value = value[segment]  # type: ignore[index]
    return float(value)  # type: ignore[arg-type]


def _resolve_binding(binding: str) -> float:
    kind, _, spec = binding.partition(":")
    if kind == "module_attr":
        return _resolve_module_attr(spec)
    if kind == "analysis_path":
        return _resolve_analysis_path(spec)
    raise ValueError(f"unknown binding kind {kind!r} in {binding!r}")


def _mismatches(rows: object) -> list[tuple[str, float, float]]:
    bad: list[tuple[str, float, float]] = []
    for claim in rows:  # type: ignore[union-attr]
        tol = _TOL.get(str(claim["source_tier"]), 1e-3)
        expected: float = float(claim["value"])
        if not expected == pytest.approx(result := _resolve_binding(str(claim["binding"])), rel=tol):
            bad.append((str(claim["claim_id"]), expected, result))
    return bad


class TestClaimLedgerBound:
    def test_every_row_matches_source(self) -> None:
        rows = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))["claims"]
        assert len(rows) >= 19, "ledger collapsed"
        assert not _mismatches(rows), _mismatches(rows)

    def test_every_row_has_a_binding(self) -> None:
        rows = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))["claims"]
        for claim in rows:
            assert claim["binding"], claim["claim_id"]
            assert str(claim["binding"]).startswith(("module_attr:", "analysis_path:"))

    def test_negative_control_perturbed_value_is_caught(self, tmp_path: Path) -> None:
        """Halving one ledger value must trip the resolver."""
        rows = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))["claims"]
        rows[0] = {**rows[0], "value": float(rows[0]["value"]) / 2.0}
        assert _mismatches(rows), "negative control inert — resolver is not sensitive"

    def test_known_module_constant_resolves(self) -> None:
        rows = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))["claims"]
        by_id = {c["claim_id"]: c for c in rows}
        e1 = by_id["emp-e1-reference-vm"]
        assert _resolve_binding(str(e1["binding"])) == 50000.0
        assert by_id["emp-nadir-field-arkangel"]["binding"].startswith("analysis_path:")
