# ATE PCB 自動佈排系統架構與演算法框架

本文件詳細說明 V93K ATE PCB 自動佈排系統的五層架構與演算法設計細節。

## 1. 數據萃取層 (Data Extraction Layer)
- **功能**：解析 Netlist、元件尺寸、約束條件。
- **輸入**：Cadence Allegro 導出的 `.def`、`.lef` 或自定義 JSON 格式。
- **輸出**：標準化的內部數據結構（元件列表、網路列表、約束矩陣）。

## 2. 啟發式規則層 (Heuristic Rule Layer)
- **功能**：基於領域知識生成初始佈排，縮減搜索空間。
- **核心規則**：
  1. **主晶片置中**：DUT (Device Under Test) 放置於板中心。
  2. **RF 靠近連接器**：RF 元件優先放置於邊緣連接器附近。
  3. **電源分佈**：去耦電容緊鄰主晶片電源引腳。
  4. **對稱佈排**：差分對元件保持對稱。

## 3. 模擬退火層 (Simulated Annealing Layer)
- **功能**：全域優化，最小化成本函數。
- **成本函數 (Cost Function)**：
  `Cost = W1 * HPWL + W2 * Overlap_Penalty + W3 * RF_Penalty`
  - `HPWL`：半周長線長（Half-Perimeter Wirelength）。
  - `Overlap_Penalty`：元件重疊懲罰（硬性約束）。
  - `RF_Penalty`：RF 訊號過長懲罰。
- **擾動策略**：隨機移動、交換位置、旋轉。

## 4. 機器學習層 (Machine Learning Layer)
- **功能**：毫秒級 SI/PI 品質預測，替代耗時的電磁模擬。
- **模型架構**：卷積神經網路 (CNN)。
- **輸入**：佈排的 2D 影像化表示（多通道：元件、走線、電源層）。
- **輸出**：四項預測指標（SI 評分、PI 評分、熱分佈、可製造性）。

## 5. 強化學習層 (Reinforcement Learning Layer)
- **功能**：學習最優佈排策略，適應不同設計需求。
- **演算法**：Deep Q-Network (DQN)。
- **狀態 (State)**：當前佈排矩陣。
- **動作 (Action)**：選擇元件並放置於網格特定位置。
- **獎勵 (Reward)**：基於 ML 層預測的品質評分與 HPWL 改善量。
