# Standalone — GoldenEye: ARKANGEL (BOND film package)

This tree is a standalone checkout of the PROJECT BOND film package `goldeneye`
(originally `projects/working/bond/goldeneye` in the suite working tree). Its
canonical remote is `github.com/docxology/bond-goldeneye`. No DOI has been
minted, so the publication sidecars (CITATION.cff, .zenodo.json, codemeta.json)
carry no DOI or repository URL.

## Purpose

`goldeneye` is the film package for *GoldenEye* (1995), mission codename
ARKANGEL: a deterministic, tested implementation of an orbital EMP weapon
model, an electronics kill-radius analysis, and Arkangel dam-facility security
— exposed to the suite through the frozen `bond-api` `MissionProvider`
protocol.

## Run it

From the repository root, where `[tool.uv.sources]` resolves in-tree:

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90     # zero-mock, ≥90% line+branch
uv run python scripts/execute.py                       # full analysis → output/data/
uv run python scripts/z_generate_manuscript_variables.py  # tokens + figures
```

## Bare clone

`bond-api` and `bond-utilities` are suite-local packages — neither is on PyPI —
but both are vendored in this tree (`vendor/bond-api`, `vendor/bond-utilities`),
so `uv sync --extra dev` resolves them with no sibling checkout and the commands
above run unchanged.

If `uv` is unavailable, the gates still run with the vendored sources on the
interpreter path:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy matplotlib pyyaml pytest pytest-cov ruff mypy
PYTHONPATH=src:vendor/bond-api/src:vendor/bond-utilities/src \
  .venv/bin/python -m pytest tests/ --cov=src --cov-fail-under=90
```

`src` belongs on `PYTHONPATH` (not just in the pytest process) because several
tests exercise the core in a spawned interpreter, the way an editable install
of `goldeneye` would expose it inside the suite.

`pyproject.toml` carries the `pytest`, `coverage` and `mypy` settings, so those
gates behave identically here and in the suite. `ruff` does not: the package
deliberately inherits `[tool.ruff]` from the suite root, so standalone defaults
disagree with the committed formatting (`ruff format --check --line-length 120`
reproduces the suite's clean 48-file result) and newer ruff versions also enable
rule families this code does not target. Run the full ruff gate through the
suite's `uv run`.

See `README.md` for the full quick start and `TODO.md` for the build record and
declared integration points. This package is one of many films implementing the
frozen `bond-api` contract.
