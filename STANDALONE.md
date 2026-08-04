# Standalone — GoldenEye: ARKANGEL (BOND film package)

This is a **local-only** working tree in the PROJECT BOND suite
(`projects/working/bond/goldeneye`). There is **no remote and it must never be
pushed**; publication sidecars (CITATION.cff, .zenodo.json, codemeta.json)
therefore carry no DOI or repository URL.

## Purpose

`goldeneye` is the film package for *GoldenEye* (1995), mission codename
ARKANGEL: a deterministic, tested implementation of an orbital EMP weapon
model, an electronics kill-radius analysis, and Arkangel dam-facility security
— exposed to the suite through the frozen `bond-api` `MissionProvider`
protocol.

## Run it

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90     # zero-mock, ≥90% line+branch
uv run python scripts/execute.py                       # full analysis → output/data/
uv run python scripts/z_generate_manuscript_variables.py  # tokens + figures
```

See `README.md` for the full quick start and `TODO.md` for the build record and
declared integration points. This package is one of many films implementing the
frozen `bond-api` contract.
