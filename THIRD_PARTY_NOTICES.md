# Third-Party Notices & Licenses

本專案 (`document-converter-skill`) 設計為本地優先（Local-first）的文件轉換抽象架構。為了確保法律合規、商業使用自由度與智慧財產權保護，各底層解析引擎與其相應的模型權重採取明確的隔離策略。

---

## 核心引擎授權與模型審查一覽表

| 引擎名稱 | 程式碼授權 (Code License) | 模型權重授權 (Model License) | 預設安裝 | 商業使用 (Commercial Use) | 官方儲存庫 / 來源 |
|---|---|---|---|---|---|
| **Docling** | MIT License | Apache-2.0 / MIT (DocLayNet, TableFormer) | **是 (Primary)** | ✅ 允許（寬鬆授權） | [docling-project/docling](https://github.com/docling-project/docling) |
| **Marker** | GPL-3.0 / 專有商業授權 | GPL-3.0 / 非商業限制 (Surya, Texify) | **否 (Optional)** | ⚠️ 需注意感染與商業限制 | [VikParuchuri/marker](https://github.com/VikParuchuri/marker) |
| **MinerU** | AGPL-3.0 / Apache-2.0 | CC-BY-NC-4.0 / 特定研究協議 (UniMERNet, etc.) | **否 (Optional)** | ⚠️ 具非商業(NC)及AGPL風險 | [opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

---

## 詳細第三方專案說明

### 1. Docling (預設推薦引擎)
- **維護者**: IBM Research
- **程式碼授權**: MIT License
- **模型授權**:
  - `docling-ibm-models` (Layout analysis, Table structure recognition): Apache-2.0 / MIT
  - OCR 引擎: EasyOCR (Apache-2.0) / Tesseract (Apache-2.0) / RapidOCR (Apache-2.0)
- **商業使用限制**: 無特殊商用限制。符合一般企業與閉源專案的商業合規要求。
- **隔離策略**: 作為主要（Primary）依賴，隨專案預設提供。

### 2. Marker (可選後備引擎 - Optional Fallback)
- **維護者**: Datalab / Vik Paruchuri
- **程式碼授權**: GPL-3.0（若需商業使用須向官方購買商業許可證）
- **模型授權**:
  - Surya (Layout, Text detection, Table parsing): GPL-3.0 / 專有條款
  - Texify (Formula recognition): GPL-3.0
- **商業使用限制**:
  - GPL-3.0 具強傳染性。若將 Marker 程式碼直接靜態連結或納入閉源/專有軟體，可能觸發 GPL-3.0 原始碼公開義務。
  - 模型權重包含非商業使用限制。
- **隔離策略**:
  - 嚴格透過外部 CLI 呼叫（Process isolation）或 `optional-dependencies` 方式隔離。
  - **不得作為預設安裝項目**，避免引入授權傳染。

### 3. MinerU / Magic-PDF (可選後備引擎 - Optional Fallback)
- **維護者**: OpenDataLab / 上海人工智能實驗室
- **程式碼授權**: AGPL-3.0 / Apache-2.0 (部分模組)
- **模型授權**:
  - 整合多個第三方與自研模型，包含 UniMERNet (公式辨識)、PaddleOCR、LayoutLMv3、YOLO。
  - 部分模型標註為 CC-BY-NC-4.0 (非商業用途) 或具有專有研究使用限制。
- **商業使用限制**:
  - AGPL-3.0 網路傳染性（若透過網路服務提供轉換，可能要求公開整個服務原始碼）。
  - 模型具 NC (Non-Commercial) 限制，直接於商業環境獲利可能面臨侵權訴訟。
- **隔離策略**:
  - 僅支援以本地已安裝之 CLI (`mineru` / `mineru-kit`) 作為可選外部程序呼叫。
  - **嚴格禁止在專案本體中重新散布（redistribute）其模型權重**。

---

## 基礎 Python 依賴庫

| 套件 | 授權 | 用途 |
|---|---|---|
| `typer` | MIT | CLI 命令列框架 |
| `rich` | MIT | 終端機格式化輸出與表格呈現 |
| `pip-audit` | Apache-2.0 | 依賴漏洞靜態掃描 (開發環境) |
| `pip-licenses` | MIT | 依賴授權檢核工具 (開發環境) |
| `pytest` | MIT | 單元測試框架 (開發環境) |
