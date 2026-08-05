"""In-process tests for the ARKANGEL figure generators.

The figures are normally rendered by the ``z_generate_manuscript_variables.py``
subprocess; these tests render them in-process so the matplotlib code paths are
covered by the coverage gate. Real rendering, no mocks.
"""

from __future__ import annotations

from pathlib import Path

from goldeneye.figures.emp_footprint import plot_emp_footprint
from goldeneye.figures.flood_wave import plot_flood_wave
from goldeneye.scenario import ARKANGEL, ArkangelScenario
from goldeneye.emp_model import EmpWeapon
from goldeneye.dam_security import Reservoir

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _assert_png(path: Path, minimum_bytes: int = 20000) -> None:
    assert path.is_file()
    data = path.read_bytes()
    assert data[:8] == _PNG_MAGIC
    assert len(data) > minimum_bytes


def test_emp_footprint_renders(tmp_path: Path) -> None:
    out = plot_emp_footprint(tmp_path / "figures" / "emp_footprint.png", ARKANGEL)
    _assert_png(out)


def test_flood_wave_renders(tmp_path: Path) -> None:
    out = plot_flood_wave(tmp_path / "flood_wave.png", ARKANGEL)
    _assert_png(out)


def test_figures_use_custom_scenario(tmp_path: Path) -> None:
    sc = ArkangelScenario(
        weapon=EmpWeapon(yield_kt=500.0, burst_altitude_km=150.0),
        reservoir=Reservoir("small", 5.0e7, 40.0),
        facility_distance_km=3.0,
        facility_elevation_m=5.0,
    )
    emp = plot_emp_footprint(tmp_path / "emp_custom.png", sc)
    flood = plot_flood_wave(tmp_path / "flood_custom.png", sc)
    _assert_png(emp)
    _assert_png(flood, minimum_bytes=10000)


def test_figure_returns_same_path(tmp_path: Path) -> None:
    target = tmp_path / "target.png"
    assert plot_emp_footprint(target, ARKANGEL) == target


def test_grid_resilience_renders(tmp_path: Path) -> None:
    from goldeneye.figures.grid_resilience import plot_grid_resilience

    out = plot_grid_resilience(tmp_path / "grid.png", ARKANGEL)
    assert out.is_file()
    data = out.read_bytes()
    assert data[:8] == _PNG_MAGIC
    assert len(data) > 10000
