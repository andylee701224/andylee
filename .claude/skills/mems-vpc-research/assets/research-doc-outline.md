# Research Doc Outline — MEMS VPC track

Use this as a section-by-section skeleton when creating `docs/research/<slug>.md`.
Every section is **required**; tables can be reduced if the user explicitly scoped a smaller subset.

---

## 0. Title + sister-doc cross-reference

```markdown
# <slug>: <one-line goal>

> Sister doc: `docs/research/v93k-layout-automation.md` (board-level placement).
> This document covers the probe-card body itself.
```

## 1. Context

3–5 paragraphs, must establish:
- Probe card has three sub-systems: probe (针身), coating (镀层), ceramic guide plate (陶瓷导板).
- Each is a separate research axis with its own physics and process options.
- Their selections are **coupled** (CTE, hardness, hole clearance) — independent optimisation fails.
- Today's manual EVT/DVT/PVT/MP cycle loses cross-stage data; automation goal is closed-loop with shared schema.

## 2. Problem decomposition

Required matrix: three axes × four stages, each cell calls out KPI / decision variable / constraint.

```markdown
| 軸 | 決策變數 | KPI | 製程相依 |
| R1 針身合金 | 合金組成 / 熱處理 / 晶相 | E, σy, CRES, CCC, fatigue, CTE | LIGA / 電鑄 / DRIE |
| R2 探針鍍層 | 種類 / 層厚 / 結構 / 分區 | CRES drift, anti-stick, wear, adhesion | 電鍍 / PVD / ALD |
| R3 陶瓷導板 | 原料 / 成型 / 燒結 / 微孔 | 孔徑公差, Ra, planarity, CTE | HIP / tape cast / 雷射 / USM |

| Stage | 目的 | 退出條件 |
| EVT | 物料候選收斂 | ≥ 1 組合通過 CRES/CCC |
| DVT | 設計驗證 | planarity / 100k drift |
| PVT | 製程驗證 | 3 lot Cpk ≥ 1.33, yield ≥ 99% |
| MP  | 量產 | 月度 SPC + MTBF |
```

## 3. R1 — Probe alloy

Required content:
- Candidate table: NiCo, NiMn, PdCo, BeCu, MP35N (drop / add per scope).
  - Columns: E (GPa), σy (MPa), ρ (µΩ·cm), CTE (ppm/K), main process, notes.
- MEMS process compatibility section: LIGA + electroforming, DRIE+fill, release chemistry, AR limits.
- KPI list mapped to `MeasurementRecord` fields.

## 4. R2 — Coating

Required content:
- Candidate table: Rh, Ru, Pd-Co, Au (soft/hard), Ni barrier, DLC (experimental).
  - Columns: hardness HV, contact-resistance trend, anti-stick, deposition method, role (tip / barrier / base).
- Stack design: tip-vs-base partitioning, layer thickness rationale, micro-structure (nano-crystalline vs columnar), post-bake.
- KPI list with target thresholds (e.g. CRES < 80 mΩ, ΔCRES@100k < 30%).

## 5. R3 — Ceramic guide plate

Required content (this is the section users most often want expanded):
- 5.1 Raw material table: Al2O3, ZrO2-3YTZP, AlN, Si3N4, MACOR, LTCC.
  - Columns: E (GPa), CTE (ppm/K), σ_bend (MPa), micro-hole drilling difficulty, notes.
- 5.2 Forming methods: dry press, isostatic (CIP/HIP), tape casting, slip / gel casting. Match to plate thickness ranges.
- 5.3 Sintering: peak temperature, hold time, shrinkage 15–20% must be regressed in DOE.
- 5.4 Micro-hole drilling table: laser IR / laser UV-fs / USM / micro-drill / µ-ECDM.
  - Columns: min hole, tolerance, wall Ra, throughput, notes.

## 6. System-level coupling

Three explicit couplings (minimum):
- Alloy CTE × ceramic CTE → hard constraint `|Δα| < 6 ppm/K` (override per project).
- Probe body diameter + 2× coating thickness vs hole diameter → minimum clearance.
- Coating tip material × pad material → Sn pickup risk (Au tip on SnAg/Pillar fails).

State that these become `constraints.check()` rules in the POC.

## 7. Measurement schema

Enumerate each KPI that lands in `MeasurementRecord`:
- `cres_mohm`, `delta_cres_pct_at_100k`, `ccc_A`, `planarity_um`, `tip_wear_um3_per_100k`,
  `coating_adhesion_grade`, `yield_pct`, `n_lots`, plus stage / combo_id / notes.

Note that the POC ships `VirtualLab` and the real lab plugs in via the same signature.

## 8. Stage gates (pseudo-rule per stage)

```text
EVT: required = [cres, ccc, adhesion]; pass = ≥ 1 combo within spec
DVT: required = EVT + [planarity, ΔCRES@100k, wear]; pass = planarity < spec AND ΔCRES < 30%
PVT: required = DVT + [yield, n_lots ≥ 3]; pass = Cpk(CRES) ≥ 1.33 AND yield ≥ 99%
MP:  required = monthly yield, MTBF, FA; pass = no SPC OOC; fail trips CAPA
```

## 9. Closed-loop architecture

Include the ASCII pipeline diagram:

```text
Spec → DOE/BO → Lab adapter → MeasurementRecord
                                     ↓
                            Constraints + Stage Gate
                       PASS → promote;  HOLD → BO update
                                     ↓
                                Stage Ledger
```

State explicitly: cross-stage data is preserved; PVT failures feed back into EVT/DVT priors.

## 10. POC scope + roadmap

- Scope: schema, catalog, constraints, VirtualLab, DOE, gates, BO, flow, tests, demo.
- Out of scope: real machine I/O, FEM, real yield models — replaceable via adapter.
- Roadmap: 8 weeks (or shorter) mapped one-per-week to a module.

## 11. Relationship to V93K layout doc

If `docs/research/v93k-layout-automation.md` exists, cross-link and explain the boundary:
- That doc = board-level placement.
- This doc = probe-card body material / process.
- Integration point: shared spec ID + measurement schema.
