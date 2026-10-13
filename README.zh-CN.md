# Document Converter 文档转换工具

[English](README.md) | [繁體中文](README.zh-TW.md) | **简体中文**

本地优先的文档转换工具：包括命令行工具、在你自己电脑上运行的浏览器工作台、
打包好的 macOS 应用，以及供 Codex 与 Claude 使用的 agent 技能（[`SKILL.md`](SKILL.md)）。
文档全部在你的电脑上转换，不会上传到任何远程服务。

---

## 1. 能转换什么

**输入格式。** 从源代码运行并安装 Docling 时，支持 PDF、DOCX、PPTX、XLSX、HTML、
EPUB、图片、Markdown 和文本文件 —— 实际支持范围请参阅所安装 Docling 版本的支持列表。
macOS 应用接受的格式较少，取决于其配置（profile），见第 2 节。

**输出格式。**

| 输出 | 从源代码运行（CLI 与浏览器） | macOS 应用 `text` 版 | macOS 应用 `pdf` 版 |
|---|---|---|---|
| Markdown（`.md`） | ✅ | ✅ | ✅ |
| HTML（`.html`） | ✅ | ✅ | ✅ |
| 纯文本（`.txt`） | ✅ | ✅ | ✅ |
| Docling JSON（`.json`） | ✅ 文件经 Docling 引擎解析时 | — | ✅ 仅限 PDF 输入 |

Docling JSON 是引擎对文档结构的解析结果，因此只有经过引擎读取的文件才有。
Markdown 和文本文件是直接读取的，而 `text` 版应用完全不包含引擎。

## 2. macOS 应用

仅支持 Apple Silicon（M 系列芯片）的 Mac。共有两个经过审查的配置：

| 配置 | 接受的文件 | 包含内容 |
|---|---|---|
| `text` | UTF-8 编码的 `.md`、`.markdown`、`.txt` | 不包含任何文档引擎和模型 |
| `pdf` | 以上格式，外加**已有文字层的 PDF** | Docling 无需模型的 PDF 读取器 —— 没有 OCR、没有 AI 模型、没有 PyTorch，也不会下载任何内容 |

`pdf` 版只提取 PDF 中原本就有的文字，不会重建标题层级或表格。扫描的 PDF 没有文字层，
应用会明确告诉你，而不是返回一个空文件。两个版本都不接受 Office 文档和图片。

### 打开应用

- **你自己构建的应用**：直接双击即可打开。macOS 只会拦截来自互联网的文件。
- **别人发给你的应用**（下载、隔空投送或通过聊天软件发送）：首次打开会被拦截，
  因为候选包只有 ad-hoc 签名，没有 Developer ID 签名，也没有经过 Apple 公证。
  从 macOS 15 开始，「按住 Control 点按 › 打开」已无法绕过这一拦截。请先尝试打开应用一次，
  再前往**系统设置 › 隐私与安全性**，在「安全性」部分找到该应用，
  点击**仍要打开**并输入管理员密码。

请不要为了绕过这一步而关闭 Gatekeeper。

### 使用方法

1. 双击 `Document Converter.app`。它会启动本地服务，并用默认浏览器打开
   `http://127.0.0.1:<port>`。
2. 拖入或选择最多 **5 个**文件。单个文件和所选文件的合计大小各不得超过 **24 MiB**。
3. 选择输出格式，点击**开始转换**。一份文档会下载为单个文件，多份文档会下载为 ZIP。
   下载的文件以原始文档的名称命名，中文文件名同样适用。
4. 上传的文件以系统生成的名称暂存在系统临时文件夹中，每次转换完成后即被删除。
5. 关闭浏览器不会停止应用。要退出它，请打开**活动监视器**，找到 `Document Converter` 并退出。

运行应用无需安装 Python、Node.js、Docker 或 VS Code。

### 验证状态

| | |
|---|---|
| ✅ 已在 Apple Silicon Mac 上验证（2026-10-12／13） | `pdf` 候选包已完成构建、ad-hoc 签名和压缩；能像普通应用一样打开并转换真实文档；冻结后的运行环境报告未加载任何禁止的模块；包含 124 个第三方许可声明文件 |
| ℹ️ 需重新构建 | 该候选包早于纯文本、Docling JSON 输出和下载文件名功能；用此版本重新构建的候选包才会具备这些功能 |
| ⏳ 尚未验证 | 在第二台 Mac 上安装 —— [`docs-release/macos-vm-verification.md`](docs-release/macos-vm-verification.md) 介绍了如何用免费的 macOS 虚拟机进行验证 |
| ❌ 尚未完成 | Developer ID 签名和 Apple 公证；每个候选包都标记为 `distribution_ready: false` |
| ❌ 不提供 | Windows —— 没有安装包，也未做过平台测试 |

### 自行构建

```sh
RELEASE_PROFILE=pdf BUILD_PYTHON="$HOME/.local/bin/python3.12" \
  sh scripts/packaging/bootstrap_macos.sh --output-dir build/private-release/candidate-pdf
```

去掉 `RELEASE_PROFILE=pdf` 即构建 `text` 版。完整的构建与验收流程请参阅
[`docs-release/macos.md`](docs-release/macos.md)。

## 3. 从源代码运行（开发者）

支持 Python 3.11 至 3.14；CI 测试 3.11 和 3.12。

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
```

Windows 的命令仅说明如何配置源代码环境，并不代表 Windows 已经过测试。

### 浏览器工作台

```bash
pip install -e ".[web]"
document-converter web             # http://127.0.0.1:8765 ; --port 8766 for another port
```

服务器只绑定本地回环地址（loopback）。限制与应用相同：最多五个文件、单个文件和合计
各 24 MiB、单次请求 25 MiB。它使用与 CLI 相同的 `auto` 引擎选择，因此会使用已安装的
任何引擎（包括 Marker 和 MinerU），但不会为你安装任何引擎。

### 命令行

```bash
document-converter convert paper.pdf --to md
document-converter convert paper.pdf --to md --to html --to json --to txt
document-converter convert ./documents --to md --output ./converted
document-converter list-engines
```

指定引擎：

```bash
document-converter convert paper.pdf --engine docling --to md
document-converter convert paper.pdf --engine docling-native --to md   # no PyTorch, no model download
document-converter convert paper.pdf --engine marker --to md
document-converter convert paper.pdf --engine mineru --to md
```

清理 Markdown 中的杂讯：

```bash
document-converter convert paper.pdf --to md --clean
document-converter convert paper.pdf --to md --clean --strip-page-numbers
```

`--clean` 会删除带标注的页码，例如 `Page 3 of 12`、`4 / 20` 和 `- 5 -`。
只有数字的行会被保留，因为引擎常把表格单元格和其他数值单独放在一行；
只有当文档的页码以单独数字的形式残留、并且你能接受同时删除单独数值时，才添加 `--strip-page-numbers`。

### 无需 PyTorch 的 PDF 转换（`docling-native`）

Docling 默认的 PDF 流程会运行布局和表格模型：需要安装数 GB 的 PyTorch，
并在首次使用时下载模型权重。`docling-native` 改用 Docling 无需模型的 `NativePdfPipeline`：

```bash
pip install "docling-slim[convert-core,format-pdf]" typer rich pypdf
pip install -e . --no-deps
```

这样安装约 0.4 GB。它只转换 PDF，不重建文档结构，不做 OCR，每次转换都会以警告记录这一限制。
`auto` 会把它排在最后，因此在安装了模型版引擎时会优先使用模型版。

### 可选引擎

```bash
pip install ".[marker]"   # check the package and model license terms first
# MinerU: install its CLI separately, after reading docs/LICENSE_AUDIT.md
```

## 4. 工作原理

每个引擎都生成同一种标准化的转换结果，再由 writer 转换为你需要的输出格式。
解析与输出相互分离，因此新增输入或输出格式时无需修改 CLI。
引擎都通过 `document_converter/engines/` 中的适配器（adapter）接入；输出序列化集中在 `writer.py`。
Docling 是主引擎；Marker 和 MinerU 是可选的备用引擎，它们的代码与模型许可分别审查。

## 5. 你的文档

> [!IMPORTANT]
> 1. 转换任何文档（PDF、Office 文档、图片或扫描件）之前，请确认你有权处理该文档，
>    必要时也有权分发。
> 2. 请勿将客户机密资料、真实商业文档、个人数据或未经授权的受版权保护文档提交到本仓库。
> 3. 自动化测试只使用自行合成、属于公有领域或不含敏感信息的文档。

## 6. 安全与隐私

- **本地优先。** 文档由本地安装的引擎处理。并非每一种引擎、软件包与模型下载器的组合
  都经过网络行为审计；处理敏感文件前，请先确认你选用的引擎。
- **上传文件。** 以系统生成的名称暂存，每次请求结束后删除，转换失败时同样如此。
- **日志。** CLI 会报告处理状态和错误。第三方引擎可能会自行记录日志。
- **敏感文件。** `.gitignore` 已涵盖常见的输出文件、凭据、临时素材和模型缓存，
  但它不会移除已被跟踪的文件；每次 commit 前请先检查 `git status`。

## 7. 许可

**本项目。** Copyright (c) 2026 Jake Chiu，采用[专有使用许可](LICENSE)：
允许个人使用和公司内部使用（包括内部商业用途）；不得转售或分发本项目自有的软件。
这不是开源许可证。

**第三方组件**各自保留原有的许可，本项目的任何内容都不限制原作者授予的权利。
请参阅 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 和
[`docs/LICENSE_AUDIT.md`](docs/LICENSE_AUDIT.md)。每个安装包的 `legal/` 文件夹
都附有所有组件的许可与声明原文。

macOS 应用的 `pdf` 版包含部分基于 FreeType Team 和 Independent JPEG Group 成果的软件。

> 本页为译文，仅供参考。许可条款以英文 [`LICENSE`](LICENSE) 为准；
> 第三方许可以 `THIRD_PARTY_NOTICES.md`、`docs/` 中的文档及各组件许可原文为准。
