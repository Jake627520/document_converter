# CHG-001 — Standalone Offline HTML Renderer

## 1. Proposal Summary
- **Change ID**: CHG-001
- **Title**: Standalone Offline HTML Renderer
- **Status**: IMPLEMENTED (local unittest/lint passed; pytest coverage not run because pytest is not installed; not yet archived)
- **Author**: Antigravity & User
- **Target Release**: v0.2.1

## 2. Problem Statement
目前 `writer.py` 的 HTML fallback 會嘗試載入可選 `markdown` 套件，失敗時則把整份 Markdown 放入 `<pre>`；因此格式化與安全行為會隨安裝環境改變。此 change 提供零 runtime dependency 的內建 renderer，並讓 fallback 一律使用它。引擎提供的原生 HTML 保持優先。

## 3. Scope & Objectives
1. **獨立原生渲染 (Zero External Runtime Dependency)**：
   - 提供內建的 HTML 渲染引擎，不強制依賴外部編譯器。
   - 由內建 parser 處理 Headings, Code Blocks, Tables, Paragraphs, Lists, Inline Code/Emphasis 與 HTML escaping；不載入或執行 Markdown 原始 HTML。
2. **自包含輸出 (No External Resources)**：
   - HTML 樣式直接內嵌於 `<style>` 標籤中，不包含任何外部 `<link href="http...">` 或 `<script src="http...">`。
3. **安全性與跳脫 (XSS Defense)**：
   - 原始文字中的 `<script>`, `&`, `<`, `>` 嚴格跳脫，避免 HTML 注入。
4. **與現有 Writer 相容**：
   - `write_result` 介面保持不變，自動替換 fallback 邏輯。

## 4. Open Design Decisions
- **Renderer implementation**：採用小型內建 parser，避免新增 runtime dependency；範圍限於本文件列出的 Markdown 語法。
- **數學公式 (LaTeX Math)**：本 change 不執行 MathJax/KaTeX，也不特別轉換公式；公式標記作一般文字處理並跳脫 HTML。未來若加入離線數學 renderer，另以獨立 change 定義。

## 5. Acceptance Criteria
- `write_result` 遇到 engine 未提供 HTML 而有 Markdown 時，產出完整、自包含的 HTML5 文件。
- Renderer 支援 heading、paragraph、ordered/unordered list、table、fenced code、inline code/emphasis 與空文件。
- Markdown 文字與標題均跳脫 HTML；code fence 語言只接受安全字元，不允許注入 attribute。
- Renderer 不引入 runtime dependency、不呼叫網路、不載入外部資源；原生 engine HTML 原樣保留。
- renderer、writer 與完整本機測試通過。
