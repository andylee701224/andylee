# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository scope

This repo holds a research plan plus a working POC for **V93000 (Advantest) DIB / Probe Card component placement automation**:

- `docs/research/v93k-layout-automation.md` — the controlling design document. It defines the three-stage problem split (P1 channel mapping → P2 global placement → P3 legalisation) and the 8-week POC roadmap. Read this **before** changing the POC.
- `poc/` — Week 1–2 deliverable: a Python implementation of the algorithmic baseline (CP-SAT + SA + iterative legalisation) on a synthetic two-site V93K-style toy board. Future AI work (GNN evaluator, RL fine-tuner) should plug into this same data model.

## Commands

Run from `poc/`:

```bash
pip install -r requirements.txt          # numpy, scipy, matplotlib, ortools, pytest, gymnasium, sb3
python -m pytest tests/                  # all tests (~5s; one CP-SAT test ~10s budget)
python -m pytest tests/test_pipeline.py::test_sa_then_legalize_reduces_distance_and_clears_drc -v
python -m examples.run_poc               # end-to-end demo, writes PNGs to poc/artifacts/
python -m examples.compare_sa_rl         # train PPO + 10-seed SA vs RL benchmark (~90 s)
```

`run_poc.py` and `tests/conftest.py` both inject `poc/` onto `sys.path`, so `v93k_poc` imports work without installing the package. There is no `pyproject.toml`.

## Architecture

The POC pipeline operates on a single mutable `Board` (`v93k_poc/board.py`) holding:

- `anchors`: fixed pins (V93K channel pads + DUT socket pins). Never moved.
- `components`: placeable bodies (decoupling caps). Have `(x, y, rotation)`.
- `keepouts`: forbidden axis-aligned rectangles (socket bodies).
- `site_centers`: dict `{site_idx: (cx, cy)}` used by the symmetry term.

### Three-stage pipeline

1. **P1 — `p1_mapping.solve_channel_mapping`** : assignment problem in CP-SAT. Each V93K channel is matched to a socket pin of the **same `SignalType`**; objective is sum of Manhattan distances. Returns `{channel_id: pin_id}` plus the integer-scaled cost. Only HIGH_SPEED / LOW_SPEED pins participate; VDD/GND go to P2.
2. **P2 — `p2_placement.simulated_annealing`** : SA on cap positions. Energy is a weighted sum of (a) cap→target-VDD distance, (b) cap-cap overlap area, (c) cap-keepout overlap area, (d) **mirror-symmetry penalty across sites**, (e) out-of-bounds. Two move types: 70% single-component perturbation, 30% **paired symmetric move** that updates a logical pair across sites with mirrored Δx — this is what lets symmetry actually converge instead of fighting the wirelength term.
3. **P3 — `p3_legalize.legalize`** : *iterated* push-out-of-keepouts → push-apart → snap-to-grid, repeated up to 5 times. The iteration matters: snap-to-grid can re-introduce overlaps that a single linear pass leaves behind, so it re-checks DRC after each pass.

### Two non-obvious invariants

- **`Component.logical_index`** pairs site-0 and site-1 components that should be mirrored. `synthetic.make_toy_board` increments `pair_idx` once per logical pair and assigns it to **both** the site-0 and site-1 cap created in lockstep. The symmetry penalty (in `p2_placement` and `metrics.site_symmetry_error`) groups by this index. If you add new components, you must assign matching `logical_index` values across sites or symmetry scoring will silently drop them.
- **Cap initial offsets must push *away* from the socket centre.** In `synthetic.py`, `offset_y = -1.0 if rr == 0 else 1.0` exists because the synthetic socket places `r=0` at `cy - 2.5` (south edge); flipping the sign puts caps *inside* the keepout. `tests/test_metrics.py::test_drc_initially_clean` guards against this regression.

### RL extension

`v93k_poc/rl_env.py` exposes `V93KPlacementEnv` (Gymnasium-compatible). Observation = per-cap (own xy, target VDD xy, nearest-keepout dx/dy) normalised by board half-extent; action = per-cap continuous Δ(x, y) in [-1, 1] scaled by `step_mm`. Reward is `(E_prev - E_new) / E_init` using the **same** energy function as P2 SA, so RL and SA are directly comparable. `examples/compare_sa_rl.py` trains PPO (~80 s on CPU) and benchmarks both methods on 10 random seeds. Reference run shows SA dominates (E≈13 vs ≈190, sym 0.03 mm vs 10 mm) — expected, since the problem only has 16 free dimensions and SA is cheap. The harness exists so future GNN-evaluator or AlphaChip-checkpoint experiments can be slotted in cleanly.

### Test layout

- `test_synthetic.py` — anchor/component counts, signal-type split, board geometry.
- `test_metrics.py` — invariants on the factory layout (DRC-clean, symmetric).
- `test_p1_mapping.py` — CP-SAT returns a valid one-to-one matching with signal-type compatibility.
- `test_pipeline.py` — full random-init → SA → legalise smoke test; asserts post-legalise DRC=0, max cap-VDD < 6 mm, symmetry < 4 mm. Use this as the integration check after any algorithm tweak.
- `test_rl_env.py` — observation/action shapes, zero-action no-op invariant, `max_steps` truncation contract. Does **not** train PPO — keep training out of the test suite.

## Branch / PR conventions

Default branch is `claude/v93k-layout-automation-ai-48XMi` (this is intentional — the repo has no `main`). Develop further work on the same branch unless splitting out a sub-feature.
