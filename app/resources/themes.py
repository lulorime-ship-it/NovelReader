"""阅读主题色板 - 运行时动态生成 QSS 片段"""
from dataclasses import dataclass


@dataclass
class ThemePreset:
    name: str
    bg: str
    sidebar: str
    reader_bg: str
    reader_text: str
    reader_secondary: str
    accent: str
    border: str
    text_primary: str
    text_secondary: str


THEMES = {
    "light": ThemePreset(
        name="明亮",
        bg="#f5f6fa", sidebar="#ffffff",
        reader_bg="#fafafa", reader_text="#2c3e50", reader_secondary="#64748b",
        accent="#6366f1", border="#e4e7ed",
        text_primary="#1e293b", text_secondary="#475569",
    ),
    "dark": ThemePreset(
        name="暗黑",
        bg="#1a1d23", sidebar="#22262e",
        reader_bg="#15171c", reader_text="#d4d8de", reader_secondary="#8a93a0",
        accent="#818cf8", border="#2d3340",
        text_primary="#e2e8f0", text_secondary="#a0a8b5",
    ),
    "sepia": ThemePreset(
        name="羊皮纸",
        bg="#f4ecd8", sidebar="#ebe0c6",
        reader_bg="#f7efd8", reader_text="#5b4636", reader_secondary="#8a6f4e",
        accent="#a0522d", border="#d8c9a7",
        text_primary="#3d2e1f", text_secondary="#6b5236",
    ),
    "green": ThemePreset(
        name="护眼绿",
        bg="#e8efe0", sidebar="#dfe9d3",
        reader_bg="#dfead0", reader_text="#3a4a32", reader_secondary="#6e7a60",
        accent="#5a7a3a", border="#c5d3b3",
        text_primary="#2a3525", text_secondary="#566b48",
    ),
    "eye_care": ThemePreset(
        name="护眼",
        bg="#d6e1c5", sidebar="#cdd9b5",
        reader_bg="#c9d7a3", reader_text="#3a3a2a", reader_secondary="#6e6e5a",
        accent="#6a8454", border="#b4c499",
        text_primary="#2c2c20", text_secondary="#585848",
    ),
}


def get_theme_qss(theme_key: str, base_qss: str) -> str:
    """根据主题动态生成完整 QSS"""
    theme = THEMES.get(theme_key, THEMES["light"])

    extra = f"""
    /* === 动态主题: {theme.name} === */
    QMainWindow, QWidget {{
        background-color: {theme.bg};
        color: {theme.text_primary};
    }}

    QFrame#sidebar {{
        background-color: {theme.sidebar};
        border-right: 1px solid {theme.border};
    }}

    QPushButton#navButton {{
        color: {theme.text_secondary};
    }}
    QPushButton#navButton:hover {{
        background-color: {theme.bg};
        color: {theme.text_primary};
    }}
    QPushButton#navButton:checked {{
        background-color: {theme.accent}22;
        color: {theme.accent};
    }}

    QLabel#sidebarTitle {{
        color: {theme.text_primary};
    }}
    QLabel#sidebarSubtitle {{
        color: {theme.text_secondary};
    }}

    QFrame#topbar {{
        background-color: {theme.sidebar};
        border-bottom: 1px solid {theme.border};
    }}

    QLineEdit#searchBox {{
        background-color: {theme.bg};
        color: {theme.text_primary};
    }}
    QLineEdit#searchBox:focus {{
        background-color: {theme.sidebar};
        border: 1px solid {theme.accent};
    }}

    QPushButton#iconButton {{
        color: {theme.text_secondary};
    }}
    QPushButton#iconButton:hover {{
        background-color: {theme.bg};
        color: {theme.text_primary};
    }}

    QPushButton#primaryButton {{
        background-color: {theme.accent};
    }}
    QPushButton#primaryButton:hover {{
        background-color: {theme.accent}dd;
    }}

    QFrame#bookCard {{
        background-color: {theme.sidebar};
        border: 1px solid {theme.border};
    }}
    QFrame#bookCard:hover {{
        border: 1px solid {theme.accent};
    }}

    QLabel#bookTitle {{
        color: {theme.text_primary};
    }}
    QLabel#bookAuthor {{
        color: {theme.text_secondary};
    }}
    QLabel#bookProgress {{
        color: {theme.accent};
    }}

    QProgressBar#bookProgressBar {{
        background-color: {theme.bg};
    }}
    QProgressBar#bookProgressBar::chunk {{
        background-color: {theme.accent};
    }}

    QFrame#readerArea {{
        background-color: {theme.reader_bg};
    }}

    QTextBrowser#readerText {{
        background-color: transparent;
        color: {theme.reader_text};
    }}

    QFrame#readerToolbar, QFrame#readerBottomBar {{
        background-color: {theme.sidebar};
    }}

    QSlider#readerSlider::groove:horizontal {{
        background: {theme.border};
    }}
    QSlider#readerSlider::handle:horizontal {{
        background: {theme.accent};
    }}
    QSlider#readerSlider::sub-page:horizontal {{
        background: {theme.accent};
    }}

    QListWidget#chapterList {{
        background-color: {theme.sidebar};
        color: {theme.text_primary};
    }}
    QListWidget#chapterList::item {{
        border-bottom: 1px solid {theme.border};
        color: {theme.text_secondary};
    }}
    QListWidget#chapterList::item:hover {{
        background-color: {theme.bg};
    }}
    QListWidget#chapterList::item:selected {{
        background-color: {theme.accent}22;
        color: {theme.accent};
    }}

    QPushButton#themeChip {{
        background-color: {theme.bg};
        color: {theme.text_secondary};
    }}
    QPushButton#themeChip:checked {{
        background-color: {theme.accent}22;
        border: 2px solid {theme.accent};
        color: {theme.accent};
    }}

    QStatusBar {{
        background-color: {theme.sidebar};
        color: {theme.text_secondary};
        border-top: 1px solid {theme.border};
    }}

    QLabel#emptyTitle {{ color: {theme.text_secondary}; }}
    QLabel#emptySubtitle {{ color: {theme.text_secondary}; opacity: 0.6; }}
    """

    return base_qss + extra
