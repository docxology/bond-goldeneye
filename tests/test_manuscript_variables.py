"""Manuscript-variable tests: config loading, token map, and live cross-reference.

The live cross-reference gate (``test_all_manuscript_tokens_are_generated``)
scans every manuscript section for ``{{TOKEN}}`` and fails if any token is
missing from :func:`~goldeneye.manuscript_variables.generate_variables` — the
same gate that keeps prose from drifting from the code.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from goldeneye import breach_hydrograph, coupling, dam_security, emp_model, orbital_mechanics
from goldeneye.manuscript_variables import (
    PACKAGE_ROOT,
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)

_TOKEN_ARG = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_generate_variables_defaults() -> None:
    variables = generate_variables()
    assert variables["GE_IDENTITY"] == "GOLDENEYE"
    assert variables["GE_CODENAME"] == "ARKANGEL"
    assert variables["GE_VERSION"] == "0.1.0"
    assert variables["GE_NUM_CLASSES"] == "4"
    assert all(isinstance(value, str) for value in variables.values())

    # Scenario-derived values must be present and non-empty.
    for key in (
        "GE_YIELD_KT",
        "GE_BURST_ALTITUDE_KM",
        "GE_NADIR_FIELD_VM",
        "GE_RADIUS_MILITARY_KM",
        "GE_PEAK_DISCHARGE_CMS",
        "GE_FLOOD_RISK",
        "GE_ACCESS_DETECT_PROB",
        "GE_SECURITY_SCORE",
    ):
        assert variables[key] not in ("", "nan")


def test_manuscript_token_values_are_sensible() -> None:
    v = generate_variables()
    assert float(v["GE_RADIUS_UNPROTECTED_KM"]) > 1000.0
    assert float(v["GE_RADIUS_LEGACY_TUBE_KM"]) == 0.0
    assert float(v["GE_NADIR_FIELD_VM"]) > 80000.0
    assert v["GE_FLOOD_RISK"] == "extreme"
    assert 0 < float(v["GE_SECURITY_SCORE"]) <= 100


def test_all_manuscript_tokens_are_generated() -> None:
    variables = generate_variables()
    used: set[str] = set()
    for section in sorted(PACKAGE_ROOT.glob("manuscript/[0-9][0-9]_*.md")):
        used.update(_TOKEN_ARG.findall(section.read_text(encoding="utf-8")))
    assert used, "manuscript sections use no tokens — the gate would be vacuous"
    missing = used - set(variables)
    assert missing == set(), f"manuscript tokens missing from generate_variables(): {sorted(missing)}"


def test_generate_variables_custom_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        'paper:\n  title: "Custom Title"\n  subtitle: "Custom Subtitle"\n  version: "9.9.9"\n',
        encoding="utf-8",
    )
    variables = generate_variables(config_path=config)
    assert variables["GE_TITLE"] == "Custom Title"
    assert variables["GE_SUBTITLE"] == "Custom Subtitle"
    assert variables["GE_VERSION"] == "9.9.9"


def test_generate_variables_draft_mode(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text('paper:\n  title: "T"\n  version: "1.0"\n', encoding="utf-8")
    # require_outputs=False must still succeed.
    variables = generate_variables(config_path=config, require_outputs=False)
    assert variables["GE_TITLE"] == "T"


def test_load_manuscript_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manuscript_config(tmp_path / "nope.yaml")


def test_load_manuscript_config_non_mapping(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("just a string\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level mapping"):
        load_manuscript_config(config)


def test_generate_variables_paper_must_be_mapping(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("paper: [1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section"):
        generate_variables(config_path=config)


class TestResolveTree:
    def test_resolve_substitutes_tokens(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "00_abstract.md").write_text(
            "Mission {{GE_CODENAME}} on film {{GE_IDENTITY}}.\n", encoding="utf-8"
        )
        output = tmp_path / "out"
        resolved_dir, files = resolve_manuscript_tree(
            {"GE_CODENAME": "ARKANGEL", "GE_IDENTITY": "GOLDENEYE"},
            manuscript_dir=manuscript,
            output_dir=output,
        )
        assert resolved_dir == output
        assert files == ["00_abstract.md"]
        text = (output / "00_abstract.md").read_text(encoding="utf-8")
        assert text == "Mission ARKANGEL on film GOLDENEYE.\n"

    def test_resolve_strict_fails_on_unknown_token(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "00_abstract.md").write_text("Leftover {{UNKNOWN_TOKEN}} here.\n", encoding="utf-8")
        with pytest.raises(ValueError, match="UNKNOWN_TOKEN"):
            resolve_manuscript_tree(
                {"GE_CODENAME": "ARKANGEL"},
                manuscript_dir=manuscript,
                output_dir=tmp_path / "out",
            )

    def test_resolve_lenient_keeps_unknown(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "00_abstract.md").write_text("Leftover {{UNKNOWN_TOKEN}} here.\n", encoding="utf-8")
        _, files = resolve_manuscript_tree(
            {"GE_CODENAME": "ARKANGEL"},
            manuscript_dir=manuscript,
            output_dir=tmp_path / "out",
            strict=False,
        )
        assert files == ["00_abstract.md"]
        text = (tmp_path / "out" / "00_abstract.md").read_text(encoding="utf-8")
        assert "{{UNKNOWN_TOKEN}}" in text

    def test_resolve_ignores_sidecar_files(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "00_abstract.md").write_text("ok\n", encoding="utf-8")
        (manuscript / "README.md").write_text("not a section\n", encoding="utf-8")
        _, files = resolve_manuscript_tree(
            {"A": "1"},
            manuscript_dir=manuscript,
            output_dir=tmp_path / "out",
            strict=False,
        )
        assert files == ["00_abstract.md"]


class TestStrictModeGate:
    """The strict-mode gate must be falsifiable, not green by construction.

    It replaced a ``not kill_table`` check that could never fire (the kill
    table is built from a non-empty module constant), so it carries its own
    positive control: a real config that drives a real token to infinity.
    """

    _DEGENERATE = (
        "paper:\n"
        '  title: "Degenerate"\n'
        '  version: "0.0.0"\n'
        "scenario:\n"
        "  coupling:\n"
        # An absurd shield thickness overflows the absorption term (8.686*t/delta)
        # and drives GE_COUPLING_SE_DB to infinity.
        "    shield_thickness_mm: 1.0e308\n"
    )

    def test_gate_rejects_non_finite_token(self, tmp_path: Path) -> None:
        config = tmp_path / "config.yaml"
        config.write_text(self._DEGENERATE, encoding="utf-8")
        with pytest.raises(ValueError, match="non-finite manuscript tokens"):
            generate_variables(config_path=config)

    def test_gate_names_the_offending_token(self, tmp_path: Path) -> None:
        config = tmp_path / "config.yaml"
        config.write_text(self._DEGENERATE, encoding="utf-8")
        with pytest.raises(ValueError, match="GE_COUPLING_SE_DB"):
            generate_variables(config_path=config)

    def test_draft_mode_bypasses_the_gate(self, tmp_path: Path) -> None:
        config = tmp_path / "config.yaml"
        config.write_text(self._DEGENERATE, encoding="utf-8")
        variables = generate_variables(config_path=config, require_outputs=False)
        assert not math.isfinite(float(variables["GE_COUPLING_SE_DB"]))

    def test_canonical_scenario_passes_the_gate(self) -> None:
        # The negative control: the shipped scenario must clear it.
        variables = generate_variables()
        assert variables["GE_CODENAME"] == "ARKANGEL"


class TestModelConstantsAreTokenized:
    """Rule 6 was prose-only; this makes it a gate.

    Every empirical model coefficient quoted in the methodology must reach the
    page through a ``{{TOKEN}}`` bound to the module constant that defines it.
    Retyping the literal in prose is what let a wrong Froehlich factor and a
    units-broken Schelkunoff form sit in the manuscript unnoticed.
    """

    #: token name -> (module constant, literal that must NOT appear in prose)
    REGISTRY: dict[str, tuple[float, str]] = {
        "GE_FROEHLICH_PEAK_COEFF": (dam_security.FROEHLICH_PEAK_COEFFICIENT, "0.607"),
        "GE_FROEHLICH_PEAK_VOL_EXP": (dam_security.FROEHLICH_PEAK_VOLUME_EXPONENT, "0.295"),
        "GE_FROEHLICH_PEAK_HEAD_EXP": (dam_security.FROEHLICH_PEAK_HEAD_EXPONENT, "1.24"),
        "GE_RITTER_DEPTH_COEFF": (dam_security.RITTER_DEPTH_COEFFICIENT, "4H/9"),
        "GE_FROEHLICH_WIDTH_COEFF": (breach_hydrograph.FROEHLICH_WIDTH_COEFFICIENT, "0.27"),
        "GE_FROEHLICH_K0_OVERTOPPING": (breach_hydrograph.FROEHLICH_OVERTOPPING_FACTOR, "1.3\\,"),
        "GE_FROEHLICH_K0_PIPING": (breach_hydrograph.FROEHLICH_PIPING_FACTOR, "K_0 = 1.0"),
        "GE_FROEHLICH_WIDTH_VOL_EXP": (breach_hydrograph.FROEHLICH_WIDTH_VOLUME_EXPONENT, "0.32"),
        "GE_FROEHLICH_WIDTH_HEAD_EXP": (breach_hydrograph.FROEHLICH_WIDTH_HEAD_EXPONENT, "0.04"),
        "GE_ABSORPTION_DB_PER_SKIN_DEPTH": (coupling.ABSORPTION_DB_PER_SKIN_DEPTH, "8.686"),
        "GE_FREE_SPACE_IMPEDANCE_OHM": (coupling.FREE_SPACE_IMPEDANCE_OHM, "376.7"),
        "GE_MU_EARTH_M3S2": (orbital_mechanics.MU_EARTH, "3.986\\times"),
        "GE_E1_REFERENCE_VM": (emp_model.E1_REFERENCE_VM, "50000"),
        "GE_YIELD_EXPONENT": (emp_model.YIELD_SCALING_EXPONENT, "0.85"),
    }

    @staticmethod
    def _sections() -> dict[str, str]:
        return {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(PACKAGE_ROOT.glob("manuscript/[0-9][0-9]_*.md"))
        }

    def test_registry_is_non_empty(self) -> None:
        # Guard against a vacuous sweep if the registry is ever emptied.
        assert len(self.REGISTRY) >= 10

    @staticmethod
    def _as_number(rendered: str) -> float:
        """Parse a token value, including the LaTeX scientific form."""
        return float(rendered.replace("\\times 10^{", "e").replace("}", ""))

    def test_every_registered_token_resolves_to_its_module_constant(self) -> None:
        variables = generate_variables()
        for token, (constant, _literal) in self.REGISTRY.items():
            assert token in variables, f"{token} missing from generate_variables()"
            assert self._as_number(variables[token]) == pytest.approx(constant, rel=1e-4), token

    def test_every_registered_token_is_actually_used_in_the_manuscript(self) -> None:
        used: set[str] = set()
        for text in self._sections().values():
            used.update(_TOKEN_ARG.findall(text))
        unused = sorted(set(self.REGISTRY) - used)
        assert unused == [], f"registered model constants never referenced in prose: {unused}"

    def test_no_registered_constant_is_retyped_as_a_literal(self) -> None:
        offenders: list[str] = []
        for name, text in self._sections().items():
            for token, (_constant, literal) in self.REGISTRY.items():
                if literal in text:
                    offenders.append(f"{name}: {literal!r} retyped instead of {{{{{token}}}}}")
        assert offenders == [], "\n".join(offenders)


def test_deepened_tokens_present_and_sensible() -> None:
    v = generate_variables()
    assert float(v["GE_ORBIT_PERIOD_MIN"]) > 80.0
    assert 7.0 < float(v["GE_ORBIT_SPEED_KMS"]) < 8.0
    assert float(v["GE_COUPLING_INDUCED_V"]) > 10000.0
    # 0.1 mm aluminium at 100 MHz: 106.0 dB absorption + 86.3 dB reflection.
    # Pinned to the hand-computed physics, not re-derived from the module.
    assert float(v["GE_COUPLING_SE_DB"]) == pytest.approx(192.3, abs=0.5)
    assert float(v["GE_GRID_SERVED_FRACTION"]) > 0.0
    assert int(v["GE_GRID_MIN_DISJOINT_PATHS"]) >= 2
    # Froehlich (2008) with the correct K0 = 1.3: 0.27*1.3*(1.3e8)^0.32*75^0.04.
    assert float(v["GE_BREACH_WIDTH_M"]) == pytest.approx(164.7, abs=0.5)
    assert int(v["GE_NUM_STATIONS"]) == 3
    assert float(v["GE_MEAN_OUTFLOW_CMS"]) > 0.0
