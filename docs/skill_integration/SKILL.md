---
name: ate-pcb-auto-placement
description: 專為 Advantest V93K 等高端 ATE 測試卡設計的訊號用元件自動佈排系統開發與部署指南。當使用者需要進行 ATE PCB 的自動化佈排研究、架構設計、演算法開發（啟發式、SA、ML、RL）、Cadence Allegro 整合、PoC 驗證、生成相關技術文檔與投影片，或需要將 ATE/EDA 技術內容轉成高品質前端介面、HTML 簡報、互動展示頁與反 AI slop 視覺輸出時，請觸發此技能。
---

# ATE PCB 自動佈排系統開發指南

本技能提供了一套完整的標準作業流程 (SOP)，用於開發與部署針對高端 ATE 測試卡（如 Advantest V93K 60層板）的訊號用元件自動佈排系統。

## 核心價值與應用場景

本技能旨在解決 ATE PCB 設計中高度複雜的訊號完整性 (SI) 與電源完整性 (PI) 挑戰，透過 AI 驅動的混合演算法，將設計週期從數週縮短至數天，並顯著提升佈排品質。

本版本已整合 **Taste Skill** 作為前端與視覺輸出品質模組。當任務涉及 HTML 簡報、互動展示頁、dashboard、PoC demo UI、技術報告網頁化或任何需要避免 generic AI slop 的介面設計時，請讀取 `references/frontend_taste_skill.md`，並將其規則套用於版面、字體、色彩、動效、響應式結構與輸出完整性檢查。

**適用場景**：
1. **研究與架構設計**：建立多層次演算法框架（啟發式規則 → 模擬退火 → 機器學習 → 強化學習）。
2. **代碼開發與整合**：實作佈排演算法並與 Cadence Allegro 無縫整合（SKILL 腳本與 DEF 檔案）。
3. **驗證與文檔生成**：執行 PoC 測試，並自動生成專業的技術報告、演算法說明與簡報。
4. **高品質視覺與前端輸出**：當 ATE/EDA 成果需要轉成 HTML 簡報、互動展示頁、dashboard 或產品化 demo 時，啟用 Taste Skill 模組，降低模板化、紫色漸層、卡片堆疊、低對比與過度通用化 UI 的風險。

## 系統架構與演算法框架

本系統採用五層獨立模組架構，詳見 `references/architecture_framework.md`：
1. **數據萃取層**：解析 Netlist 與元件尺寸。
2. **啟發式規則層**：基於領域知識的初始佈排（如主晶片置中、RF 靠近連接器）。
3. **模擬退火層 (SA)**：最小化 HPWL 與消除重疊。
4. **機器學習層 (ML)**：使用 CNN 進行毫秒級 SI/PI 品質預測。
5. **強化學習層 (RL)**：使用 DQN 學習最優佈排策略。

## 執行工作流程

當使用者要求執行 ATE PCB 自動佈排相關任務時，請依序執行以下步驟：

### 步驟 1：需求確認與參數設定
- 確認目標 PCB 規格（如層數、尺寸、訊號類型）。
- 讀取 `references/signal_priority_rules.md` 了解不同訊號（RF、HSIO、時鐘、GPIO、電源）的佈排優先級與權重。

### 步驟 2：代碼生成與整合
- 根據需求，使用 `scripts/` 目錄下的模板生成對應的 Python 代碼。
- 確保代碼包含 Cadence Allegro 整合層（生成 `.il` 與 `.def` 檔案）。
- 參考 `references/allegro_integration_guide.md` 確保輸出格式正確。

### 步驟 3：PoC 驗證與測試
- 執行整合測試，驗證演算法的收斂性與佈排品質。
- 記錄關鍵指標：成本降低率、HPWL 改善、SI 評分提升、執行時間。

### 步驟 4：文檔、簡報與前端視覺輸出
- 使用 `templates/` 目錄下的模板生成技術報告與演算法說明。
- 若使用者需要簡報，請參考 `templates/slides_structure.md` 的大綱，生成專業投影片。
- 若輸出形式為 HTML 簡報、互動展示頁、dashboard、React/Next.js UI 或前端 demo，必須先讀取 `references/frontend_taste_skill.md`，並依據該模組進行設計品味校正、反 AI slop 檢查、響應式布局與最終 pre-flight review。

## 參考資源與模板

本技能包含以下資源，請根據任務需求讀取：

- **參考文檔 (`references/`)**：
  - `architecture_framework.md`：系統架構與演算法設計細節。
  - `signal_priority_rules.md`：訊號分類、權重與佈排策略。
  - `allegro_integration_guide.md`：Cadence Allegro 整合規範。
  - `frontend_taste_skill.md`：Taste Skill 前端設計品質模組，用於 HTML 簡報、互動展示頁、dashboard、前端 demo、UI polish 與反 AI slop 檢查。

- **模板檔案 (`templates/`)**：
  - `slides_structure.md`：標準的 14 頁技術簡報大綱與設計規範。
  - `report_template.md`：技術報告與演算法說明模板。

- **腳本範例 (`scripts/`)**：
  - `poc_runner_template.py`：PoC 整合測試框架範例。

## 最佳實踐與注意事項

1. **訊號優先級**：永遠確保 RF 與 HSIO 訊號（權重 3.0x）優先佈排，其次是時鐘（2.0x），最後是 GPIO 與電源。
2. **搜索空間縮減**：採用「元件中心策略」，固定主要晶片，被動元件圍繞其佈排，可縮減 90% 搜索空間。
3. **多目標優化**：成本函數必須同時考慮 HPWL、元件重疊（硬性約束）與 RF 懲罰。
4. **文檔品質**：所有生成的文檔與簡報必須保持高度專業性，使用量化數據支持結論。
5. **視覺輸出品質**：若生成任何前端或 HTML 視覺成果，必須套用 Taste Skill 模組，先確認 typography、spacing、color、motion、responsive behavior、component architecture 與 accessibility，再交付最終版本。
