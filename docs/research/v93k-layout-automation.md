# V93K 元件佈排自動化（DIB / Load Board + Probe Card）：演算法 × AI 研究藍圖

## Context（為什麼做這件事）

V93000 (Advantest) 是業界主流 SoC 測試平台，每一顆新晶片量產前都需要兩塊高度客製化的高頻 PCB：

- **DIB / Load Board**（FT 用）：將 V93K pin electronics（在 dock 裡的 channel pad）連到 socket，並承載 decoupling、relay、buffer、感測等被動/主動元件。
- **Probe Card / Probe PCB**（CP 用）：把同樣的訊號從 channel pad 連到 needle / MEMS probe，落在 wafer pad 上。

這兩種板都受到相同核心限制：
- **腳位來源固定**：V93K channel landing pad 座標由 Advantest TDC 釋出（DXF），是不可移動的「pin source」。
- **DUT 端腳位也固定**：socket / probe pattern 一旦選定就鎖死。
- **強訊號完整性 (SI) 與電源完整性 (PI) 限制**：高速 DUT 已進入 32–112 Gb/s SerDes、幾百 A 大電流，去耦電容必須貼近 DUT、阻抗連續、回流路徑乾淨。
- **Multi-site 對稱性**：4-/8-/16-site 配置要求高度幾何對稱，否則 site-to-site 一致性會崩。

目前 layout 大量仰賴資深工程師手工在 Cadence Allegro / Mentor Xpedition 內擺放，週期動輒數週。如果能把「元件擺放（placement）」這個最具經驗依賴的步驟用「演算法 + AI」自動化，可顯著縮短 NPI 週期並降低人為差異。本研究以**可行性評估**為目標，盤點現有方法、辨識可遷移到 V93K 場景的關鍵技術、給出 POC 路徑。

---

## 1. 問題分解

把「V93K 元件佈排」拆成三個耦合但可分階段處理的子問題：

| 階段 | 輸出 | 主要決策變數 | 主要約束 |
|------|------|--------------|----------|
| **P1 拓撲映射 (channel mapping)** | channel↔DUT pin 對應表 | 排列 | 訊號群組、長度匹配、layer 配置可行性 |
| **P2 全域佈放 (global placement)** | 每個元件的 (x,y,layer,rotation) | 連續/離散位置 | 不重疊、SI 限制、鏡像對稱、keep-out |
| **P3 細節合法化 (legalization + DRC)** | 通過 DRC 的最終座標 | 微調 | 製程 DRC、via stub、安規 |

> **關鍵洞察**：和 ASIC placement 不一樣，DIB/Probe Card 的 macro 數量僅數百到數千，但「每一顆元件的擺放品質」對 SI/PI 影響極大；因此 V93K 場景的 sweet spot 是 **少量 macro + 強約束 + 高品質要求**，這正好是 RL/GNN 最容易展現價值的設定。

---

## 2. 約束建模（這是 V93K 與一般 PCB 的差異所在）

需要把 V93K 領域知識編碼成可被優化器消化的目標/約束：

- **固定錨點**：V93K channel pad、DUT socket pin、機構孔（dock 介面螺絲）→ hard constraint。
- **群組距離**：去耦電容 ≤ X mm 至 DUT power pin；Kelvin sense 線必須成對等長。
- **長度匹配 (length matching)**：差動對、bus 群組長度差 < spec。
- **Layer transition cost**：via 數成本（影響 SI、可靠度）。
- **Multi-site 對稱**：相同子佈局在不同 site 之間幾何鏡射/旋轉一致。
- **Thermal / mechanical**：handler / prober 機構淨空、socket 散熱通道。
- **Test resource budget**：V93K 不同 PS 卡（PS1600/PS5000/PSDC 等）每 channel 的能力不同，影響哪根 channel 必須對應哪類 DUT pin。

---

## 3. 傳統最佳化演算法（baseline / inner-loop）

這些方法不需要訓練資料，是 POC 階段的基礎，也常被 AI 方法當成 reward / fine-tune 的 inner loop。

- **Simulated Annealing (SA)**：對 macro placement 與 pad alignment 已被驗證有效；DAC 2024「Modern Automatic PCB Placement with Complex Constraints」即用 force-directed + SA legalization。
- **Genetic Algorithm (GA)**：歷史悠久，特別適合處理離散決策（channel mapping、元件分組），如 SOGA。也可與 SA 混合做 analog module placement。
- **Force-directed / Analytical placement**：把 net 視為彈簧、用二次型最佳化做 global placement，速度快、適合作為 RL 環境的 warm-start。
- **Constraint Programming / ILP**：對 channel mapping (P1) 這種離散指派非常合適；可用 OR-Tools / Gurobi 求次優解。

> 建議 baseline：**ILP 解 P1 → 力導向 + SA 解 P2 → constraint-graph legalization 解 P3**。這三步本身就是一個可獨立交付的 POC，AI 在後續層加上去。

---

## 4. AI 方法（以三條路線評估）

### 4.1 GNN（監督式 / 自監督）

- **角色**：把 schematic / netlist 表示為圖，預測「placement 品質」（wirelength、SI heatmap、congestion、DRC violation 機率），作為**評估器** / **代理函數**取代昂貴的 SI 模擬。
- **可遷移文獻**：
  - *CktGNN*（ICLR）：兩層 nested GNN 表示電路拓撲。
  - *Optimization of Analog Circuit Placement: A GNN Approach*（2024）：直接把 GNN 當成 placement 輔助。
  - *GNN4IC*：整理 GNN 在 IC/EDA 的應用。
  - 半導體業界已有用 graph self-supervised learning 做 probe card 維護的研究（ScienceDirect 2025）。
- **優點**：相對於 RL，資料效率高、可解釋；可從歷史成功 board 中學「哪些元件該靠近哪些」。
- **挑戰**：需要可用的歷史 layout 資料庫；DIB 公司通常視為 IP，可能要先在內部資料上 self-supervise。

### 4.2 強化學習（RL，AlphaChip 路線）

- **角色**：把 placement 當序列決策，用 RL agent 一個個放元件，reward 由 SI/PI proxy + wirelength + DRC penalty 組成。
- **可遷移文獻**：
  - Mirhoseini et al., *A graph placement methodology for fast chip design*, Nature 2021（AlphaChip 前身）。
  - DeepMind *AlphaChip* 2024 公開的 pre-trained checkpoint（已用於 TPU）。
  - Vassallo MSc thesis, *Automated PCB Component Placement using RL*（2023）：直接針對 PCB 而非 ASIC。
- **優點**：不需要大量 labeled data；reward 可直接定義為產線關注的指標。
- **挑戰**：訓練成本高、收斂不穩定；AlphaChip 的學術爭議顯示「比 SA 真的好多少」並不必然；對 V93K 這種樣本數少的場景，從零訓練 RL 不划算。
- **務實做法**：用 AlphaChip checkpoint 做 transfer learning，或只在「已被傳統演算法解到次優」的情況下用 RL fine-tune。

### 4.3 LLM / 生成式 AI 輔助

- **角色**：解析 datasheet / spec、自動產生 design rule 檔、把工程師的自然語言意圖（"把 SerDes 群組放靠近 socket 北側"）轉為約束。
- **不取代** geometric placement 求解器，而是**前處理**與**人機介面**。

---

## 5. 推薦架構：Hybrid Pipeline（演算法核心 + AI 輔助）

```
[Spec / Netlist / V93K TDC pad DXF]
        │
        ▼
 (LLM 前處理)         ── 自動抽取群組、約束、對稱要求
        │
        ▼
 P1: ILP/CP channel mapping ── (GNN 預測 mapping 品質作 warm-start)
        │
        ▼
 P2: Force-directed + SA  ── (GNN 取代 SI proxy；可選 RL fine-tune)
        │
        ▼
 P3: Constraint-graph legalization
        │
        ▼
 匯出 Allegro / Xpedition script（.tcl / SKILL）
        │
        ▼
 工程師 review + 局部手動調整 (human-in-the-loop)
```

關鍵原則：**演算法當主幹（可解釋、可重現、不需訓練資料），AI 當加速器與品質評估器**。一旦累積足夠歷史資料，再把 AI 比重往上拉。

---

## 6. 資料與工具生態

- **V93K 端**：Advantest TDC（DUT Board Design Guide、AT93000 Package and Probe PCB DXF/座標）、SmarTest 7/8、TestInsight AMS-VT（pre-silicon load board 驗證）。
- **EDA 端**：Cadence Allegro / Sigrity（SI/PI sim、SKILL 自動化 API）、Mentor Xpedition（HLDRC/DRC API）、KiCad（POC 友好、開源）。
- **演算法庫**：OR-Tools、Gurobi、SciPy SA、DEAP（GA）。
- **AI 框架**：PyTorch Geometric / DGL（GNN）、google-research/circuit_training（AlphaChip 開源版）、Stable-Baselines3（RL baseline）。
- **資料**：CktGNN OCB 資料集（10K op-amp，可作 GNN 預訓練）；內部歷史 DIB / Probe Card 是真正的金礦但需要 IP 授權。

---

## 7. 可行性評估摘要

| 維度 | 評估 |
|------|------|
| 演算法成熟度 | 高（SA/GA/ILP 已多年應用於 PCB） |
| AI 成熟度 | 中（GNN 已有 PCB-level 案例；RL 多在 ASIC，PCB 案例稀少） |
| 資料可得性 | 低～中（內部 DIB layout 屬 IP；公開 ATE-board 資料極少） |
| V93K 領域整合 | 中（TDC 提供座標，但 SmarTest 與 layout tool 之間沒有官方 bridge） |
| 預期 ROI | 高（NPI 週期縮短、site 對稱性自動保證、減少 SI iteration 次數） |
| 主要風險 | (1) 資料不足導致 AI 無法泛化；(2) SI/PI proxy 與真實 sim 落差；(3) 工程師 adoption（黑盒疑慮） |

---

## 8. 建議的 POC 路徑（若進入下一階段）

1. **Week 1–2**：用 KiCad 或合成資料集，搭一個只含「固定 V93K pad + 模擬 DUT socket + 一群去耦電容」的 toy board，跑 ILP+SA baseline，驗證能擺出對稱、合 DRC 的結果。
2. **Week 3–4**：把 baseline 接到一個簡化 SI proxy（HFSS lite 或解析模型），觀察自動化結果與手工 layout 的差距。
3. **Week 5–6**：用 PyG 訓練一個 GNN 預測 wirelength + via 數，取代/加速 P2 的評估函式。
4. **Week 7–8**：嘗試 AlphaChip checkpoint transfer 或 PPO from scratch，對比 RL vs SA。
5. **報告**：以 wirelength、DRC violation、site 對稱誤差、執行時間四個指標跨方法比較。

---

## 9. 主要參考來源（驗證用）

- Advantest, *V93000 DUT Board Design Guide* — https://www3.advantest.com/en/service-support/ic-test-systems/dut-board-design/v93000-dut-board-design-guide
- Mirhoseini et al., *A graph placement methodology for fast chip design*, Nature 2021 — https://www.nature.com/articles/s41586-021-03544-w
- DeepMind, *How AlphaChip transformed computer chip design*（2024 addendum + checkpoint）— https://deepmind.google/blog/how-alphachip-transformed-computer-chip-design/
- google-research/circuit_training（AlphaChip 開源實作）— https://github.com/google-research/circuit_training
- *Late Breaking Results: Modern Automatic PCB Placement with Complex Constraints*, DAC 2024 — https://dl.acm.org/doi/10.1145/3649329.3663495
- *Optimization of Analog Circuit Placement: A GNN Approach*, 2024 — https://dl.acm.org/doi/10.1145/3669754.3669815
- *CktGNN: Circuit GNN for EDA*, ICLR — https://arxiv.org/abs/2308.16406
- Vassallo, *Automated PCB Component Placement using RL*, MSc 2023 — https://www.lukevassallo.com/wp-content/uploads/2023/09/automated_pcb_component_placement_using_rl_msc_thesis_v2_1_lv.pdf
- *Semiconductor probe card proactive maintenance using graph self-supervised learning*, ScienceDirect 2025 — https://www.sciencedirect.com/science/article/abs/pii/S0360835225001019
- DfX-NYUAD/GNN4IC（GNN×IC 論文清單）— https://github.com/DfX-NYUAD/GNN4IC

---

## Verification（如何驗收這份研究）

由於本任務是「純研究 / 可行性評估」，驗收標準為：

- 本份計畫文件涵蓋 (a) 問題分解 (b) 約束建模 (c) 傳統演算法 (d) AI 方法 (e) 整合架構 (f) 資料/工具盤點 (g) 風險與 ROI (h) POC 路徑 — 已完成。
- 列出之參考來源可被 user 點擊驗證 — 已附 URL。
- 後續若進入 POC：依 §8 路徑執行，產出可量測的 baseline metrics。
