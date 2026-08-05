"""GoldenEye: ARKANGEL — Special-Agent Mission Software.

A BOND-suite film package for *GoldenEye* (1995), mission codename ARKANGEL.
It models an orbital EMP weapon and its ground effects, electronics kill
radii, EM coupling/shielding, regional power-network resilience, and the
Arkangel dam-facility security and breach-flood risk.

This package is deliberately *not* a BOND-layer dependency: importing
:mod:`goldeneye` never imports ``bond_api``. The pure domain core
(:mod:`goldeneye.emp_model`, :mod:`goldeneye.kill_radius`,
:mod:`goldeneye.dam_security`, :mod:`goldeneye.orbital_mechanics`,
:mod:`goldeneye.coupling`, :mod:`goldeneye.grid_resilience`,
:mod:`goldeneye.breach_hydrograph`, :mod:`goldeneye.scenario`) is importable in
any environment; :mod:`goldeneye.mission` is the thin adapter that implements
the frozen ``bond_api.MissionProvider`` protocol and is imported only by
scripts and discovery.
"""

from __future__ import annotations

from goldeneye import (
    breach_hydrograph,
    coupling,
    dam_security,
    emp_model,
    grid_resilience,
    kill_radius,
    orbital_mechanics,
    scenario,
)
from goldeneye.breach_hydrograph import Station
from goldeneye.dam_security import Reservoir, SecurityLayer
from goldeneye.emp_model import EmpWeapon
from goldeneye.grid_resilience import GridLine, GridNode, PowerGrid
from goldeneye.kill_radius import VulnerabilityClass
from goldeneye.orbital_mechanics import OrbitGeometry
from goldeneye.scenario import (
    ARKANGEL,
    ArkangelScenario,
    CouplingParams,
    analyze_arkangel,
    load_scenario_config,
)

__all__ = [
    "ARKANGEL",
    "ArkangelScenario",
    "CouplingParams",
    "EmpWeapon",
    "GridLine",
    "GridNode",
    "OrbitGeometry",
    "PowerGrid",
    "Reservoir",
    "SecurityLayer",
    "Station",
    "VulnerabilityClass",
    "analyze_arkangel",
    "breach_hydrograph",
    "coupling",
    "dam_security",
    "emp_model",
    "grid_resilience",
    "kill_radius",
    "load_scenario_config",
    "orbital_mechanics",
    "scenario",
]

__version__ = "0.1.0"
