"""Subprocess smoke tests for the thin ARKANGEL CLIs (scripts/).

Each orchestration script is invoked with the venv ``sys.executable`` from the
project root (as documented). Exit codes and regenerable artifacts under
``output/`` are asserted; ``output/`` is gitignored so the tree stays clean.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
OUTPUT = PROJECT_ROOT / "output"


def _run(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_brief_exit_zero() -> None:
    proc = _run("brief.py")
    assert proc.returncode == 0, proc.stderr
    assert "ARKANGEL" in proc.stdout
    assert "GOLDENEYE" in proc.stdout


def test_recon_exit_zero() -> None:
    proc = _run("recon.py")
    assert proc.returncode == 0, proc.stderr
    assert "[goal]" in proc.stdout

    proc_custom = _run("recon.py", "custom goal text")
    assert proc_custom.returncode == 0
    assert "custom goal text" in proc_custom.stdout


def test_plan_exit_zero() -> None:
    proc = _run("plan.py")
    assert proc.returncode == 0, proc.stderr
    assert "synthesize" in proc.stdout


def test_execute_writes_artifacts() -> None:
    proc = _run("execute.py")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "data" / "arkangel_outcome.json").is_file()
    assert (OUTPUT / "data" / "arkangel_mission.json").is_file()
    assert "EXECUTION REPORT" in proc.stdout


def test_debrief_requires_execute_first() -> None:
    # Running debrief before execute (absent artifact) exits 1 with guidance.
    artifact = OUTPUT / "data" / "arkangel_outcome.json"
    backup = None
    if artifact.is_file():
        backup = artifact.read_bytes()
        artifact.unlink()
    try:
        proc = _run("debrief.py")
        assert proc.returncode == 1
        assert "execute.py" in proc.stdout
    finally:
        if backup is not None:
            artifact.write_bytes(backup)


def test_debrief_after_execute() -> None:
    _run("execute.py")
    proc = _run("debrief.py")
    assert proc.returncode == 0, proc.stderr
    assert "GOLDENEYE :: ARKANGEL" in proc.stdout or "ARKANGEL — DEBRIEF" in proc.stdout


def test_z_generate_manuscript_variables() -> None:
    proc = _run("z_generate_manuscript_variables.py")
    assert proc.returncode == 0, proc.stderr
    assert (OUTPUT / "data" / "manuscript_variables.json").is_file()
    assert (OUTPUT / "figures" / "emp_footprint.png").is_file()
    assert (OUTPUT / "figures" / "flood_wave.png").is_file()
    assert (OUTPUT / "figures" / "grid_resilience.png").is_file()
    assert (OUTPUT / "manuscript" / "00_abstract.md").is_file()


def test_figures_are_pngs() -> None:
    for name in ("emp_footprint.png", "flood_wave.png", "grid_resilience.png"):
        path = OUTPUT / "figures" / name
        assert path.is_file()
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
