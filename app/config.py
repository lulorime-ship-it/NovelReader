"""应用配置常量"""
import os
import sys
from pathlib import Path


def _is_frozen() -> bool:
    """是否运行在 PyInstaller 打包后的可执行文件中"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def app_resource_path(*parts: str) -> Path:
    """获取应用资源（QSS、主题、捐赠二维码等只读资源）的绝对路径

    - 源码运行：项目根目录
    - PyInstaller 打包：从 sys._MEIPASS 取出
    """
    if _is_frozen():
        return Path(sys._MEIPASS).joinpath(*parts)
    return ROOT_DIR.joinpath(*parts)


def donation_qr_path(filename: str) -> Path:
    """获取捐赠二维码图片的运行时绝对路径

    - 源码运行：项目根目录/erweima/<filename>
    - PyInstaller 打包：_MEIPASS/erweima/<filename>
      （由 novel_reader.spec 注入，源目录为项目根的 erweima/）
    """
    return app_resource_path("erweima", filename)


def user_data_path(*parts: str) -> Path:
    """获取用户数据（DB、封面、日志等可写数据）的绝对路径

    - Windows: %APPDATA%/NovelReader/
    - macOS:   ~/Library/Application Support/NovelReader/
    - Linux:   $XDG_DATA_HOME/NovelReader/ 或 ~/.local/share/NovelReader/
    - 兜底: 项目根目录下的 data/
    """
    if _is_frozen():
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / "NovelReader"
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / "NovelReader"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME",
                                       str(Path.home() / ".local" / "share"))) / "NovelReader"
        base = base.joinpath(*parts)
        base.parent.mkdir(parents=True, exist_ok=True)
        return base
    # 源码运行：保留旧行为，方便开发
    return (Path(__file__).parent.parent / "data").joinpath(*parts)


# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
APP_DIR = ROOT_DIR / "app"
RESOURCES_DIR = ROOT_DIR / "app" / "resources"

# 捐赠二维码目录（项目根目录下的 erweima/，打包时由 spec 注入到 _MEIPASS）
ERWEIMA_DIR = ROOT_DIR / "erweima"
# 各钱包二维码文件名
DONATION_QR_FILES = {
    "XMR":           "xmr.jpg",
    "USDT (TRC20)":  "usdt-tr20.jpg",
    "USDT (ERC20)":  "usdt-erc20.jpg",
}

# 作者与捐献信息（关于对话框展示用）
AUTHOR_NAME = "Lorime"
AUTHOR_EMAIL = "lorime@126.com"
DONATION_ADDRESSES = {
    "XMR":          "4DSQMNzzq46N1z2pZWAVdeA6JvUL9TCB2bnBiA3ZzoqEdYJnMydt5akCa3vtmapeDsbVKGPFdNkzzqTcJS8M8oyK7WGj5qMvNZRw61w6wMF",
    "USDT (TRC20)": "TG6DCBoQszDxc64owRZKkSHqZfcAQrqR8uM",
    "USDT (ERC20)": "0x4323d39BA9b6Bd0570920e63a8D3a192b4459330",
}

# 用户数据目录（首次运行时创建）
USER_DATA_DIR = user_data_path(".")
DB_PATH = user_data_path("library.db")
COVER_DIR = user_data_path("covers")
LOG_DIR = user_data_path("logs")

# 窗口默认尺寸
DEFAULT_WINDOW_SIZE = (1280, 800)
MIN_WINDOW_SIZE = (960, 600)

# 阅读器设置默认值
DEFAULT_SETTINGS = {
    "font_family": "Microsoft YaHei",
    "font_size": 18,
    "line_height": 1.6,
    "page_margin": 40,
    "theme": "light",  # light / dark / sepia / green
    "page_transition": "slide",  # slide / fade / none
}

# 快捷键默认值 - 每个动作支持多个键位绑定
# 键名使用 Qt 标准名称：Right / Left / PageDown / PageUp / Space / Escape /
# Home / End / Ctrl+字母 / Shift+字母 / F1-F12 / 标点符号等
DEFAULT_SHORTCUTS = {
    "next_page":         ["Right", "PageDown", "Space"],
    "prev_page":         ["Left", "PageUp"],
    "next_chapter":      ["Ctrl+Right", "]"],
    "prev_chapter":      ["Ctrl+Left", "["],
    "back":              ["Escape"],
    "toggle_chapter":    ["Ctrl+B"],
    "add_bookmark":      ["Ctrl+D"],
    "cycle_theme":       ["Ctrl+T"],
    "font_size_up":      ["Ctrl+="],
    "font_size_down":    ["Ctrl+-"],
    "toggle_settings":   ["Ctrl+,"],
}

# 快捷键动作元信息 - 用于在 UI 中显示
SHORTCUT_ACTIONS = [
    ("next_page",       "下一页"),
    ("prev_page",       "上一页"),
    ("next_chapter",    "下一章"),
    ("prev_chapter",    "上一章"),
    ("back",            "返回书架"),
    ("toggle_chapter",  "显示/隐藏目录"),
    ("add_bookmark",    "添加书签"),
    ("cycle_theme",     "切换主题"),
    ("font_size_up",    "增大字号"),
    ("font_size_down",  "减小字号"),
    ("toggle_settings", "打开设置"),
]

# 主题列表
THEMES = ["light", "dark", "sepia", "green", "eye_care"]

# 支持的书籍文件扩展名
SUPPORTED_EXTENSIONS = [".txt"]
