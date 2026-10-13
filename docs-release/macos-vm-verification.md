# 用 macOS 虛擬機驗收候選包（免費，不需要第二台 Mac）

候選包有兩項風險只有在**別人的機器**上才會現形：

1. **漏帶東西**——`.app` 其實偷偷依賴了建置機器上裝過的 Python、Homebrew 套件或系統函式庫。
   在建置的那台機器上永遠測不出來，因為那些東西就在那裡。
2. **Gatekeeper**——從網路拿到的檔案會被貼上隔離標籤（`com.apple.quarantine`），
   收件者看到的是阻擋畫面，不是你看到的畫面。

一台全新的 macOS 虛擬機可以免費驗收這兩項。Apple 的授權允許在同一台 Apple Silicon Mac 上
**同時執行 2 台 macOS 虛擬機**（授權條款 2.B.iii 列入軟體開發與測試用途），
Virtualization framework 會在核心層擋掉第三台。

## 這能驗收什麼、不能驗收什麼

| | |
|---|---|
| ✅ `.app` 是否真的自帶一切執行所需 | 客體系統沒有 Python、沒有 Xcode、沒有 Homebrew |
| ✅ Gatekeeper 的完整流程 | 從客體系統內下載 ZIP，會真的被貼標籤 |
| ✅ 收件者實際看到的錯誤訊息與放行步驟 | 逐字記錄下來，才能寫給同事 |
| ✅ 首次啟動的系統權限提示 | 網路、檔案存取等 |
| ❌ 不同世代晶片的差異 | M1／M2／M3／M4 共用同一顆主機晶片 |
| ❌ 不同 macOS 大版本的差異 | 客體版本受主機支援範圍限制，取得舊版還原映像檔也不容易 |
| ❌ 真實網路環境、企業 MDM 管控的機器 | 虛擬機是乾淨的未納管機器 |

換句話說：**虛擬機抓「漏帶東西」，抓不到「硬體與 OS 版本差異」。**
前者是跨機安裝最常出事的地方，所以這個驗收有價值；但它不等於在真正的第二台機器上驗過。

## 事前準備

- Apple Silicon Mac（主機）
- 主機可用磁碟空間約 **80 GB 以上**：還原映像檔約 14 GB，虛擬磁碟建議 64 GB
- [UTM](https://mac.getutm.app/)：免費開源。Mac App Store 上的付費版（約 USD 10）功能相同，
  差別是自動更新。兩者皆使用 Apple 的 Virtualization framework
- 已建置完成的候選包（見 `docs-release/macos.md`）

## 步驟

### 1. 建立虛擬機

UTM → **Create a New Virtual Machine** → **Virtualize** → **macOS 12+**。

還原映像檔留空，UTM 會自動下載一份與主機相容的 macOS（約 14 GB，請預留時間）。
若要指定特定版本，須自備對應的 `.ipsw` 還原映像檔。

建議配置：CPU 4 核、記憶體 8 GB、磁碟 64 GB。記憶體給 4 GB 以下會明顯變慢。

### 2. 初始設定——保持乾淨

客體系統開機後走完設定流程，但：

- **跳過** Apple ID 登入
- **跳過** 移轉輔助程式
- **不要**安裝 Python、Xcode、Command Line Tools 或 Homebrew

> 這一點是整個驗收的重點。客體系統一旦裝了 Python，
> 就再也無法分辨「`.app` 自己帶的」和「系統上剛好有的」，驗收就失去意義。

設定完成後，**先在 UTM 存一份快照**（UTM → 虛擬機設定 → 存檔）。
之後每次要重測乾淨安裝，回到這個快照即可，不必重裝系統。

### 3. 把候選包傳進客體系統——要用會貼標籤的方式

這一步刻意模擬同事的真實情境。**不要**用 UTM 的共用資料夾或拖放，
那樣不會貼上隔離標籤，就測不到 Gatekeeper。

在**主機**的候選包目錄起一個臨時 HTTP 伺服器：

```sh
cd build/private-release/candidate-pdf
python3 -m http.server 8000
```

查出主機 IP：

```sh
ipconfig getifaddr en0
```

在**客體系統**用 Safari 打開 `http://<主機IP>:8000/`，點擊
`Document-Converter-macos-arm64-pdf-local-candidate.zip` 下載。

下載完成後，在客體系統確認標籤真的貼上了：

```sh
xattr -p com.apple.quarantine ~/Downloads/Document-Converter-macos-arm64-pdf-local-candidate.zip
```

有輸出（類似 `0083;...;Safari;...`）才算成功模擬。沒有輸出表示傳輸方式不對，請改用 Safari 下載。

測完記得在主機按 Ctrl-C 關掉 HTTP 伺服器。

### 4. 核對 ZIP 的 SHA-256

```sh
shasum -a 256 ~/Downloads/Document-Converter-macos-arm64-pdf-local-candidate.zip
```

要與建置輸出的 `zip_sha256` 一致。不一致表示傳輸過程出了問題，先解決再往下走。

### 5. 解壓縮並嘗試開啟——預期會被擋

在 Finder 中雙擊 ZIP 解壓縮，然後雙擊 `Document Converter.app`。

**預期被 Gatekeeper 阻擋**，因為候選包只有 ad-hoc 簽章，沒有 Developer ID 簽章，也未經 Apple notarization。

逐字記錄跳出的訊息。這就是同事會看到的畫面。

> 注意：macOS 15 (Sequoia) 起，Apple 已移除「按右鍵選『打開』」繞過 Gatekeeper 的方式。
> 現在只能走系統設定。

### 6. 放行並確認真的能跑

**系統設定 → 隱私權與安全性 → 捲到「安全性」區塊 → 找到被擋的 App → 「仍要打開」**，
輸入管理者密碼。（此按鈕只在嘗試啟動後的一段時間內出現；若找不到，先再雙擊一次 App。）

放行後確認：

1. 瀏覽器自動開啟 `http://127.0.0.1:<port>`，看到上傳頁面
2. 頁面標示接受的格式含 `.pdf`
3. 上傳一個有文字層的 PDF → 成功轉出 Markdown
4. 上傳一個掃描的 PDF → 回報「沒有文字層」，而不是空檔案
5. 上傳一個 `.docx` → 被拒絕為不支援的格式

### 7. 在客體系統確認自我完整性

這是驗收「漏帶東西」的關鍵一步。客體系統沒有 Python，所以若下列指令能跑，
就證明 `.app` 自帶了完整的執行環境：

```sh
"/Applications/Document Converter.app/Contents/MacOS/Document Converter" --diagnostics
```

（若未搬到 `/Applications`，請改成實際路徑。）

輸出應為：

```json
{
  "profile": "pdf-text",
  "inputs": [".markdown", ".md", ".pdf", ".txt"],
  "frozen": true,
  "forbidden_loaded": []
}
```

同時確認客體系統真的沒有 Python，驗收才站得住腳：

```sh
which -a python3 python3.12
```

`/usr/bin/python3` 可能存在（macOS 內建的 stub），但不應出現 Homebrew 或 uv 的路徑。

## 驗收紀錄表

每次驗收請記錄下列各項，連同結果存進 `verification/<日期>-<主題>/`：

| 項目 | 結果 |
|---|---|
| 主機 macOS 版本與晶片 | |
| 客體 macOS 版本 | |
| ZIP SHA-256 與建置輸出一致 | ☐ |
| 隔離標籤確實貼上（`xattr -p` 有輸出） | ☐ |
| Gatekeeper 阻擋訊息（逐字） | |
| 經系統設定放行後可啟動 | ☐ |
| `--diagnostics` 的 `forbidden_loaded` 為空 | ☐ |
| 文字層 PDF 轉檔成功 | ☐ |
| 掃描 PDF 回報無文字層 | ☐ |
| `.docx` 被拒絕 | ☐ |
| 客體系統無 Homebrew／uv 的 Python | ☐ |

## 不想裝虛擬機時的簡化版

只想看 Gatekeeper 會怎麼擋，可以在主機上手動貼標籤模擬：

```sh
cd "build/private-release/candidate-pdf/Document-Converter-macos-arm64-pdf-local-candidate"
xattr -w -r com.apple.quarantine "0081;$(printf %x $(date +%s));Safari;" "Document Converter.app"
open "Document Converter.app"      # 預期被擋

# 測完撕掉標籤恢復原狀
xattr -dr com.apple.quarantine "Document Converter.app"
```

這只驗收 Gatekeeper，**不驗收「漏帶東西」**——主機上該有的東西都還在。
兩者不能互相取代。

## 關於發佈

候選包固定標記 `distribution_ready: false`。虛擬機驗收通過**不等於**可以發佈：
正式交付仍需確認自有權利與接受者、Developer ID 簽章與 notarization，
以及在真實的目標機器上安裝驗收。詳見 `docs-release/macos.md` 與 `docs/PRIVATE_DISTRIBUTION.md`。

**不得**以關閉 Gatekeeper（`spctl --master-disable`）或教使用者習慣性移除隔離標籤
來取代上述步驟。前者關掉的是全系統防護；後者是在訓練使用者忽略安全警告。
