# MEMS VPC 探針卡材料/鍍層/陶瓷導板自動化研究藍圖

> Sister doc：`docs/research/v93k-layout-automation.md`（V93K 板級佈排）。本文聚焦在**探針卡本身**的材料體系與陶瓷導板，串接 EVT → DVT → PVT → MP 的閉環實驗自動化。

## Context（為什麼做這件事）

Vertical Probe Card（VPC）是先進製程 wafer test 的主流形式。一張 VPC 由三層主要次系統構成：

1. **探針（針身）**：成千上萬根 MEMS 製程做出的細長彈性導體。針身需同時滿足彈性接觸力、低接觸電阻 (CRES)、高載流 (CCC)、抗疲勞、與晶圓 pad（Al / Cu / Sn-Ag / Pillar）長壽命匹配。
2. **探針鍍層**：在針尖與針身選擇性鍍上 Rh / Ru / Pd-Co / Au / Ni 等金屬層，控制接觸電阻穩定性、抗黏附（Sn / Solder pick-up）、抗氧化、抗磨耗。
3. **陶瓷導板（guide plate / die）**：上下兩片高精度陶瓷板，板上以 ~µm 級孔位精度導引每根探針，決定整張卡的對位、planarity、與 over-travel 壽命。

這三個次系統的物理選型彼此耦合：

- 針身的**楊氏模數 / 降伏強度**決定 over-travel × pitch 的可行域；
- 鍍層的**硬度 / 接觸電阻**決定 CRES 與抗黏附；
- 陶瓷導板的**CTE / 孔徑公差 / 孔壁粗糙度**決定針身能不能在熱循環下保持對位、以及針身磨耗速率。

業界目前的開發流程在 EVT/DVT/PVT/MP 四個階段都仰賴人工 DOE 與經驗判斷，跨階段的資料是斷裂的。本研究的目標：

- **產出 1**：一份可被工程團隊直接引用的選材矩陣（針身合金 × 鍍層 × 陶瓷原料 × 製程方法），明確列出每個候選的指標與排除條件。
- **產出 2**：一個可重現的自動化 POC，定義輸入規格 → 自動生成 DOE → 收集量測 → 跑閉環貝氏最佳化 → 自動產生下一輪實驗或進行 stage gate 判定。

---

## 1. 問題分解（三軸 × 四階段）

把「VPC 物料與製程開發」拆成三條互相耦合的研究軸：

| 軸 | 主要決策變數 | 關鍵 KPI | 製程相依 |
|----|--------------|----------|----------|
| **R1 針身合金** | 合金組成、熱處理、晶相 | 楊氏模數 E、降伏 σy、CRES baseline、CCC、疲勞 N、CTE | LIGA / 電鑄 / DRIE 適配性 |
| **R2 探針鍍層** | 鍍層種類、層厚、結晶結構、針尖 vs 針身分區 | 接觸電阻穩定性、抗黏附、抗氧化、磨耗壽命 | 電鍍/PVD/ALD 適配性、與合金附著力 |
| **R3 陶瓷導板** | 原料、成型法、燒結曲線、微孔加工方法 | 孔徑公差、孔壁粗糙度、平面度、CTE 與合金匹配 | 雷射/超音波/微銑 與 HIP/HPSN |

並沿四個 stage 推進：

| Stage | 目的 | 輸入 | 退出條件（gate） |
|-------|------|------|------------------|
| **EVT** Engineering | 物料候選收斂 | 規格表 + 候選清單 | 至少 1 組合通過 CRES/CCC bench 篩 |
| **DVT** Design | 設計驗證 | EVT 收斂的 1–3 組合 | 全卡 planarity / over-travel / 100k touchdown 通過 |
| **PVT** Production | 製程驗證 | DVT 通過的 1 組合 | 連續 3 lot × Cpk ≥ 1.33 |
| **MP** Mass Production | 量產 | PVT lock 的 BOM + recipe | 月度 yield / MTBF 監控，trigger CAPA |

> **關鍵洞察**：和 IC 設計不同，物料/製程開發的成本主要在「跑一輪實驗」，因此自動化的價值不在 CPU，而在於**每一輪 DOE 都用上一輪所有量測資料**——這正是貝氏最佳化（BO）+ stage gate 自動化的 sweet spot。

---

## 2. R1：MEMS 探針合金選材 × 製程適配

### 2.1 候選合金（合金 × 製程適配矩陣）

| 合金族 | E (GPa) | σy (MPa) | ρ (µΩ·cm) | 主製程 | 備註 |
|--------|---------|----------|-----------|--------|------|
| **NiCo (e.g. Ni-20Co)** | ~210 | 1500–2200 | 15–25 | LIGA 電鑄 | 業界主流，疲勞表現佳，CCC 中等 |
| **NiMn / NiW** | ~200 | 1800–2400 | 25–40 | 電鑄 | 高強度，但電阻高，需厚鍍 Au |
| **Pd / Pd-Co / Pd-Ni** | ~120 | 800–1400 | 10–15 | 電鑄 | 高貴金屬，抗氧化佳，常見於針尖 |
| **BeCu (C17200)** | ~130 | 1100–1400 | 7 | 機械加工 / 線切 | 傳統 cantilever / vertical 早期方案，含 Be 環保壓力 |
| **MP35N / NiCoCrMo** | ~230 | 2000 | 100 | 線切 / 機械 | 高疲勞，但 CCC 差，pitch 受限 |
| **Rh / Pt 複合針尖** | — | — | — | PVD/CVD 局部 | 通常作為鍍層而非結構 |

> **R1 評估指標 (EVT 篩選用)**：
> - `pitch_min` 可達 → 由 σy / E 與 AR 推估
> - `CCC` @ 自身溫升 ΔT < 40°C
> - `CRES_initial` 與 100k touchdown 後 `ΔCRES / CRES_initial`
> - 在 –40°C / 25°C / 150°C 三點的彈性常數漂移
> - 與目標 pad 材質（Al / Cu / Sn-Ag）100k 接觸後針尖磨損體積

### 2.2 MEMS 製程適配性（必須與材料一起評估）

R1 的「材料候選」不能脫離製程獨立看，這是和傳統機械加工最大的差別：

- **LIGA + 電鑄**：候選必須能在水溶液鍍浴中析出（Ni / Co / Mn / W 合金 OK；Pd 也可；Rh 較難厚鍍）。研究維度：浴液配方、電流密度波形（DC vs pulse vs pulse-reverse）、應力控制、晶粒尺寸。
- **DRIE + 填料**：候選需與 deep silicon trench 相容，後段以電鑄填充。Mn 系合金易與 SiO2 mask 反應，需評估。
- **XeF2 / wet release**：候選必須耐 release 化學品。
- **Mask 對齊 / AR (aspect ratio)**：合金的鍍層應力上限決定能做到多高 AR；高應力會導致 release 後彎曲。

> **R1 輸出 schema**（會落到 `mems_vpc.materials.AlloyCandidate`）：
> `name, composition, E_GPa, sigma_y_MPa, rho_uohm_cm, cte_ppm_per_K, fatigue_N_at_1pct_strain, deposition_method, deposition_window`。

---

## 3. R2：探針鍍層研究

### 3.1 候選鍍層

| 鍍層 | 硬度 HV | 接觸電阻趨勢 | 抗黏附 | 適配製程 | 常見定位 |
|------|---------|--------------|--------|----------|----------|
| **Rh** | 800–1000 | 穩定，氧化薄、可導電 | 對 Sn-Ag 中等 | 電鍍（薄）、PVD | 針尖首選 |
| **Ru** | 800–1200 | 穩定 | 對 Sn-Ag 佳 | 電鍍困難，多 PVD/ALD | Rh 替代品 |
| **Pd-Co** | 500–700 | 良好，需 Au flash | 中等 | 電鍍 | 針身延伸層 |
| **Au (soft / hard)** | 60 / 200 | 極低但易黏 Sn | 差 | 電鍍 | 過渡層 / 針身 |
| **Ni 阻擋層** | 300 | n/a | n/a | 電鍍 | 防止 Cu / Pd 互擴散 |
| **DLC / TiN (實驗性)** | >2000 | 半導體性，需設計 | 佳 | PVD | 研究中 |

### 3.2 鍍層設計變數

- **針尖 vs 針身分區鍍**：典型結構為「針身 NiCo + Au 過渡層 + 針尖 Rh tip」。研究維度：分區 mask 方式、邊界處沒附著風險。
- **層厚分佈**：Rh 太厚易剝落；太薄則磨穿。常見 0.3–1.5 µm。
- **微結構**：nano-crystalline vs columnar 對磨耗壽命差異 >3×。
- **熱處理**：post-plating bake 200–400°C 影響晶粒長大與內應力。

### 3.3 R2 KPI

| KPI | 量測方法 | EVT 通過值（example） |
|-----|----------|----------------------|
| `CRES_initial` (mΩ) | 4-point @ 5 gf | < 80 |
| `ΔCRES @ 100k TD` | benchmark cycle | < +30% |
| `Sn-pickup mass / 1k TD` | EDS / weight | < threshold |
| 針尖磨損體積 / 100k TD | confocal | < x µm³ |
| 鍍層附著力 (剝離) | scratch | grade ≥ HF1 |

> **R2 輸出 schema**：`CoatingCandidate(name, layers=[(material, thickness_um)], hardness_HV, deposition_method, deposition_window)`，並有 `composite_score()` 把上述 KPI 加權成單值給 BO。

---

## 4. R3：陶瓷導板原料 × 製程 × 微孔加工

陶瓷導板是 VPC 對位精度的根源。研究分四層：

### 4.1 原料選型

| 材料 | E (GPa) | CTE (ppm/K) | σ_bend (MPa) | 微孔加工難度 | 備註 |
|------|---------|-------------|--------------|---------------|------|
| **Al2O3 (99.5)** | 380 | 7.5 | 350 | 中（雷射/超音波） | 業界基線，便宜，CTE 偏高 |
| **ZrO2 (3Y-TZP)** | 210 | 10 | 1200 | 中 | 高韌性，孔壁不易崩 |
| **AlN** | 320 | 4.5 | 350 | 中（CTE 與 Si 接近） | 適合需要 wafer-CTE 匹配 |
| **MACOR (machinable)** | 67 | 9.3 | 94 | 易（傳統機械） | 強度低，prototype only |
| **LTCC** | 110 | 5.8 | 320 | 易（生坯打孔） | 多層整合佳 |
| **Si3N4** | 310 | 3.2 | 700 | 難 | 高強度高熱導，成本高 |

R3 的決策變數要納入 R1：針身合金 CTE 必須與陶瓷 CTE 配對，否則熱循環下會有 cumulative drift（典型容忍 |Δα| < 3 ppm/K）。

### 4.2 成型法

- **乾壓**：適合厚板（>1 mm）、產量高，但密度梯度大。
- **等靜壓 (CIP / HIP)**：密度均勻，孔徑加工後孔壁更光滑。
- **Tape casting**：適合 < 0.5 mm 薄板 / LTCC 多層；料漿配方（黏結劑、塑化劑、溶劑）是研究核心。
- **Slip casting / Gel casting**：複雜形狀。

### 4.3 燒結 / 製程

- 燒結曲線：升溫率、最高溫、保溫時間直接決定收縮率 (typical 15–20%) 與最終孔徑。**收縮率必須在 DOE 中迴歸建模**——這是孔位精度的最大誤差源。
- HIP / 後 HIP：消除閉孔，提升強度。
- 退火：釋放微銑/雷射後的殘餘應力。

### 4.4 微孔加工

孔徑公差直接決定整張 VPC 的 alignment budget。

| 方法 | 最小孔徑 | 公差 | 孔壁粗糙度 Ra | 速率 | 備註 |
|------|----------|------|----------------|------|------|
| **Nd:YAG / fiber 雷射** | 30 µm | ±5 µm | 1–3 µm | 快 | 熱影響區、taper |
| **UV / fs 雷射** | 15 µm | ±2 µm | <0.5 µm | 中 | 冷加工，但慢且貴 |
| **超音波 (USM)** | 50 µm | ±3 µm | 0.5–1 µm | 慢 | 適合脆性陶瓷 |
| **微鑽 / 微銑** | 80 µm | ±5 µm | 2 µm | 慢 | 工具磨損嚴重 |
| **電化學放電 (µ-ECDM)** | 50 µm | ±5 µm | 1 µm | 慢 | 實驗性 |

> **R3 輸出 schema**：`CeramicSpec(material, forming, sinter_profile, drilling_method, hole_diameter_um, hole_tolerance_um, hole_wall_Ra_um, plate_thickness_mm, plate_warp_um)`。

---

## 5. 系統級耦合（這三軸不能獨立優化）

| 耦合 | 物理 | 自動化怎麼處理 |
|------|------|---------------|
| 合金 CTE × 陶瓷 CTE | 熱循環 drift | 在 DOE 加入 `cte_mismatch_ppm` 作為硬約束 |
| 合金強度 × 孔徑公差 | over-travel 下針身不該卡死孔壁 | 從 (E, σy, 孔徑公差) 算出可行 over-travel range |
| 鍍層厚度 × 孔徑 | 鍍後直徑 = 針身 + 2 × 鍍層；可能磨擦孔壁 | 從 BOM 自動推算干涉風險 |
| 鍍層硬度 × pad 硬度 | 太硬刮 Al pad、太軟壽命短 | 對應的 pad-material profile 內建到 KPI 模型 |

這些耦合會在 `mems_vpc.constraints` 內以可呼叫的 `check(combo) -> list[Violation]` 表達。

---

## 6. 量測指標（Measurement / KPI 統一定義）

所有 stage 共用同一套量測 schema（`MeasurementRecord`），由 fixture 自動寫入：

- **CRES**: mΩ, 4-point, 規定接觸力與電流。
- **CCC**: A, 自身溫升 ΔT ≤ 40°C 的最大持續電流。
- **Planarity**: µm, 全卡所有針尖 z-座標 max − min。
- **Force-displacement curve**: 接觸力 vs over-travel。
- **Touchdown lifetime**: 在指定 pad 上 cycle 至 ΔCRES > 30% 的次數。
- **Yield / FA (failure analysis)**: per-lot、per-fixture。

`mems_vpc.measurements.VirtualLab` 在 POC 中以解析模型 + 雜訊模擬這些量測，讓自動化閉環可在沒有實體 fixture 時跑出可重現的數字。實體導入時把 `VirtualLab` 換成 `RealLab` adapter 即可。

---

## 7. Stage Gate 自動化

每個 stage 由三件事定義：

1. **進入條件 (entry criteria)**：哪些上一階段欄位必須存在。
2. **必收量測 (required measurements)**：list[KPI]。
3. **退出規則 (exit rule)**：一個 `pure function (records) -> {PASS, HOLD, FAIL}`。

EVT/DVT/PVT/MP 各自的 default rule（可被專案覆寫）：

```text
EVT:
  required = [CRES_initial, CCC, alloy_E_match, coating_adhesion]
  rule = all(KPI within spec) AND n_candidates >= 1
DVT:
  required = EVT + [planarity, over_travel_curve, 100k_touchdown]
  rule = planarity < 25 µm AND ΔCRES@100k < 30%
PVT:
  required = DVT + [yield_per_lot, lot_to_lot_variation]
  rule = Cpk(CRES) >= 1.33 AND yield >= 99% over 3 consecutive lots
MP:
  required = monthly yield, MTBF, FA list
  rule = no SPC OOC for 30 days; else trigger CAPA
```

`mems_vpc.gates.evaluate(stage, records) -> GateDecision` 是純函式，便於單元測試。

---

## 8. 閉環自動化架構

```text
  ┌────────────────┐
  │ Spec / Inputs  │   (pitch, pad material, max_force, target lifetime…)
  └───────┬────────┘
          ▼
  ┌────────────────┐    生成下一輪 N 個 candidate (combo)
  │ DOE / BO Layer │ ◄────────────────────────────────────────┐
  └───────┬────────┘                                          │
          ▼                                                   │
  ┌────────────────┐    模擬 / 真實量測                       │
  │ Lab Adapter    │ ──► MeasurementRecord                    │
  └───────┬────────┘                                          │
          ▼                                                   │
  ┌────────────────┐                                          │
  │ Constraints +  │                                          │
  │ Stage Gate     │ ──► GateDecision                         │
  └───────┬────────┘                                          │
          │ HOLD → 給 BO 更新先驗 ───────────────────────────┘
          │ PASS → promote 到下一階段
          ▼
  ┌────────────────┐
  │ Stage Ledger   │   (parquet / sqlite，跨 stage 共享所有 record)
  └────────────────┘
```

重點：
- **跨 stage 不丟資料**：EVT 篩出的 candidate 在 DVT 還在用，DVT 的失效資料反饋給 EVT BO 的先驗。
- **BO 多目標**：以 Pareto front 同時推 CRES、CCC、lifetime、cost 而非單值。POC 用 EHVI / qParEGO 風格的 acquisition。
- **可解釋性**：每一個 candidate 必須能 trace 到 (合金, 鍍層, 陶瓷) 三軸的具體 ID，方便工程師打斷自動化、做手工 override。

---

## 9. POC 範圍與不在範圍

POC（`mems_poc/`）做：

- 三軸 schema + 真實業界候選清單初始 catalog。
- DOE 生成器：full factorial、Latin hypercube、Sobol。
- `VirtualLab`：以解析模型把 (合金, 鍍層, 陶瓷) 映射到 CRES / CCC / planarity / lifetime，含可調雜訊。
- Constraint checker：CTE mismatch、孔徑干涉、製程適配。
- Stage gate evaluator（EVT/DVT/PVT/MP 各一條 default rule）。
- 簡單 BO（GP + EI / Thompson）跑閉環，能在 < 30 s 收斂 EVT 階段。
- End-to-end demo：給定一份 spec，跑完 EVT → DVT → PVT 三輪，輸出 ledger。

POC **不做**：

- 真實電鍍/雷射機台的 I/O 介接（保留 adapter 介面）。
- 物理級 FEM（針身 buckling、ANSYS 接力）——以解析近似代替。
- 真實 yield 模型（用 Beta 分布近似）。

---

## 10. 8-週 Roadmap

| 週 | 交付 | 對應模組 |
|----|------|----------|
| 1 | Schema + materials/coatings/ceramics catalog seed | `schemas.py`, `materials.py`, `coatings.py`, `ceramics.py` |
| 2 | Constraint checker + VirtualLab v0 | `constraints.py`, `measurements.py` |
| 3 | DOE 生成 (factorial / LHS / Sobol) + tests | `doe.py` |
| 4 | EVT/DVT/PVT/MP gate evaluator + tests | `gates.py` |
| 5 | 簡單 BO（GP + EI）+ Pareto 工具 | `bo.py`, `pareto.py` |
| 6 | Stage runner / ledger | `flow.py`, `ledger.py` |
| 7 | End-to-end example + 可視化 | `examples/run_mems_flow.py` |
| 8 | 文件、API freeze、與真實 lab adapter 介面定稿 | `docs/`, `adapters/` |

---

## 11. 與 V93K layout 研究的關係

- `v93k-layout-automation.md` 解決**板級**問題（DIB / probe PCB 上的元件放在哪）。
- 本文解決**探針卡本體**問題（針身 / 鍍層 / 陶瓷導板選什麼、怎麼做、量什麼、什麼時候 promote）。
- 兩者最終整合：本研究的 `MeasurementRecord` 與 V93K POC 的 `Board` 透過共用的 spec ID 串接，讓「板級佈線最佳化」可以以「目前 probe 設計鎖定的 over-travel / CCC / planarity」為輸入。
