"""Pytest configuration for the goldeneye BOND film package."""

from __future__ import annotations

import os
import sys

# Force the headless matplotlib backend before any pyplot import in tests.
os.environ.setdefault("MPLBACKEND", "Agg")

# Make src/ importable directly (the project pyproject's ``pythonpath`` also
# covers it; belt-and-suspenders for subprocess-style checks). bond-api and
# bond-utilities resolve from the installed editable path dependencies.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(PROJECT_ROOT, "src")
for _path in (SRC, PROJECT_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)
