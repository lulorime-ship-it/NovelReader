# Novel Reader

A modern, local-first desktop novel reader built with **PySide6**. It supports importing local `.txt` files, smart chapter detection, per-chapter reading, reading-progress tracking, statistics, customizable keyboard shortcuts, multiple themes, and one-click packaging into a single Windows executable.

> Design inspired by [Koodo Reader](https://github.com/koodo-reader/koodo-reader) and [Legado](https://github.com/gedoor/legado).

> 🌐 **Language / 语言**：[English](README.md) · [简体中文](README-CN.md)

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick Start (from source)](#quick-start-from-source)
- [Default Shortcuts](#default-shortcuts)
- [Shelf Operations](#shelf-operations)
- [Project Layout](#project-layout)
- [Where Data Is Stored](#where-data-is-stored)
- [Building an EXE](#building-an-exe)
- [Author & Donations](#author--donations)
- [FAQ](#faq)

---

## Features

- 📚 **Local TXT import** — pick `.txt` files from disk; the same path is never imported twice
- 🧠 **Smart chapter detection** — recognises patterns like `第X章`, `Chapter N`, etc.
- 📖 **Chapter-level reading** — render the whole chapter, free-scroll inside it; pressing `PageDown` / `→` / `Space` at the end of a chapter jumps to the next one (and vice-versa)
- 🔖 **Bookmarks & progress** — all reading progress, bookmarks, and settings are persisted to SQLite and restored on the next launch
- 📊 **Reading statistics** — today's reading time / character count, totals, per-book progress
- 🎨 **Multiple themes** — light, dark, parchment, eye-care green; switch with one click in the reader toolbar
- ⌨️ **Fully customizable shortcuts** — bind up to 4 keys per action, edit them in **Settings → Shortcuts**, applied instantly
- 📦 **One-click packaging** — the bundled PyInstaller script produces a single `NovelReader.exe` in ~30 seconds

---

## Requirements

- Python **3.10+** (3.11 / 3.12 / 3.13 recommended)
- Windows / macOS / Linux (EXE packaging has only been tested on Windows)
- Dependencies: see [requirements.txt](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/requirements.txt)

```text
PySide6>=6.6.0
Pillow>=10.0.0
pyinstaller>=6.0.0
```

---

## Quick Start (from source)

```powershell
# 1) Install dependencies
pip install -r requirements.txt

# 2) Launch the app
python main.py
```

Once running:

1. Click **「➕ 导入书籍 / Import Books」** in the top-right of the main window to pick local `.txt` files (multi-select supported)
2. Click a card to open the reader
3. Use the reader toolbar to switch themes, open the table of contents, add bookmarks, or open settings
4. Press **Esc** to return to the shelf
5. Hover a card or right-click it to delete a book from the shelf

---

## Default Shortcuts

All bindings can be re-assigned in **Settings → Shortcuts**.

| Action | Default keys |
| --- | --- |
| Next chapter / page-down at chapter end | `→` / `PageDown` / `Space` |
| Previous chapter / page-up at chapter start | `←` / `PageUp` |
| Force next chapter | `Ctrl+→` / `]` |
| Force previous chapter | `Ctrl+←` / `[` |
| Back to shelf | `Esc` |
| Show / hide table of contents | `Ctrl+B` |
| Add bookmark | `Ctrl+D` |
| Cycle theme | `Ctrl+T` |
| Increase / decrease font size | `Ctrl+=` / `Ctrl+-` |
| Open settings | `Ctrl+,` |

> When `PageDown` / `→` / `Space` is pressed inside a chapter, the view first scrolls; once you reach the bottom, the same key jumps to the next chapter.

---

## Shelf Operations

### Import
Click **「➕ 导入书籍 / Import Books」** in the top-right, or use the menu `File → Import Books` / `Ctrl+O`.

### Delete
Two entry points:

- **Hover** the card — the ✕ button in the top-right turns red, click to delete
- **Right-click** the card — pick `🗑 从书架删除 / Remove from shelf`

A confirmation dialog appears before any deletion, reminding you that:

> Only the shelf record and the program's generated cover cache are removed; the original file is left untouched.

---

## Project Layout

```text
novel-reader/
├── app/                          # Application source
│   ├── config.py                 # Paths / settings / default shortcuts
│   ├── controllers/              # Business logic
│   │   └── library_controller.py
│   ├── models/                   # Data models + SQLite
│   │   ├── book.py
│   │   └── database.py
│   ├── resources/                # Resources (themes / QSS)
│   │   ├── styles/style.qss
│   │   └── themes.py
│   ├── utils/                    # Utilities
│   │   ├── book_parser.py        #   Chapter parsing
│   │   └── cover_generator.py    #   Cover generation
│   ├── views/                    # View layer
│   │   ├── about_dialog.py       #   About + donations
│   │   ├── main_window.py
│   │   ├── reader_view.py
│   │   ├── settings_dialog.py
│   │   └── statistics_dialog.py
│   └── widgets/                  # Custom widgets
│       ├── book_card.py
│       └── book_grid.py
├── erweima/                      # Donation QR codes (bundled into the EXE)
│   ├── usdt-erc20.jpg
│   ├── usdt-tr20.jpg
│   └── xmr.jpg
├── main.py                       # Application entry point
├── build.py                      # One-click packaging script
├── novel_reader.spec             # PyInstaller spec
├── README.md                     # English documentation (this file)
├── README-CN.md                  # 简体中文文档
└── requirements.txt
```

---

## Where Data Is Stored

The packaged executable keeps user data inside the OS user directory — the install location is never touched.

| OS | User data location |
| --- | --- |
| Windows | `%APPDATA%\NovelReader\`<br/>i.e. `C:\Users\<you>\AppData\Roaming\NovelReader\` |
| macOS | `~/Library/Application Support/NovelReader/` |
| Linux | `$XDG_DATA_HOME/NovelReader/` or `~/.local/share/NovelReader/` |

Sub-folders:

```text
NovelReader/
├── library.db       # SQLite database (books / progress / bookmarks / settings)
├── covers/          # Cached cover images
└── logs/            # Logs
```

When running from source, data is written to `data/` under the project root for a friendlier dev experience.

---

## Building an EXE

The project ships with a PyInstaller configuration. Common commands:

```powershell
# Default: single-file release (output: dist/NovelReader.exe)
python build.py

# Directory mode (faster startup, multiple files)
python build.py --onedir

# Debug mode (console + verbose logs)
python build.py --debug

# Skip cleaning (incremental build)
python build.py --no-clean
```

See [novel_reader.spec](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/novel_reader.spec) for the packaging config:
- Bundles `app/resources/styles/style.qss` and `erweima/` (donation QRs)
- Excludes unused Qt submodules (`QtNetwork`, `QtWebEngine*`, `QtMultimedia`, …) to reduce size
- UPX compression is enabled by default; output is about 50 MB

Run the built executable directly:

```powershell
.\dist\NovelReader.exe
```

---

## Author & Donations

In the app, click **「ℹ 关于 / About」** in the sidebar or use the menu `Help → About` to open the About dialog.

**Author**

- Name: **Lorime**
- Email: lorime@126.com

**Donations**

If this tool is useful to you, feel free to support its development with a donation:

| Coin | Address |
| --- | --- |
| XMR | `4DSQMNzzq46N1z2pZWAVdeA6JvUL9TCB2bnBiA3ZzoqEdYJnMydt5akCa3vtmapeDsbVKGPFdNkzzqTcJS8M8oyK7WGj5qMvNZRw61w6wMF` |
| USDT (TRC20) | `TG6DCBoQszDxc64owRZKkSHqZfcAQrqR8uM` |
| USDT (ERC20) | `0x4323d39BA9b6Bd0570920e63a8D3a192b4459330` |

The About dialog includes QR codes for each wallet (sourced from the `erweima/` directory); you can also copy the addresses directly.

> To replace or add a QR code, drop a same-name `.jpg` / `.png` into `erweima/` and re-run `python build.py`.

---

## FAQ

**Q1: I can't find the import button after launch.**
A: The **「➕ 导入书籍 / Import Books」** button lives in the top-right of the main window. You can also use the menu `File → Import Books` or `Ctrl+O`.

**Q2: Can I delete books from the shelf?**
A: Yes, two ways:
- Hover the card → the ✕ button in the top-right
- Right-click the card → pick `Remove from shelf` from the menu

Only the shelf record and the program's generated cover cache are removed; the original file is kept. To reset everything, manually delete `%APPDATA%\NovelReader\library.db`.

**Q3: My custom shortcut doesn't work.**
A: Some combinations (e.g. `Ctrl+Alt+Del`) are reserved by the OS — pick another one. Changes take effect immediately; no restart required.

**Q4: The packaged EXE is too large.**
A: Most of the ~50 MB is PySide6. You can trim it further by editing the `excludes` list in `novel_reader.spec`, or use `python build.py --onedir` plus `nuitka` for additional optimizations.

**Q5: My donation QR isn't showing.**
A: Make sure `xmr.jpg`, `usdt-tr20.jpg`, and `usdt-erc20.jpg` exist in `erweima/`. The images are bundled into the EXE; if you renamed them, also update `DONATION_QR_FILES` in [app/config.py](file:///c:/Users/lorime/Documents/trae_projects/novel-reader/app/config.py).

---

## Translations

This repository ships with documentation in multiple languages:

- 🇬🇧 English: [README.md](README.md)
- 🇨🇳 简体中文: [README-CN.md](README-CN.md)

Contributions for additional languages are welcome — just open a pull request with a `README-<lang>.md` and add it to the list above.
