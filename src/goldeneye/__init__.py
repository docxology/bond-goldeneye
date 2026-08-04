"""GoldenEye: ARKANGEL — Special-Agent Mission Software.

A BOND-suite film package for *GoldenEye* (1995), mission codename ARKANGEL.
It models an orbital EMP weapon, the electronics kill-radius analysis, and the
Arkangel dam-facility security and flood risk.

This package is deliberately *not* a BOND-layer dependency: importing
:mod:`goldeneye` never imports ``bond_api``. The pure domain core
(:mod:`goldeneye.emp_model`, :mod:`goldeneye.kill_radius`,
:mod:`goldeneye.dam_security`, :mod:`goldeneye.scenario`) is importable in any
environment; :mod:`goldeneye.mission` is the thin adapter that implements the
frozen ``bond_api.MissionProvider`` protocol and is imported only by scripts
and discovery.
"""

from __future__ import annotations

from goldeneye import dam_security, emp_model, kill_radius, scenario
from goldeneye.emp_model import EmpWeapon
from goldeneye.dam_security import Reservoir, SecurityLayer
from goldeneye.kill_radius import VulnerabilityClass
from goldeneye.scenario import ARKANGEL, ArkangelScenario, analyze_arkangel, load_scenario_config

__all__ = [
    "ARKANGEL",
    "ArkangelScenario",
    "EmpWeapon",
    "Reservoir",
    "SecurityLayer",
    "VulnerabilityClass",
    "analyze_arkangel",
    "dam_security",
    "emp_model",
    "kill_radius",
    "load_scenario_config",
    "scenario",
]

__version__ = "0.1.0"
