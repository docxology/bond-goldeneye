"""Regeneration-determinism gate for the byte-identity claim.

``manuscript/06_reproducibility.md`` claims that re-running ``execute.py`` and
``z_generate_manuscript_variables.py`` in one environment rewrites a named set
of artifacts byte for byte. This module *runs the real generators twice in the
same test* and compares the persisted bytes — it does not inject a fixed clock,
because a fixed-clock test is exactly what let a wall-clock
``GENERATION_TIMESTAMP`` token render into the manuscript while the prose
claimed byte-identity.

The covered set and the one documented exclusion are pinned here so the prose
and the gate cannot drift apart:

* covered — ``data/arkangel_outcome.json``, ``data/manuscript_variables.json``,
  ``manuscript/*.md``, ``figures/*.png``
* excluded — ``data/arkangel_mission.json``, the run-scoped provenance record
  that deliberately carries a real ``started_at`` wall clock.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from goldeneye.manuscript_variables import generate_variables

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
OUTPUT = PROJECT_ROOT / "output"

#: Globs naming exactly the artifacts the byte-identity claim covers.
COVERED_GLOBS = (
    "data/arkangel_outcome.json",
    "data/manuscript_variables.json",
    "manuscript/*.md",
    "figures/*.png",
)

#: Documented exclusion — run-scoped provenance, wall clock permitted.
EXCLUDED_ARTIFACT = OUTPUT / "data" / "arkangel_mission.json"

#: Matches an ISO-8601 date *with a time of day* — i.e. a wall-clock stamp.
_WALL_CLOCK_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")

#: Clock-reading calls that must never appear in the token generator.
_CLOCK_CALLS = ("datetime.now(", "datetime.utcnow(", "time.time(", "time.monotonic(")


def _covered_files() -> list[Path]:
    """Every existing artifact matched by :data:`COVERED_GLOBS`, sorted."""
    files: list[Path] = []
    for pattern in COVERED_GLOBS:
        files.extend(OUTPUT.glob(pattern))
    return sorted(files)


def _digest_map() -> dict[str, str]:
    """Map ``output/``-relative path -> SHA-256 of the file's bytes."""
    return {str(path.relative_to(OUTPUT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in _covered_files()}


def _regenerate() -> None:
    """Run both persisting orchestrators, failing the test on a bad exit code."""
    for script in ("execute.py", "z_generate_manuscript_variables.py"):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"{script} failed ({proc.returncode}): {proc.stderr}"


class TestRegenerationIsByteIdentical:
    """The claim itself: two full regenerations, compared byte for byte."""

    def test_two_regenerations_write_the_same_bytes(self) -> None:
        _regenerate()
        first = _digest_map()
        _regenerate()
        second = _digest_map()

        assert first, "no covered artifacts found — the comparison would be vacuous"
        assert set(first) == set(second), "regeneration changed the covered file set"
        differing = sorted(name for name in first if first[name] != second[name])
        assert differing == [], (
            f"regeneration is not byte-identical; these covered artifacts changed between two runs: {differing}"
        )

    def test_covered_set_is_the_set_the_manuscript_names(self) -> None:
        """Guard against a green run over an empty or shrunken artifact set."""
        _regenerate()
        names = set(_digest_map())
        assert "data/arkangel_outcome.json" in names
        assert "data/manuscript_variables.json" in names
        section_count = sum(1 for name in names if name.startswith("manuscript/"))
        figure_count = sum(1 for name in names if name.startswith("figures/"))
        assert section_count >= 8, f"expected the resolved sections, got {section_count}"
        assert figure_count == 3, f"expected three figures, got {figure_count}"

    def test_digest_map_detects_a_single_changed_byte(self) -> None:
        """Positive control: the comparison machinery can actually see a change."""
        _regenerate()
        before = _digest_map()
        victim = OUTPUT / "manuscript" / "00_abstract.md"
        original = victim.read_bytes()
        try:
            victim.write_bytes(original + b"\n")
            after = _digest_map()
        finally:
            victim.write_bytes(original)
        changed = [name for name in before if before[name] != after[name]]
        assert changed == ["manuscript/00_abstract.md"]


class TestNoWallClockInCoveredArtifacts:
    """No covered artifact may carry a generation timestamp."""

    def test_no_generated_token_is_a_wall_clock(self) -> None:
        offenders = sorted(token for token, value in generate_variables().items() if _WALL_CLOCK_RE.search(value))
        assert offenders == [], f"wall-clock value in manuscript tokens: {offenders}"

    def test_persisted_token_map_has_no_wall_clock(self) -> None:
        _regenerate()
        persisted = json.loads((OUTPUT / "data" / "manuscript_variables.json").read_text(encoding="utf-8"))
        offenders = sorted(token for token, value in persisted.items() if _WALL_CLOCK_RE.search(str(value)))
        assert offenders == [], f"wall-clock value persisted in manuscript_variables.json: {offenders}"

    def test_resolved_sections_have_no_wall_clock(self) -> None:
        _regenerate()
        offenders = sorted(
            path.name
            for path in (OUTPUT / "manuscript").glob("*.md")
            if _WALL_CLOCK_RE.search(path.read_text(encoding="utf-8"))
        )
        assert offenders == [], f"wall-clock value rendered into manuscript prose: {offenders}"

    def test_token_generator_reads_no_clock(self) -> None:
        source = (PROJECT_ROOT / "src" / "goldeneye" / "manuscript_variables.py").read_text(encoding="utf-8")
        found = sorted(call for call in _CLOCK_CALLS if call in source)
        assert found == [], f"manuscript_variables.py reads the clock: {found}"

    def test_manuscript_date_token_comes_from_committed_config(self) -> None:
        variables = generate_variables()
        config_text = (PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
        assert variables["GE_MANUSCRIPT_DATE"], "GE_MANUSCRIPT_DATE must not be empty"
        assert variables["GE_MANUSCRIPT_DATE"] in config_text


class TestDocumentedExclusion:
    """The excluded provenance record is excluded *because* it holds a clock."""

    def test_provenance_record_is_outside_the_covered_set(self) -> None:
        _regenerate()
        assert EXCLUDED_ARTIFACT.is_file()
        assert str(EXCLUDED_ARTIFACT.relative_to(OUTPUT)) not in _digest_map()

    def test_provenance_record_carries_a_real_started_at(self) -> None:
        _regenerate()
        record = json.loads(EXCLUDED_ARTIFACT.read_text(encoding="utf-8"))
        assert "started_at" in record, "the exclusion is only justified by a real wall clock"
        assert _WALL_CLOCK_RE.search(str(record["started_at"]))
