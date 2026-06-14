# 小说阅读器 (Novel Reader)

基于 **PySide6** 构建的现代化本地小说阅读器。支持本地 txt 导入、智能分章、章节级阅读、阅读进度与统计、自定义快捷键、多套主题等特性，并支持一键打包为 Windows 单文件可执行程序。

> 设计灵感来自 [Koodo Reader](https://github.com/koodo-reader/koodo-reader) 与 [Legado](https://github.com/gedoor/legado)。

> 🌐 **语言 / Language**：[English](README.md) · [简体中文](README-CN.md)

---

## 目录

- [主要特性](#主要特性)
- [运行环境](#运行环境)
- [快速开始（源码运行）](#快速开始源码运行)
- [快捷键](#快捷键)
- [目录结构](#目录结构)
- [数据存储位置](#数据存储位置)
- [打包成 exe](#打包成-exe)
- [关于作者与捐献](#关于作者与捐献)
- [常见问题](#常见问题)

---

## 主要特性

- 📚 **本地 txt 导入**：选择本地 txt 文件即可导入，相同路径的书籍不会重复导入
- 🧠 **智能分章**：自动识别 `第X章 / Chapter N` 等常见章节标题
- 📖 **按章阅读**：每次只渲染整章内容，章节内自由滚动；滚到章末按 `PageDown`/`→`/`Space` 自动进入下一章，反之亦然
- 🔖 **书签 / 进度自动保存**：阅读进度、书签、设置全部写入 SQLite，下次启动自动恢复
- 📊 **阅读统计**：今日阅读时长 / 字数、总阅读量、书架总字数一应俱全
- 🎨 **多套主题**：明亮 / 暗黑 / 羊皮纸 / 护眼绿，可在阅读界面一键切换
- ⌨️ **快捷键完全可定制**：每个动作最多绑定 4 个键位，在「设置 → 快捷键」中修改并立即生效
- 📦 **打包即用**：内置 PyInstaller 打包脚本，30 秒产出单文件 exe

---

## 运行环境

- Python **3.10+**（推荐 3.11/3.12/3.13）
- Windows / macOS / Linux（仅在 Windows 上验证过 exe 打包）
- 依赖：见 [requirements.txt](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/requirements.txt)

```text
PySide6>=6.6.0
Pillow>=10.0.0
pyinstaller>=6.0.0
```

---

## 快速开始（源码运行）

```powershell
# 1) 安装依赖
pip install -r requirements.txt

# 2) 启动应用
python main.py
```

应用启动后：

1. 点击右上角 **「➕ 导入书籍」** 选择本地 txt 文件（支持多选）
2. 卡片点击 → 进入阅读视图
3. 阅读界面顶栏可切换主题、显示目录、添加书签、打开设置
4. **Esc** 返回书架
5. 悬停卡片或右键 → 可从书架删除单本书籍

---

## 快捷键

默认绑定（所有快捷键可在 `设置 → 快捷键` 重新指定）：

| 动作 | 默认键位 |
| --- | --- |
| 下一章 / 章末翻页 | `→` / `PageDown` / `Space` |
| 上一章 / 章首翻页 | `←` / `PageUp` |
| 强制下一章 | `Ctrl+→` / `]` |
| 强制上一章 | `Ctrl+←` / `[` |
| 返回书架 | `Esc` |
| 显示/隐藏目录 | `Ctrl+B` |
| 添加书签 | `Ctrl+D` |
| 切换主题 | `Ctrl+T` |
| 增大 / 减小字号 | `Ctrl+=` / `Ctrl+-` |
| 打开设置 | `Ctrl+,` |

> 章内按 `PageDown` / `→` / `Space`：若尚未滚到章节底部则执行翻页；滚到底部后再按则跳到下一章。

---

## 目录结构

```text
novel-reader/
├── app/                          # 应用源代码
│   ├── config.py                 # 路径/设置/快捷键默认值
│   ├── controllers/              # 业务逻辑层
│   │   └── library_controller.py
│   ├── models/                   # 数据模型 + SQLite
│   │   ├── book.py
│   │   └── database.py
│   ├── resources/                # 资源（主题 / QSS）
│   │   ├── styles/style.qss
│   │   └── themes.py
│   ├── utils/                    # 工具
│   │   ├── book_parser.py        #   章节解析
│   │   └── cover_generator.py    #   封面生成
│   ├── views/                    # 视图层
│   │   ├── about_dialog.py       #   关于 + 捐赠
│   │   ├── main_window.py
│   │   ├── reader_view.py
│   │   ├── settings_dialog.py
│   │   └── statistics_dialog.py
│   └── widgets/                  # 自定义控件
│       ├── book_card.py
│       └── book_grid.py
├── erweima/                      # 捐赠二维码（打包时注入 exe）
│   ├── usdt-erc20.jpg
│   ├── usdt-tr20.jpg
│   └── xmr.jpg
├── main.py                       # 应用入口
├── build.py                      # 一键打包脚本
├── novel_reader.spec             # PyInstaller 打包配置
└── requirements.txt
```

---

## 数据存储位置

打包后的可执行文件把用户数据放在系统用户目录，**不会污染安装目录**：

| 系统 | 用户数据目录 |
| --- | --- |
| Windows | `%APPDATA%\NovelReader\`<br/>即 `C:\Users\<你>\AppData\Roaming\NovelReader\` |
| macOS | `~/Library/Application Support/NovelReader/` |
| Linux | `$XDG_DATA_HOME/NovelReader/` 或 `~/.local/share/NovelReader/` |

子目录：

```text
NovelReader/
├── library.db       # SQLite 数据库（书籍 / 进度 / 书签 / 设置）
├── covers/          # 封面图片缓存
└── logs/            # 日志
```

源码运行时为兼容开发体验，回退到项目根目录下的 `data/`。

---

## 打包成 exe

项目自带 PyInstaller 打包配置，常用命令：

```powershell
# 默认：单文件 release 模式（产物 dist/NovelReader.exe）
python build.py

# 目录模式（启动更快，多文件）
python build.py --onedir

# 调试模式（带控制台 + 详细日志）
python build.py --debug

# 跳过清理（增量构建）
python build.py --no-clean
```

打包配置见 [novel_reader.spec](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/novel_reader.spec)：
- 已注入 `app/resources/styles/style.qss` 与 `erweima/`（捐赠二维码）
- 已排除 `QtNetwork` / `QtWebEngine*` / `QtMultimedia` 等用不到的子模块，减小体积
- 默认开启 UPX 压缩，产物约 50 MB

直接运行产物：

```powershell
.\dist\NovelReader.exe
```

---

## 关于作者与捐献

应用内点击侧栏 **「ℹ 关于」** 或菜单 `帮助 → 关于` 打开「关于」对话框。

**作者**

- 作者：**Lorime**
- 邮箱：lorime@126.com

**捐献支持**

如果您觉得这个工具对您有帮助，欢迎通过以下方式捐献支持开发：

| 币种 | 地址 |
| --- | --- |
| XMR | `4DSQMNzzq46N1z2pZWAVdeA6JvUL9TCB2bnBiA3ZzoqEdYJnMydt5akCa3vtmapeDsbVKGPFdNkzzqTcJS8M8oyK7WGj5qMvNZRw61w6wMF` |
| USDT (TRC20) | `TG6DCBoQszDxc64owRZKkSHqZfcAQrqR8uM` |
| USDT (ERC20) | `0x4323d39BA9b6Bd0570920e63a8D3a192b4459330` |

「关于」对话框内置三个钱包的二维码图片（来自 `erweima/` 目录），扫描即可查看对应地址。地址文案也可直接复制。

> 替换或新增二维码：把同名 jpg/png 覆盖 `erweima/` 下文件后重新执行 `python build.py` 即可。

---

## 常见问题

**Q1: 启动后看不到导入按钮？**
A: 主窗口右侧顶栏的 **「➕ 导入书籍」** 即为入口，也可使用菜单 `文件 → 导入书籍` 或 `Ctrl+O`。

**Q2: 书架上的书可以删除吗？**
A: 可以。两种方式：
- 悬停卡片 → 右上角 ✕ 按钮
- 右键卡片 → 弹出菜单选择「从书架删除」

删除只会清理：书架数据库记录、本程序生成的封面缓存、原文件保留。如需彻底重置，可手动删除 `%APPDATA%\NovelReader\library.db`。

**Q3: 自定义快捷键不生效？**
A: 部分键位（如 `Ctrl+Alt+Del`）会被系统占用，请改用其他组合。设置保存后立即生效，无需重启。

**Q4: 打包后 exe 体积太大？**
A: 50 MB 主要来自 PySide6。可在 `novel_reader.spec` 的 `excludes` 中继续裁剪不用的 Qt 子模块；或在 `build.py` 加 `--onedir` 并用 `nuitka` 进一步优化。

**Q5: 捐赠二维码没显示？**
A: 检查 `erweima/` 目录里是否存在 `xmr.jpg` / `usdt-tr20.jpg` / `usdt-erc20.jpg`。打包后图片随 exe 一起分发，若重命名了文件名，需要同时更新 [app/config.py](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/app/config.py) 中的 `DONATION_QR_FILES`。

---

## 多语言文档

仓库自带多种语言的文档：

- 🇨🇳 简体中文：[README-CN.md](README-CN.md)
- 🇬🇧 English：[README.md](README.md)

欢迎贡献更多语言 — 提交 PR 时附带 `README-<lang>.md`，并在上方列表中追加即可。
