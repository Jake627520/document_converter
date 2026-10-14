# 5. 授權與合規

[English](05-licensing-and-compliance.md) | **繁體中文** | [简体中文](05-licensing-and-compliance.zh-CN.md)

專案自己的程式碼採用自訂授權；它的 App 裡卻附帶了大約六十個別人的套件。這兩件事必須同時成立。
證據在 [`docs/LICENSE_AUDIT.md`](../LICENSE_AUDIT.md) 和 [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)；
這一章說明是怎麼走到那裡的。

> 這是查核了什麼的紀錄，不是法律意見。稽核文件對自己也是這麼說的。

## 依授權決定要附帶什麼

授權工作在任何程式碼被打包之前就開始了：App 裡要放什麼，有一部分是看它的授權允許 App 做什麼來決定的。

| 候選 | 授權 | 結果 |
| --- | --- | --- |
| PyMuPDF / MuPDF | AGPL-3.0，或 Artifex 商業授權 | **不附帶。** AGPL 的效力會擴及整個 App；商業授權則要花一筆專案不必花的錢 |
| `pypdfium2` + PDFium | BSD-3-Clause 或 Apache-2.0；PDFium 的元件皆為寬鬆授權 | **附帶**於 `pdf` 設定檔，作為 PDF 讀取器 |
| Docling，免模型流程 | MIT | **附帶**於 `pdf` 設定檔。它的模型流程沒有附帶，它的模型也從未審查過 |
| Marker | 程式碼 Apache-2.0；模型權重另有條款，附帶商業限制 | 選用引擎，由使用者自行安裝，從不打包 |
| MinerU 4.x | Apache-2.0 加附加條款：月活躍使用者超過 1 億或月營收超過 2,000 萬美元需另取得授權，線上服務必須標明使用了 MinerU | 選用引擎，從不打包。較舊的 `magic-pdf` 套件是 AGPL-3.0 |

「選用」本身沒有任何法律效力。使用者自行安裝的引擎仍適用它自己的條款；
稽核文件把這些條款記錄下來，讓安裝的人看得到自己同意了什麼。

## `pdf` 版 App 實際包含什麼

| | |
| --- | --- |
| 套件 | 60 個，以雜湊值鎖定 |
| GPL 或 AGPL 的執行階段程式碼 | 無 |
| 弱著作傳染性（weak copyleft） | `certifi` 和 `tqdm`（MPL-2.0），未經修改直接附帶——MPL 的義務只及於修改過的檔案 |
| PyInstaller | GPL-2.0-or-later，**附帶它的 Bootloader 例外條款**，允許把 bootloader 放進 App 出貨，而 GPL 不會擴及 App 本身 |
| PDFium | 一個二進位檔，內含 15 份元件授權：FreeType、libjpeg-turbo、ICU、libpng、zlib、OpenJPEG、Little CMS、Abseil 等 |
| 建置好的 App 裡的授權聲明 | 124 個檔案，涵蓋 60 個套件，位於 `Contents/Resources/legal/` |

## 讀授權本文，不只看標籤

授權標籤——「BSD」、「MIT」——說的是適用哪一類條款，沒說那些條款要你做什麼。
把 PDFium 的 15 份元件授權逐一讀過，發現其中兩份**要求**在只發行編譯後程式時，在發行文件裡加上一句話：

- *This software is based in part on the work of the FreeType Team.*
- *This software is based in part on the work of the Independent JPEG Group.*

兩句現在都寫在 `THIRD_PARTY_NOTICES.md` 裡，隨每個安裝包一起出貨。第一輪只找到 FreeType。
IJG 的要求在一個獨立的檔案 `libjpeg_turbo.ijg` 裡，是把每一份隨附的授權檔完整讀完才找到的。
其中有四份授權還禁止用作者的名義做廣告，所以這些聲明寫成文件說明，而不是背書。

## 授權聲明不見的時候

建置是用檔名收集授權檔的——`LICENSE`、`COPYING`、`NOTICE`。依照現行標準
（[PEP 639](https://peps.python.org/pep-0639/)）打包的套件，會把授權檔放在 `licenses/` 資料夾裡，
檔名由上游決定，例如 `freetype.txt`。這類檔案共 21 個，全被一聲不吭地漏掉了，包括 `pypdfium2` 的 18 個。

問題是在負責人的 Mac 上浮現的：建置停了下來，因為 `latex2mathml` 完全沒有授權聲明。
追查原因後發現，3.81.0 和 3.81.1 兩個版本都沒附授權檔，而收集器另外還有一個更安靜的漏洞。
[#5](https://github.com/Jake627520/documnet_converter/pull/5) 的修正：

- 除了比對檔名，也比對那個標準位置；
- 把 `latex2mathml` 鎖定在 3.80.0，這個版本有附授權檔；
- 新增 `scripts/packaging/audit_notices.py`，依雜湊值下載每個鎖定的 wheel，用建置本身的規則檢查，
  完全不用安裝——所以這個問題在建置之前、在任何機器上都能回答。

建置大聲地失敗，是好的結果。那 21 份被漏掉的聲明，可是連一個錯誤都沒產生。

## 寫給另一個版本的文件

法律文件是為第一版 App 寫的，那一版不含任何文件引擎。後來 `pdf` 設定檔加入了 Docling 和 PDFium——
文件卻仍然寫著 Docling 被排除在外。沒有任何東西會拿文字敘述去對照依賴清單。

這是在負責人要求公開前再確認一次授權時抓到的，並在 [#6](https://github.com/Jake627520/documnet_converter/pull/6) 修正。
從中得到的規則：**出貨內容的變更，就是法律文件的變更**，放在同一個 PR 裡。

## 公開不等於開源

repo 是公開的；授權沒有改變。自訂的 [`LICENSE`](../../LICENSE) 允許個人使用與公司內部使用，
包括內部商業用途，並限制原始程式碼的轉售與再散布。這不是開源授權——
[開源定義（Open Source Definition）](https://opensource.org/osd)要求再散布的自由。

公開只多了一件事：GitHub 的服務條款讓任何人都能檢視這個 repo，並在 GitHub 上 fork。
README 的 fork 說明寫了這樣做允許什麼、不允許什麼。第三方條款不論 repo 公開或私有都一樣。

## 重建元件來避開它的授權

在評估各種選項時出現過一個問題：能不能用逆向工程工具，把一個授權有限制的元件重建成專案自己的東西？

沒辦法用這種方式讓條款消失。從另一個程式反編譯或反組譯出來再重建的程式碼，仍然是衍生自它，
而且很多授權直接禁止逆向工程。行得通的路，是這個專案已經走的或保留的這幾條：

- **選擇寬鬆授權的替代品**——用 PDFium，而不是 MuPDF；
- **購買商業授權**，如果對方有提供；
- **淨室實作（clean-room）**——由沒研究過原始程式的人，依據公開規格撰寫。
  這是一套有自己紀錄的法律程序，不是程式代理能替自己擔保的事。

## AI 輔助創作

這個專案大部分的程式碼由 AI 程式代理撰寫。
[美國著作權局 2025 年 1 月的報告](https://www.copyright.gov/ai/)認為，著作權保護及於人的創作貢獻——
選擇、編排、修改——但不及於由 AI 系統決定的表達；單純下提示不構成創作。
這個專案有多少可受保護的部分，尚未評估。

這會影響專案自己的授權能在多大程度上約束它自己的程式碼。它完全不改變第三方條款——那些條款不論如何都約束這個專案。
稽核文件把它記錄為一個未解的問題，它本來就是。
