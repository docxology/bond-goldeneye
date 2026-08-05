# src/goldeneye/ — source

GoldenEye: ARKANGEL domain core and BOND protocol adapter.

## Module map

| Module | Responsibility | Layer |
| --- | --- | --- |
| `emp_model.py` | Orbital EMP threat envelope, geometry/horizon, waveform | pure core |
| `kill_radius.py` | Electronics kill radii by vulnerability class | pure core |
| `dam_security.py` | Arkangel access control + breach-flood risk | pure core |
| `orbital_mechanics.py` | Orbital platform: Keplerian period/speed, pass geometry | pure core |
| `coupling.py` | Skin depth, Schelkunoff SE, conductor coupling | pure core |
| `grid_resilience.py` | Regional network resilience (reliability, redundancy) | pure core |
| `breach_hydrograph.py` | Froehlich (2008) breach width + triangular hydrograph | pure core |
| `scenario.py` | ARKANGEL composition, config loading, analysis, input hash | pure core |
| `mission.py` | Frozen `bond_api.MissionProvider` adapter + gadget registry | protocol adapter |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from config + scenario | manuscript |
| `figures/` | `emp_footprint.py`, `flood_wave.py`, `grid_resilience.py` (deterministic PNGs) | figures |

## Layer contract

- Pure-core modules (`emp_model`, `kill_radius`, `dam_security`, `scenario`)
  must **not** import `bond_api`, `bond_utilities`, or `infrastructure`; they
  are importable in any Python environment.
- `mission.py` is the **only** module that imports `bond_api`. It implements
  the frozen protocol (do not rename `MissionProvider` or change method
  signatures) and registers gadgets with `bond_api.GadgetRegistry` under
  `goldeneye` at import time.
- `manuscript_variables.py` and `figures/` are pure w.r.t. BOND (they never
  import `bond_api` either) and may use numpy/matplotlib/yaml.

## Determinism

Fixed scenario parameters, seed 0, no wall-clock in analysis artifacts. Every
public function is annotated and documented; matches `ruff format`.

## Verification

```bash
uv run mypy src/
rg -n "^(from|import) (bond_|infrastructure)" src/goldeneye/ || echo "pure core clean"
```
