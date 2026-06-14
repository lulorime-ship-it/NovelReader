# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 小说阅读器

生成方式（在项目根目录执行）：
    pyinstaller novel_reader.spec --clean --noconfirm

或通过 build.py 封装：
    python build.py
"""
import os
from pathlib import Path

block_cipher = None

# 项目根目录
PROJECT_ROOT = Path(os.path.abspath(SPECPATH))  # SPECPATH 由 PyInstaller 注入

# ========== 数据文件（QSS、主题、捐赠二维码等只读资源） ==========
# 这些文件需要打包到 _MEIPASS 内，运行时由 app_resource_path() 解析
datas = [
    (str(PROJECT_ROOT / "app" / "resources" / "styles" / "style.qss"),
     "app/resources/styles"),
    (str(PROJECT_ROOT / "erweima"),
     "erweima"),
]

# ========== 隐式导入（PySide6 子模块按需补全） ==========
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtPrintSupport",
    "sqlite3",
    "app.views.shortcut_keys",
    "app.views.about_dialog",
]

# ========== 排除的模块（减小体积） ==========
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "PySide6.QtNetwork",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtXml",
]

# ========== 可选应用图标 ==========
ICON_PATH = PROJECT_ROOT / "assets" / "icon.ico"
icon = str(ICON_PATH) if ICON_PATH.exists() else None

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NovelReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # GUI 程序，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
