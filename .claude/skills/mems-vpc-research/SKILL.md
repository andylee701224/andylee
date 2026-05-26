---
name: mems-vpc-research
description: Bootstrap a MEMS VPC (vertical probe card) material / coating / ceramic research project with the three-axis (probe alloy × coating × ceramic guide plate) design doc and a runnable EVT→DVT→PVT→MP closed-loop automation POC (DOE + virtual lab + stage gates + Bayesian optimization). Use when the user asks to set up probe-card material research, probe coating studies, ceramic guide-plate selection, or DVT/EVT/PVT/MP process-flow automation for hardware bring-up. Triggers on phrases like "MEMS 探針 / probe card 材料研究", "DVT EVT PVT MP 自動化", "陶瓷導板選型", "探針鍍層研究", "vertical probe card material flow".
---

# MEMS VPC Probe-Card Research & Automation Skill

Sets up two artefacts together:

1. A **controlling research design doc** (`docs/research/<slug>.md`) that frames the probe-card material problem as three coupled axes (R1 probe alloy, R2 coating stack, R3 ceramic guide plate) and four lifecycle stages (EVT, DVT, PVT, MP).
2. A **runnable POC** (`<poc-dir>/`) with: schemas, seeded catalog, cross-axis constraints, virtual measurement lab, DOE (factorial / LHS / Sobol), stage-gate evaluator, RBF-GP + Expected-Improvement BO, end-to-end flow runner, pytest tests, and a CLI demo.

The reference implementation produced by this skill lives at:

- `docs/research/mems-vpc-probe.md`
- `mems_poc/` (module `mems_vpc`)

Treat those as the canonical examples to mirror for new projects.

---

## When to invoke

User intent typically looks like:
- "幫我做 MEMS / VPC 探針卡的材料研究 + 自動化"
- "探針合金 / 鍍層 / 陶瓷導板 選型 + DVT EVT PVT MP 流程自動化"
- "set up a probe-card material research project with closed-loop DOE"

Do NOT invoke for: V93K board-level layout (use the `v93k-layout-automation.md` track), purely chemical / metallurgy questions with no automation component, or generic Bayesian-optimization tutorials.

---

## Workflow

Make a todo list of these steps and work them one at a time. Mark each done immediately.

### 1. Clarify scope (always, even for short prompts)

Before writing any file, use `AskUserQuestion` to confirm at least:

| Header | Question | Why it matters |
|--------|----------|----------------|
| `產出形式` | research doc only / doc + POC skeleton / data model + automation only | Decides which files to create |
| `R1 範圍` | base alloys only / coatings only / both with MEMS process compatibility | Drives `catalog.ALLOYS` / `COATINGS` seed |
| `R3 範圍` | raw material selection / forming / sintering / micro-hole drilling (multi-select) | Drives `catalog.CERAMICS` schema fields |
| `自動化範圍` | input spec only / DOE only / closed-loop with BO + stage gates | Decides whether to scaffold `bo.py` and `flow.py` |

Skip a question only if the user already volunteered the answer.

### 2. Create the research design doc

Use `assets/research-doc-template.md` (in this skill directory) as the structure. The doc MUST have these sections in order:

1. **Context** — why VPC material/process automation matters; cite the three sub-systems (probe, coating, ceramic).
2. **Problem decomposition** — the (R1, R2, R3) × (EVT, DVT, PVT, MP) matrix.
3. **R1 probe alloy** — candidates table + MEMS process compatibility (LIGA, electroforming, DRIE) + KPI list (`pitch_min`, `CCC`, `CRES_initial`, `ΔCRES@100k`, fatigue).
4. **R2 coating** — Rh / Ru / PdCo / Au / DLC table + tip-vs-base partitioning + KPI list.
5. **R3 ceramic** — material table (Al2O3 / ZrO2 / AlN / Si3N4 / MACOR / LTCC), forming, sintering, **and** micro-hole drilling (laser IR / UV-fs / USM / micro-drill / µ-ECDM).
6. **System-level coupling** — CTE alloy↔ceramic, hardness↔pad, hole-clearance↔coating-thickness.
7. **Measurement schema** — define all KPIs that will land in `MeasurementRecord`.
8. **Stage gates** — pseudocode rules for EVT/DVT/PVT/MP entry / required / exit.
9. **Closed-loop architecture** — the DOE → lab → constraints+gate → BO → next-batch diagram.
10. **POC scope + 8-week roadmap** (or shorter, scaled to the user's timeline).
11. **Relationship to V93K layout doc** if present in `docs/research/`.

Write the doc in the user's primary language (Traditional Chinese if the prompt was in zh-Hant, English otherwise).

### 3. Scaffold the POC (only if step 1 said "doc + POC")

Mirror the canonical layout. Each module must exist with the responsibilities below — copy the structure of the reference files, then adapt seed data to the user's project.

```
<poc-dir>/
├── requirements.txt          # numpy, scipy, pytest (no torch unless RL is requested)
├── mems_vpc/
│   ├── __init__.py           # re-export public dataclasses
│   ├── schemas.py            # AlloyCandidate, CoatingCandidate, CeramicSpec,
│   │                         # ProbeSpec, Combo, MeasurementRecord, Stage,
│   │                         # GateDecision, deposition / forming / drilling enums
│   ├── catalog.py            # seeded ALLOYS, COATINGS, CERAMICS + all_combos()
│   ├── constraints.py        # check(combo, spec) -> list[str]; CTE mismatch,
│   │                         # hole clearance, Sn-pickup, deposition compat
│   ├── measurements.py       # VirtualLab.measure(combo, spec, stage,
│   │                         #   n_lots=1, lot_idx=0) -> MeasurementRecord
│   │                         # MUST key its RNG by (combo, stage, lot_idx) so
│   │                         # PVT lots have non-zero variance
│   ├── doe.py                # full_factorial / lhs / sobol / dedupe
│   ├── featurize.py          # combo -> numpy vector + standardize()
│   ├── bo.py                 # tiny RBF GP (cho_factor) + EI + utility() +
│   │                         # propose(observed, candidates, batch_size)
│   ├── gates.py              # evaluate_evt / dvt / pvt / mp + dispatcher
│   └── flow.py               # StageLedger + run_evt / dvt / pvt / mp +
│                             # run_full_flow
├── tests/
│   ├── conftest.py           # adds <poc-dir>/ to sys.path
│   ├── test_schemas.py       # catalog sizes + unique combo IDs
│   ├── test_constraints.py   # CTE / Au-on-SnAg / clearance
│   ├── test_doe.py           # cardinality + dedupe
│   ├── test_measurements.py  # determinism + Sn-pad drift > Al-pad drift
│   ├── test_gates.py         # PASS / HOLD / Cpk monotonicity
│   ├── test_bo.py            # GP shapes + propose excludes seen
│   └── test_flow.py          # EVT runs; full flow smokes; promoted carry-forward
└── examples/
    └── run_<slug>_flow.py    # CLI demo: prints stage reports + top-5 leaderboard
```

### 4. Non-obvious invariants the POC MUST preserve

These are the bugs that will silently break things if you skip them:

- **Lot-indexed RNG**: `VirtualLab._rng_for(combo, stage, lot_idx)` — without `lot_idx` in the hash, PVT replicates are identical and `Cpk` blows up to ~1e10. Tests will pass but the demo will look broken.
- **Combo ID format**: include the ceramic *drilling method* in `Combo.id` (e.g. `NiCo-20|Rh-tip-on-Au|Al2O3-995-laser_ir`) — otherwise the catalog has duplicate IDs because the same ceramic material appears with different drilling methods.
- **Cpk helper guards std=0**: clamp sigma to ≥ 1e-9; if you also display the value, format it sensibly so the user does not see `Cpk=24861333333`.
- **CTE mismatch budget**: keep `MAX_CTE_MISMATCH_PPM = 6.0` unless the user provides a different tolerance — this is what makes the demo feasible-set non-trivial.
- **Sobol needs power-of-2**: `qmc.Sobol.random_base2` requires `n` rounded up; truncate after sampling.
- **Au tip on SnAg/Pillar pads** must be flagged as a constraint violation (Sn pick-up risk). The reference test asserts this.
- **Standardize features** before fitting the GP, or the RBF length-scale becomes meaningless across mixed units (GPa, MPa, µΩ·cm, µm).

### 5. Verify

Run from `<poc-dir>/`:

```bash
python -m pip install -q -r requirements.txt
python -m pytest tests/ -q                    # all tests must pass (~1 s)
python -m examples.run_<slug>_flow            # end-to-end demo
```

The demo should:
- Pass EVT (≥ 1 combo within spec).
- Pass DVT on the EVT-promoted candidates.
- Either pass or HOLD at PVT — both are valid terminal states for the POC.
- Print a top-5 EVT leaderboard sorted by `bo.utility(record, spec)`.

If `Cpk` in the PVT report exceeds ~100, you forgot the `lot_idx` fix in step 4.

### 6. Commit + PR

- Branch convention: `claude/mems-vpc-<slug>-<id>` (or whatever the task description specifies).
- Single commit titled `feat(mems-vpc): research blueprint + POC for <slug>`.
- Body lists the doc + each module created, plus the test count and demo result.
- Open a **draft** PR. Base branch is the repo's working trunk (`claude/v93k-layout-automation-ai-48XMi` in this repo, or `main` elsewhere). Use `mcp__github__create_pull_request` with `draft: true`.
- Add a `.gitignore` if missing (`__pycache__/`, `*.pyc`, `.pytest_cache/`).

### 7. Subscribe to PR activity

After the PR is open, ask the user (proactively, one short sentence) whether to `subscribe_pr_activity` so CI / review events route back to this session.

---

## Customisation knobs

When the user's project differs from the reference, change these — and only these — without touching the rest of the architecture:

| User says | Adjust |
|-----------|--------|
| "我們只關心 ceramic / coating" | Drop the unused axis from `catalog.py`, `constraints.py`, `featurize.py`, but keep `Combo` as a 3-tuple with a sentinel for the dropped axis (so `flow.py` and tests don't fork). |
| "pad is Cu pillar / SnAg" | Pass through `ProbeSpec.pad_material`; the reference `_PAD_FACTOR` table in `measurements.py` already covers Al / Cu / SnAg / Pillar. |
| "pitch is 40 µm" | Tighten `MIN_HOLE_CLEARANCE_UM` and the `hole_tolerance > 5% pitch` rule. |
| "we have real lab data" | Replace `VirtualLab.measure` with an adapter that returns the same `MeasurementRecord`. Do NOT change the `flow.py` orchestration. |
| "want multi-objective Pareto, not scalar utility" | Add `pareto.py` with non-dominated sort; keep `bo.utility` as the scalarisation fallback used by EI. |
| "need RL instead of GP" | Add `rl_env.py` mirroring the V93K POC's Gymnasium env shape (observation = features, action = combo index choice via discrete logits). Keep `flow.py` ignorant of which proposer is used. |

---

## Anti-patterns to avoid

- **Do not** invent fake datasheet numbers without citing them as illustrative seeds in the doc.
- **Do not** add a SQLite / parquet dependency just to persist the ledger — keep it in-memory in the POC; the doc only commits to the *interface*.
- **Do not** scaffold a FastAPI / web UI; the POC is a library + CLI demo.
- **Do not** import `sklearn` for the GP — the hand-rolled RBF GP in `bo.py` is ~30 lines and avoids a heavy dep.
- **Do not** silently expand the catalog to dozens of materials — five per axis is enough to demonstrate the architecture and keeps `full_factorial()` explorable in tests.
- **Do not** put the research doc inside `<poc-dir>/`; it lives under `docs/research/` so it stands alongside other research tracks.

---

## Reference assets

These files in this skill directory document the canonical templates:

- `assets/research-doc-outline.md` — section-by-section skeleton for the design doc with the required tables.
- `assets/poc-checklist.md` — the per-module responsibility checklist mirroring the reference `mems_poc/` layout.

Read both before scaffolding so the new project stays consistent with the existing one.
