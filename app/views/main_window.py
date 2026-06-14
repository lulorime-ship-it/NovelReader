"""主窗口 - 三栏布局：侧边栏 + 书架 + 阅读视图"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QLabel, QLineEdit, QFileDialog, QMessageBox, QStackedWidget, QStatusBar,
    QButtonGroup, QMenu, QApplication
)

from ..config import (
    DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, DEFAULT_SETTINGS, DEFAULT_SHORTCUTS,
    COVER_DIR, app_resource_path
)
from ..models import Database
from ..controllers import LibraryController
from ..resources.themes import THEMES, get_theme_qss
from .reader_view import ReaderView
from .settings_dialog import SettingsDialog
from .statistics_dialog import StatisticsDialog
from .about_dialog import AboutDialog
from ..widgets import BookGridView


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self, db: Database, controller: LibraryController):
        super().__init__()
        self.db = db
        self.controller = controller

        # 加载设置
        self.settings = self._load_settings()

        self.setWindowTitle("小说阅读器")
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)

        self._build_ui()
        self._build_menu()
        self._build_shortcuts()
        self._load_base_style()
        self.apply_theme(self.settings.get("theme", "light"))

        # 加载书籍
        self.refresh_library()
        self._update_status_bar()

    # ---------- UI 构建 ----------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. 侧边栏
        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        # 2. 主体区域（顶栏 + 内容堆叠）
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶栏
        self.topbar = self._build_topbar()
        main_layout.addWidget(self.topbar)

        # 内容堆叠
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        # 书架视图
        self.book_grid = BookGridView()
        self.book_grid.book_opened.connect(self._open_book)
        self.book_grid.book_deleted.connect(self._delete_book)
        self.stack.addWidget(self.book_grid)

        # 阅读视图
        self.reader_view = ReaderView(self.db)
        self.reader_view.book_closed.connect(self._show_library)
        self.reader_view.open_settings_requested.connect(self._show_settings)
        self.stack.addWidget(self.reader_view)

        root.addWidget(main_area, 1)

        # 状态栏
        self.setStatusBar(QStatusBar())

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # 标题
        title = QLabel("📚 小说阅读器")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        subtitle = QLabel("享受沉浸式阅读")
        subtitle.setObjectName("sidebarSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # 导航按钮
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("🏠  我的书架", "library"),
            ("⭐  收藏夹", "favorites"),
            ("📖  最近阅读", "recent"),
            ("📊  阅读统计", "stats"),
        ]
        for text, key in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setProperty("nav_key", key)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_clicked(k))
            self.nav_group.addButton(btn)
            layout.addWidget(btn)

        # 默认选中
        self.nav_group.buttons()[0].setChecked(True)

        layout.addStretch()

        # 设置按钮
        settings_btn = QPushButton("⚙  设置")
        settings_btn.setObjectName("navButton")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        about_btn = QPushButton("ℹ  关于")
        about_btn.setObjectName("navButton")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(self._show_about)
        layout.addWidget(about_btn)

        return sidebar

    def _build_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(60)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("🔍 搜索书名或作者...")
        self.search_box.setFixedWidth(320)
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)

        layout.addStretch()

        # 统计按钮
        stats_btn = QPushButton("📊 统计")
        stats_btn.setObjectName("iconButton")
        stats_btn.setToolTip("阅读统计")
        stats_btn.clicked.connect(self._show_statistics)
        layout.addWidget(stats_btn)

        # 设置按钮
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.setObjectName("iconButton")
        settings_btn.setToolTip("阅读设置")
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        # 导入按钮
        import_btn = QPushButton("➕ 导入书籍")
        import_btn.setObjectName("primaryButton")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self._import_books)
        layout.addWidget(import_btn)

        return topbar

    def _build_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()

        # 文件
        file_menu = menubar.addMenu("文件(&F)")
        import_action = QAction("导入书籍(&I)", self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self._import_books)
        file_menu.addAction(import_action)

        file_menu.addSeparator()
        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 视图
        view_menu = menubar.addMenu("视图(&V)")
        library_action = QAction("我的书架(&L)", self)
        library_action.setShortcut("Ctrl+1")
        library_action.triggered.connect(self._show_library)
        view_menu.addAction(library_action)

        # 工具
        tool_menu = menubar.addMenu("工具(&T)")
        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        tool_menu.addAction(settings_action)

        stats_action = QAction("阅读统计(&T)", self)
        stats_action.setShortcut("Ctrl+I")
        stats_action.triggered.connect(self._show_statistics)
        tool_menu.addAction(stats_action)

        # 帮助
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_shortcuts(self):
        """全局快捷键 - 多数键盘操作由阅读视图内部按动作表处理
        这里只保留主窗口级别的兜底快捷键（例如 Esc 退出阅读）"""
        # 注意：Esc 行为由 reader_view 通过其动作表自行处理（默认绑定为 back）
        pass

    # ---------- 主题样式 ----------
    def _load_base_style(self):
        qss_path = app_resource_path("app", "resources", "styles", "style.qss")
        if qss_path.exists():
            self.base_qss = qss_path.read_text(encoding="utf-8")
        else:
            self.base_qss = ""

    def apply_theme(self, theme_key: str):
        self.settings["theme"] = theme_key
        self.db.set_setting("theme", theme_key)
        full_qss = get_theme_qss(theme_key, self.base_qss)
        self.setStyleSheet(full_qss)
        if hasattr(self, "reader_view"):
            self.reader_view.apply_theme(theme_key)

    # ---------- 设置读写 ----------
    def _load_settings(self) -> dict:
        import json
        s = dict(DEFAULT_SETTINGS)
        # 默认快捷键
        s["shortcuts"] = dict(DEFAULT_SHORTCUTS)
        db_settings = self.db.get_all_settings()
        for k, v in db_settings.items():
            if k == "shortcuts":
                # 快捷键以 JSON 形式持久化
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, dict):
                        s["shortcuts"] = parsed
                except (TypeError, ValueError, json.JSONDecodeError):
                    pass
            elif k in ("font_size", "page_margin"):
                try:
                    s[k] = int(v)
                except (TypeError, ValueError):
                    pass
            elif k == "line_height":
                try:
                    s[k] = float(v)
                except (TypeError, ValueError):
                    pass
            else:
                s[k] = v
        return s

    def _save_settings(self):
        import json
        for k, v in self.settings.items():
            if k == "shortcuts":
                # 序列化为 JSON
                self.db.set_setting(k, json.dumps(v, ensure_ascii=False))
            else:
                self.db.set_setting(k, str(v))

    # ---------- 业务动作 ----------
    def refresh_library(self):
        books = self.controller.get_all_books()
        # 应用搜索过滤
        keyword = self.search_box.text().strip().lower()
        if keyword:
            books = [b for b in books
                     if keyword in b.title.lower() or keyword in b.author.lower()]
        # 应用导航过滤
        nav_key = self._get_current_nav_key()
        if nav_key == "favorites":
            books = [b for b in books if b.is_favorite]
        elif nav_key == "recent":
            books = [b for b in books if b.last_read_at][:20]

        self.book_grid.set_books(books)
        self._update_status_bar()

    def _get_current_nav_key(self) -> Optional[str]:
        btn = self.nav_group.checkedButton()
        return btn.property("nav_key") if btn else None

    def _on_nav_clicked(self, key: str):
        if key == "stats":
            self._show_statistics()
            # 取消选中，让“统计”保持非激活
            self.nav_group.setExclusive(False)
            for btn in self.nav_group.buttons():
                if btn.property("nav_key") != "library":
                    btn.setChecked(False)
            self.nav_group.buttons()[0].setChecked(True)
            self.nav_group.setExclusive(True)
        else:
            self._show_library()
            self.refresh_library()

    def _on_search(self, text: str):
        self.refresh_library()

    def _import_books(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择小说文件",
            str(Path.home()),
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if not files:
            return
        success = 0
        failed = []
        for f in files:
            try:
                book = self.controller.import_book(f)
                if book:
                    success += 1
            except Exception as e:
                failed.append((f, str(e)))

        self.refresh_library()
        msg = f"成功导入 {success} 本书籍"
        if failed:
            msg += f"\n失败 {len(failed)} 本：\n" + "\n".join(
                [f"• {Path(f).name}: {e}" for f, e in failed[:5]]
            )
        QMessageBox.information(self, "导入完成", msg)

    def _open_book(self, book_id: int):
        self.reader_view.open_book(book_id)
        self.reader_view.apply_settings(self.settings)
        self.stack.setCurrentIndex(1)

    def _delete_book(self, book_id: int):
        """从书架删除书籍（弹出确认对话框）"""
        book = self.controller.get_book(book_id)
        if not book:
            return
        # 二次确认
        reply = QMessageBox.question(
            self,
            "从书架删除",
            f"确定要把《{book.title}》从书架中移除吗？\n\n"
            f"提示：仅删除书架记录与本程序生成的封面缓存，\n"
            f"原文件不会被删除。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.controller.remove_book(book_id)
        except Exception as e:
            QMessageBox.critical(self, "删除失败", f"删除时发生错误：\n{e}")
            return
        self.refresh_library()
        self.statusBar().showMessage(f"已从书架移除《{book.title}》", 3000)

    def _show_library(self):
        self.stack.setCurrentIndex(0)
        self.refresh_library()

    def _show_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self, new_settings: dict):
        self.settings.update(new_settings)
        self._save_settings()
        self.apply_theme(new_settings.get("theme", "light"))
        if self.stack.currentIndex() == 1:
            self.reader_view.apply_settings(self.settings)

    def _show_statistics(self):
        dlg = StatisticsDialog(self.db, self)
        dlg.exec()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _update_status_bar(self):
        books = self.controller.get_all_books()
        total_chars = sum(b.total_chars for b in books)
        read_chars = sum(b.total_chars * b.progress for b in books)
        progress = int(read_chars / total_chars * 100) if total_chars else 0
        self.statusBar().showMessage(
            f"📚 书架: {len(books)} 本  |  总字数: {total_chars:,}  |  已读: {progress}%"
        )

    # ---------- 关闭事件 ----------
    def closeEvent(self, event):
        # 保存所有设置
        self._save_settings()
        # 关闭当前阅读会话
        if self.stack.currentIndex() == 1:
            self.reader_view.close_book()
        event.accept()
