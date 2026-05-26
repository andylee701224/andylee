# POC Module Checklist

Mirror the reference `mems_poc/` layout. Each module has a single responsibility — keep them split.

---

## `requirements.txt`

```
numpy>=1.24
scipy>=1.10
pytest>=7.4
```

Add `gymnasium`, `stable-baselines3` only if the user explicitly asks for an RL extension.

## `mems_vpc/__init__.py`

Re-export the public dataclasses so callers don't reach into submodules:

```python
from .schemas import (
    AlloyCandidate, CoatingCandidate, CeramicSpec,
    ProbeSpec, Combo, MeasurementRecord, Stage, GateDecision,
)
```

## `mems_vpc/schemas.py`

- Frozen dataclasses for `AlloyCandidate`, `CoatingCandidate`, `CeramicSpec`, `ProbeSpec`, `Combo`.
- Mutable `MeasurementRecord` (lab adapters fill fields incrementally).
- Enums: `DepositionMethod`, `FormingMethod`, `DrillingMethod`, `Stage`.
- `Combo.id` MUST include the ceramic drilling method to avoid collisions.
- `CoatingCandidate.tip_material` property returns the last layer's material.
- `CoatingCandidate.total_thickness_um` property sums layer thicknesses.

## `mems_vpc/catalog.py`

- Tuples of seeded candidates: `ALLOYS`, `COATINGS`, `CERAMICS`.
- Each entry has literature-priors-only numbers, marked as illustrative.
- `all_combos()` returns the Cartesian product as `Combo` objects.

## `mems_vpc/constraints.py`

- Module-level constants: `MAX_CTE_MISMATCH_PPM = 6.0`, `MIN_HOLE_CLEARANCE_UM = 2.0`,
  `PROBE_BODY_NOMINAL_UM = 30.0`.
- `cte_mismatch(combo) -> float`.
- `hole_clearance_um(combo, probe_body_um=...) -> float`.
- `check(combo, spec) -> list[str]` returns violation strings (empty = feasible).
- `filter_feasible(combos, spec) -> list[Combo]`.

Required rules: CTE mismatch, hole clearance, hole tolerance ≤ 5% pitch, Au-tip on SnAg/Pillar pad.

## `mems_vpc/measurements.py`

- `VirtualLab(noise_scale=0.05, seed=0)`.
- `measure(combo, spec, stage, n_lots=1, lot_idx=0) -> MeasurementRecord` —
  **`lot_idx` MUST be in the RNG hash**; without it PVT replicates are identical and Cpk explodes.
- Tip-material → baseline CRES table; pad-material → multipliers; Archard-style wear;
  anti-stick + hardness drives ΔCRES; Beta-style yield from KPI margins.
- `measure_batch(lab, combos, spec, stage, n_lots=1) -> list[MeasurementRecord]`.

## `mems_vpc/doe.py`

- `full_factorial(alloys, coatings, ceramics) -> list[Combo]`.
- `lhs(n, seed, ...)` via `scipy.stats.qmc.LatinHypercube`.
- `sobol(n, seed, ...)` via `scipy.stats.qmc.Sobol` — round n up to power of 2 for `random_base2`,
  then truncate.
- `dedupe(combos) -> list[Combo]` by `combo.id`.

## `mems_vpc/featurize.py`

- `FEATURE_NAMES` constant for traceability.
- `feature_vector(combo)` and `feature_matrix(list[combos])`.
- `standardize(X, ref=None) -> (X_std, mean, std)` — guards `std=0` with a `1.0` fallback.

## `mems_vpc/bo.py`

- `utility(record, spec) -> float` — scalarised KPI margin (mean of normalised margins).
- Tiny RBF GP with `cho_factor` / `cho_solve`. ~30 lines.
- `expected_improvement(mu, var, y_best, xi=0.01)` using `scipy.stats.norm`.
- `propose(observed, candidates, batch_size, length_scale=1.5) -> list[Combo]`.
  - Cold start (< 2 observed): return head of `candidates` not yet observed.
  - Excludes already-seen combos by `combo.id`.

## `mems_vpc/gates.py`

- `_cpk(values, usl, lsl=None)` — clamp sigma ≥ 1e-9.
- `evaluate_evt(records, spec) -> GateDecision` — needs CRES/CCC/adhesion within spec on ≥ 1 combo.
- `evaluate_dvt` — planarity ≤ spec AND ΔCRES@100k ≤ 30%.
- `evaluate_pvt(records, spec, cpk_target=1.33, min_lots=3)` — Cpk + yield ≥ 99%.
- `evaluate_mp` — any yield < 99% trips HOLD (CAPA).
- `evaluate(stage, records, spec)` dispatcher.

Each rule MUST be a pure function so it can be unit-tested independently and overridden per project.

## `mems_vpc/flow.py`

- `StageLedger` with `add(record)`, `records(stage)`, `combos(stage)`, `all_records()`.
- `StageReport(stage, decision, n_evaluated, n_passing, promoted)`.
- `run_evt(spec, lab, ledger, *, initial_doe=16, bo_rounds=3, bo_batch=4, seed=0)`:
  filter feasible → Sobol seed → BO rounds → gate → top-3 promote.
- `run_dvt(spec, lab, ledger, promoted_ids)`.
- `run_pvt(spec, lab, ledger, locked_id, n_lots=3)` — pass `lot_idx` per call.
- `run_mp(spec, lab, ledger, locked_id, n_lots=6)` — pass `lot_idx` per call.
- `run_full_flow(spec, *, lab=None, seed=0) -> (ledger, list[StageReport])`.

## `tests/`

- `conftest.py` adds `<poc-dir>/` to `sys.path`.
- One file per module. Required assertions:
  - `test_schemas.py`: catalog sizes, unique combo IDs.
  - `test_constraints.py`: CTE rejection (BeCu × AlN), Au-on-SnAg rejection.
  - `test_doe.py`: cardinality, dedupe.
  - `test_measurements.py`: determinism, Sn-pad drift > Al-pad drift on a non-Au tip.
  - `test_gates.py`: PASS/HOLD branches, Cpk monotonicity (tighter spread → higher Cpk).
  - `test_bo.py`: GP shape sanity, propose excludes seen combos.
  - `test_flow.py`: EVT runs and produces records, full flow smokes, promoted carry-forward.

Total target: ≥ 20 tests, runs in < 2 s.

## `examples/run_<slug>_flow.py`

- Adds `<poc-dir>/` to `sys.path` so `python -m examples.run_<slug>_flow` works.
- Builds a `ProbeSpec`, runs `flow.run_full_flow`, prints stage reports + top-5 EVT leaderboard.

## `.gitignore` (repo root, only if missing)

```
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.venv/
venv/
*.egg-info/
.DS_Store
```
