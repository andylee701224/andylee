# Cadence Allegro 整合指南

本文件說明如何將 Python 自動佈排系統與 Cadence Allegro EDA 工具無縫整合。

## 整合架構

系統採用雙向資料流架構：
1. **Allegro → Python**：透過 SKILL 腳本導出元件座標、網路列表與約束條件。
2. **Python → Allegro**：透過生成 SKILL 腳本 (`.il`) 或 DEF 檔案 (`.def`) 將優化後的佈排結果匯入 Allegro。

## 1. 導出資料 (Allegro to Python)

在 Allegro 命令列中執行以下 SKILL 腳本，將當前設計導出為 JSON 格式：

```skill
; export_design_data.il
defun export_design_data ()
  let((out_port comp_list net_list)
    out_port = outfile("design_data.json")
    fprintf(out_port "{\n  \"components\": [\n")
    
    ; 遍歷所有元件
    comp_list = axlDBGetDesign()->components
    foreach(comp comp_list
      fprintf(out_port "    {\"name\": \"%s\", \"x\": %f, \"y\": %f, \"rotation\": %f},\n" 
              comp->name comp->xy[0] comp->xy[1] comp->rotation)
    )
    
    fprintf(out_port "  ]\n}\n")
    close(out_port)
  )
)
```

## 2. 匯入佈排結果 (Python to Allegro)

Python 系統優化完成後，會生成一個包含所有元件新座標的 SKILL 腳本。

### 2.1 生成 SKILL 腳本

Python 模組 `allegro_interface.py` 負責生成以下格式的 `.il` 檔案：

```skill
; apply_placement.il
defun apply_placement ()
  let((comp)
    ; 移動元件 U1
    comp = car(axlSelectByName("COMPONENT" "U1"))
    if(comp then
      axlTransformObject(comp ?move '(100.0 200.0) ?angle 90.0)
    )
    
    ; 移動元件 C1
    comp = car(axlSelectByName("COMPONENT" "C1"))
    if(comp then
      axlTransformObject(comp ?move '(150.0 250.0) ?angle 0.0)
    )
    
    axlClearSelSet()
    axlUIConfirm("自動佈排已完成！")
  )
)
```

### 2.2 在 Allegro 中執行

1. 將生成的 `apply_placement.il` 放置於 Allegro 的工作目錄。
2. 在 Allegro 命令列輸入：
   ```
   skill load("apply_placement.il")
   skill apply_placement()
   ```

## 3. DEF 檔案整合 (替代方案)

對於大規模設計，使用 DEF (Design Exchange Format) 檔案匯入更為高效。

### 3.1 生成 DEF 檔案

Python 系統可生成標準 DEF 格式的佈排區塊：

```def
COMPONENTS 2 ;
- U1 IC_PKG + PLACED ( 10000 20000 ) N ;
- C1 CAP_0402 + PLACED ( 15000 25000 ) N ;
END COMPONENTS
```

### 3.2 匯入 DEF 檔案

在 Allegro 中，選擇 `File -> Import -> DEF`，選擇生成的 `.def` 檔案即可更新元件位置。

## 注意事項

- **座標單位**：確保 Python 系統與 Allegro 使用相同的座標單位（如 mils 或 mm）。
- **原點對齊**：佈排前需確認板框原點 (0,0) 的位置，避免元件被放置於板外。
- **鎖定元件**：對於已手動固定位置的關鍵元件（如連接器），在導出資料時需標記為 `FIXED`，Python 系統將不會移動這些元件。
