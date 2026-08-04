# manuscript/ — GoldenEye: ARKANGEL technical manuscript

This directory holds the manuscript for the goldeneye BOND film package
(*GoldenEye*, 1995; mission codename ARKANGEL).

| File | Role |
|---|---|
| `NN_*.md` | Numbered prose sections (`00_abstract` … `07_scope_and_related_work`, `99_references`). Tokens resolve through `src/goldeneye/manuscript_variables.py`. |
| `config.yaml` | Paper identity + scenario parameters. Single source of truth for all tokens. |
| `config.yaml.example` | Reference copy of `config.yaml`. |
| `SYNTAX.md` | Token and figure syntax reference. |
| `references.bib` | Bibliography (BibTeX). |
| `layer_contract.yaml` | Declarative layer-contract record. |
| `preamble.md` | LaTeX preamble injections (empty by default). |

## Editing protocol

- **Never** hand-author a numeric result in a section; use a token. The live
  cross-reference test in `tests/test_manuscript_variables.py` fails on any
  token absent from `generate_variables()`.
- Do not put a literal double-brace example (for example a literal token like
  `{{VARIABLE}}`) inside a numbered `NN_*.md` section — the cross-reference
  scan would flag it as a missing token. Keep such illustrations in
  `SYNTAX.md`.
- To change scenario behaviour, edit `config.yaml` and/or the defaults in
  `src/goldeneye/scenario.py`, then re-run the regenerate script.
