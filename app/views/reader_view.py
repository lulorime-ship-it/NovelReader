"""阅读视图 - 按章节阅读，章节内自由滚动，滚到边界自动跳转章节"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QTextBrowser, QLabel, QPushButton,
    QSlider, QListWidget, QListWidgetItem, QSplitter, QWidget, QInputDialog,
    QMessageBox
)

from ..config import DEFAULT_SHORTCUTS
from ..models.book import Book, Bookmark
from ..models.database import Database
from .shortcut_keys import parse_shortcut_int, parse_shortcut_string


class ReaderView(QWidget):
    """阅读视图

    阅读模式：按章节分章，每次只显示整章内容
    - 章节内通过 QTextBrowser 自带的滚动条自由滚动
    - 滚动到章节末尾时再次按 PageDown / → / Space 自动进入下一章
    - 滚动到章节起始时按 PageUp / ← 自动进入上一章
    - Ctrl+→ / Ctrl+← / ] / [ 始终强制跳转章节
    """
    book_closed = Signal()
    progress_updated = Signal(int, int, int)  # book_id, chapter_index, position
    open_settings_requested = Signal()

    # 滚到底部时允许的容差（像素），避免鼠标点击位置导致的误判
    BOTTOM_THRESHOLD = 4
    # 滚到顶部时严格判 0，但留 1px 容差
    TOP_THRESHOLD = 1

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_book: Optional[Book] = None
        self.current_content: str = ""
        self.current_chapter_index = 0
        self.session_chars_read = 0
        self.session_start = None

        # 阅读设置
        self.font_family = "Microsoft YaHei"
        self.font_size = 18
        self.line_height = 1.6
        self.theme = "light"
        self.page_margin = 40

        # 快捷键：动作名 -> 已解析的 QKeySequence 列表（用于比对）
        self.shortcut_sequences: dict[str, list[QKeySequence]] = {}
        self.set_shortcuts(DEFAULT_SHORTCUTS)

        # 自动保存计时器
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setInterval(5000)  # 5 秒
        self._auto_save_timer.timeout.connect(self._auto_save_progress)

        self._build_ui()
        self.apply_theme("light")

        # 在子控件上安装事件过滤器，拦截键盘事件
        # Qt 默认把按键事件发给有焦点的子控件；QTextBrowser 自身会处理
        # PageDown/PageUp/方向键（accept 掉），导致父 ReaderView 永远收不到。
        # 过滤器策略：按键先过 reader_view 的匹配表，命中则 reader 处理并 consume；
        # 未命中才放行给子控件。
        # 注意：_render_chapter() 中也会重新调用，因为 setHtml() 会重置 text_browser
        # 内部子控件。
        self._install_event_filter()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 顶栏
        self.topbar = QFrame()
        self.topbar.setObjectName("readerToolbar")
        self.topbar.setFixedHeight(56)
        top_layout = QHBoxLayout(self.topbar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self.back_btn = QPushButton("← 返回书架")
        self.back_btn.setObjectName("iconButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self._on_back_clicked)
        top_layout.addWidget(self.back_btn)

        self.title_label = QLabel("未打开书籍")
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        top_layout.addWidget(self.title_label, 1)

        self.font_dec_btn = QPushButton("A-")
        self.font_dec_btn.setObjectName("iconButton")
        self.font_dec_btn.clicked.connect(lambda: self._change_font_size(-1))
        top_layout.addWidget(self.font_dec_btn)

        self.font_inc_btn = QPushButton("A+")
        self.font_inc_btn.setObjectName("iconButton")
        self.font_inc_btn.clicked.connect(lambda: self._change_font_size(1))
        top_layout.addWidget(self.font_inc_btn)

        self.theme_btn = QPushButton("🌗 主题")
        self.theme_btn.setObjectName("iconButton")
        self.theme_btn.clicked.connect(self._cycle_theme)
        top_layout.addWidget(self.theme_btn)

        self.bookmark_btn = QPushButton("🔖 书签")
        self.bookmark_btn.setObjectName("iconButton")
        self.bookmark_btn.clicked.connect(self._add_bookmark)
        top_layout.addWidget(self.bookmark_btn)

        self.chapter_toggle_btn = QPushButton("☰ 目录")
        self.chapter_toggle_btn.setObjectName("iconButton")
        self.chapter_toggle_btn.clicked.connect(self._toggle_chapter_panel)
        top_layout.addWidget(self.chapter_toggle_btn)

        outer.addWidget(self.topbar)

        # 主体 - 章节列表 + 阅读区
        self.splitter = QSplitter(Qt.Horizontal)

        # 章节面板
        self.chapter_panel = QFrame()
        self.chapter_panel.setFixedWidth(260)
        cp_layout = QVBoxLayout(self.chapter_panel)
        cp_layout.setContentsMargins(0, 0, 0, 0)
        cp_layout.setSpacing(0)

        cp_title = QLabel("📖 目录")
        cp_title.setStyleSheet(
            "font-weight: 700; font-size: 14px; padding: 14px 16px;"
            "border-bottom: 1px solid #e4e7ed;"
        )
        cp_layout.addWidget(cp_title)

        self.chapter_list = QListWidget()
        self.chapter_list.setObjectName("chapterList")
        self.chapter_list.currentRowChanged.connect(self._on_chapter_changed)
        cp_layout.addWidget(self.chapter_list, 1)

        self.splitter.addWidget(self.chapter_panel)

        # 阅读区
        self.reader_area = QFrame()
        self.reader_area.setObjectName("readerArea")
        ra_layout = QVBoxLayout(self.reader_area)
        ra_layout.setContentsMargins(0, 0, 0, 0)
        ra_layout.setSpacing(0)

        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("readerText")
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_browser.anchorClicked.connect(self._on_anchor_clicked)
        # 滚动到位置时记录，用于进度估算
        self.text_browser.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        ra_layout.addWidget(self.text_browser, 1)

        # 底栏：上一章 / 章节指示 / 进度滑块 / 下一章
        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName("readerBottomBar")
        self.bottom_bar.setFixedHeight(64)
        bb_layout = QHBoxLayout(self.bottom_bar)
        bb_layout.setContentsMargins(24, 0, 24, 0)
        bb_layout.setSpacing(12)

        self.prev_btn = QPushButton("◀ 上一章")
        self.prev_btn.setObjectName("iconButton")
        self.prev_btn.clicked.connect(self._prev_chapter)
        bb_layout.addWidget(self.prev_btn)

        self.chapter_label = QLabel("— / —")
        self.chapter_label.setStyleSheet("color: #64748b; font-size: 12px; min-width: 110px;")
        self.chapter_label.setAlignment(Qt.AlignCenter)
        bb_layout.addWidget(self.chapter_label)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("readerSlider")
        self.progress_slider.setRange(0, 100)
        # 滑块只接受鼠标拖拽；键盘 PageUp/PageDown/方向键一律不上滑块，
        # 否则会拦截翻页快捷键，统一由 ReaderView.keyPressEvent 处理
        self.progress_slider.setFocusPolicy(Qt.NoFocus)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        bb_layout.addWidget(self.progress_slider, 1)

        self.next_btn = QPushButton("下一章 ▶")
        self.next_btn.setObjectName("iconButton")
        self.next_btn.clicked.connect(self._next_chapter)
        bb_layout.addWidget(self.next_btn)

        ra_layout.addWidget(self.bottom_bar)

        self.splitter.addWidget(self.reader_area)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 1000])
        self.chapter_panel.setVisible(False)

        outer.addWidget(self.splitter, 1)

    # ---------- 公开接口 ----------
    def open_book(self, book_id: int):
        """打开书籍"""
        book = self.db.get_book(book_id)
        if not book:
            return
        self.current_book = book
        # clamp：避免上次会话保存的 current_chapter 越界（章节数变化时）
        total = len(book.chapters) if book.chapters else 0
        target = book.current_chapter or 0
        if total > 0:
            target = max(0, min(target, total - 1))
        else:
            target = 0
        self.current_chapter_index = target

        # 读取全文
        try:
            self.current_content = Path(book.file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.current_content = Path(book.file_path).read_text(encoding="gbk", errors="ignore")

        self.title_label.setText(f"{book.title} · {book.author}")

        # 填充章节列表
        self.chapter_list.clear()
        if book.chapters:
            for ch in book.chapters:
                self.chapter_list.addItem(QListWidgetItem(ch.title))
        else:
            self.chapter_list.addItem(QListWidgetItem(book.title))

        self.chapter_list.setCurrentRow(self.current_chapter_index)

        # 启动自动保存
        self._auto_save_timer.start()

        from datetime import datetime
        self.session_start = datetime.now()

    def close_book(self):
        """关闭当前书籍"""
        self._auto_save_progress()
        self._auto_save_timer.stop()
        self._record_reading_session()
        self.current_book = None
        self.current_content = ""
        self.chapter_list.clear()
        self.text_browser.clear()
        self.title_label.setText("未打开书籍")
        self.chapter_label.setText("— / —")

    def apply_settings(self, settings: dict):
        """应用阅读设置"""
        self.font_family = settings.get("font_family", self.font_family)
        self.font_size = int(settings.get("font_size", self.font_size))
        self.line_height = float(settings.get("line_height", self.line_height))
        self.page_margin = int(settings.get("page_margin", self.page_margin))
        self.theme = settings.get("theme", self.theme)
        # 同步快捷键：把用户 settings 里的值与 DEFAULT_SHORTCUTS 合并
        # 关键修复：旧版本持久化的 shortcuts 可能缺关键键
        # （QKeySequence 解析失败时整段丢失），合并后保证基础翻页
        # 永远可用。
        merged = dict(DEFAULT_SHORTCUTS)
        user_shortcuts = settings.get("shortcuts") or {}
        for action, keys in user_shortcuts.items():
            if keys:  # 只在用户明确给了非空键才覆盖
                merged[action] = list(keys)
        self.set_shortcuts(merged)
        self._update_text_style()
        self.apply_theme(self.theme)
        if self.current_book:
            self._render_chapter()

    def set_shortcuts(self, shortcuts: dict[str, list[str]]):
        """加载并解析快捷键配置（动作名 -> 键名列表）

        关键：不能用 QKeySequence("PageDown") 这种字符串形式构造，
        PySide6 中它返回空序列（toString()="")，导致 set_shortcuts
        静默丢弃所有键名，永远匹配不到真实 QKeyEvent。
        必须用 Qt.Key_* 常量（int）构造。
        """
        # 存储为 (action -> set of (mod_int, key_int))，匹配时直接比 int
        self.shortcut_keys: dict[str, set[tuple[int, int]]] = {}
        parse_failures: list[str] = []
        for action, keys in shortcuts.items():
            pairs = set()
            for k in keys:
                pair = parse_shortcut_int(k)
                if pair is None:
                    parse_failures.append(f"{action}/{k}")
                else:
                    pairs.add(pair)
            self.shortcut_keys[action] = pairs
        # 兼容旧字段（不再用，但保留以防外部访问）
        self.shortcut_sequences = self.shortcut_keys
        # 把 set_shortcuts 结果也写进日志，便于排查"快捷键表为空"的极端情况
        try:
            from app.config import user_data_path
            log_path = user_data_path() / "keyevent.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"--- set_shortcuts called ---\n")
                f.write(f"  parse_failures: {parse_failures}\n")
                for action, pairs in self.shortcut_keys.items():
                    f.write(f"  {action}: {sorted(pairs)}\n")
        except Exception:
            pass
        if self.current_book:
            self._render_chapter()

    def apply_theme(self, theme_key: str):
        """应用主题"""
        self.theme = theme_key
        from ..resources.themes import THEMES
        theme = THEMES.get(theme_key, THEMES["light"])
        self.reader_area.setStyleSheet(f"background-color: {theme.reader_bg};")
        self.text_browser.setStyleSheet(
            f"QTextBrowser#readerText {{"
            f"  background-color: {theme.reader_bg};"
            f"  color: {theme.reader_text};"
            f"  padding: {self.page_margin}px 60px;"
            f"}}"
        )

    # ---------- 章节加载与渲染 ----------
    def _on_chapter_changed(self, row: int):
        if row < 0 or not self.current_book:
            return
        self._auto_save_progress()
        self.current_chapter_index = row
        self.current_book.current_chapter = row
        self.current_book.current_position = self.current_book.chapters[row].start_pos
        self._render_chapter()
        self._update_slider()

    def _render_chapter(self):
        """将当前章节的完整内容渲染到 QTextBrowser"""
        if not self.current_book or not self.current_book.chapters:
            return
        chapter = self.current_book.chapters[self.current_chapter_index]
        start = chapter.start_pos
        end = chapter.end_pos
        chapter_text = self.current_content[start:end]

        # 章节首部居中标题 + 完整正文
        display = (
            f"<h2 style='text-align:center; color:#94a3b8; font-weight:600; "
            f"margin-bottom: 24px;'>{self._html_escape(chapter.title)}</h2>"
            f"<div style='line-height:{self.line_height};'>{self._html_escape(chapter_text)}</div>"
            f"<p style='text-align:center; color:#94a3b8; font-size:12px; margin-top:40px;'>"
            f"— 本章完 —</p>"
        )
        self.text_browser.setHtml(display)
        # 回到顶部（章节切换后从新章节开始读）
        cursor = self.text_browser.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.text_browser.setTextCursor(cursor)
        self.text_browser.verticalScrollBar().setValue(0)

        self._update_text_style()
        self._update_slider()
        self._update_chapter_label()
        # 把键盘焦点抢回正文区（避免滑块/按钮抢走后 PageUp/PageDown 失效）
        self.text_browser.setFocus(Qt.OtherFocusReason)
        # 关键：setHtml() 会重置 text_browser 内部子控件，
        # 之前装的 eventFilter 已经失效，必须重新安装。
        self._install_event_filter()

    def _install_event_filter(self):
        """在所有子控件上重新安装事件过滤器

        关键时点：_render_chapter() 调用 setHtml() 后，QTextBrowser
        内部会重建子控件（viewport、scrollbars、document 子节点等），
        这些新子控件没有 eventFilter。按页键会被它们默认 accept 掉，
        父 ReaderView 收不到事件 → 章节切不动。

        必须在 __init__ 末尾和每次 _render_chapter 之后各调一次。
        """
        for child in self.findChildren(QWidget):
            if child is self:
                continue
            child.installEventFilter(self)

    def _on_scroll_changed(self, value: int):
        """滚动条变化 - 用于估算阅读位置"""
        if not self.current_book or not self.current_book.chapters:
            return
        chapter = self.current_book.chapters[self.current_chapter_index]
        scrollbar = self.text_browser.verticalScrollBar()
        maximum = scrollbar.maximum()
        if maximum <= 0:
            # 章节内容短到不需要滚动
            ratio = 1.0
        else:
            ratio = min(1.0, max(0.0, value / maximum))
        chapter_len = max(1, chapter.end_pos - chapter.start_pos)
        approx_pos = chapter.start_pos + int(ratio * chapter_len)
        self.current_book.current_position = approx_pos

    def _html_escape(self, text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br/>"))

    def _update_text_style(self):
        """刷新字体设置"""
        font = QFont(self.font_family, self.font_size)
        self.text_browser.setFont(font)

    # ---------- 滚动状态判定 ----------
    def _is_at_top(self) -> bool:
        bar = self.text_browser.verticalScrollBar()
        return bar.value() <= self.TOP_THRESHOLD

    def _is_at_bottom(self) -> bool:
        """判断是否已经滚到"视觉底部"（再翻也翻不动）

        之所以不用 value + pageStep >= maximum：
        QTextBrowser 末尾常因 HTML 边距/空白段导致滚动条可移动范围
        大于实际可见内容。改用 "尝试滚动后值是否还能前进" 判定。
        """
        bar = self.text_browser.verticalScrollBar()
        if bar.maximum() <= 0:
            return True  # 短章节
        # 距离底部 ≤ 一屏 视为到底（一次翻页能多前进一步，但不会有新内容可见）
        if bar.value() >= bar.maximum() - self.BOTTOM_THRESHOLD:
            return True
        # 试探性前进一步：若被 clamp 回原值，说明已经到底
        trial = min(bar.value() + bar.pageStep(), bar.maximum())
        return trial == bar.value()

    # ---------- 滚动（边界时跳转章节） ----------
    def _scroll_forward(self):
        """PageDown / → / Space：先在章节内滚动；已到底则进入下一章"""
        if not self.current_book:
            return
        if self._is_at_bottom():
            self._next_chapter()
        else:
            # QTextBrowser 没有 pageDown()，直接控制 verticalScrollBar
            bar = self.text_browser.verticalScrollBar()
            new_value = bar.value() + bar.pageStep()
            bar.setValue(min(new_value, bar.maximum()))

    def _scroll_backward(self):
        """PageUp / ←：先在章节内滚动；已在顶则进入上一章"""
        if not self.current_book:
            return
        if self._is_at_top():
            self._prev_chapter()
        else:
            bar = self.text_browser.verticalScrollBar()
            new_value = bar.value() - bar.pageStep()
            bar.setValue(max(new_value, bar.minimum()))

    def _next_chapter(self):
        if not self.current_book or not self.current_book.chapters:
            return
        # 用 book.chapters 而不是 chapter_list.count()，避免 UI 列表与数据不同步
        if self.current_chapter_index < len(self.current_book.chapters) - 1:
            self.chapter_list.setCurrentRow(self.current_chapter_index + 1)

    def _prev_chapter(self):
        if not self.current_book or not self.current_book.chapters:
            return
        if self.current_chapter_index > 0:
            self.chapter_list.setCurrentRow(self.current_chapter_index - 1)

    def _on_anchor_clicked(self, url):
        """处理目录锚点点击（可扩展）"""
        pass

    def _on_slider_released(self):
        """滑块释放时跳转 - 通过总进度跳到目标章节"""
        if not self.current_book:
            return
        value = self.progress_slider.value() / 100.0
        total = self.current_book.total_chars or 1
        target_pos = int(value * total)

        # 找到对应章节
        target_chapter = 0
        for i, ch in enumerate(self.current_book.chapters):
            if ch.start_pos <= target_pos < ch.end_pos:
                target_chapter = i
                break
            if ch.end_pos <= target_pos:
                target_chapter = i

        self.chapter_list.setCurrentRow(target_chapter)

    # ---------- 标签栏 ----------
    def _toggle_chapter_panel(self):
        self.chapter_panel.setVisible(not self.chapter_panel.isVisible())

    def _change_font_size(self, delta: int):
        new_size = max(12, min(36, self.font_size + delta))
        if new_size == self.font_size:
            return
        self.font_size = new_size
        # 字号变化时记录当前滚动比例，重新渲染后尽量保持位置
        ratio_before = self._scroll_ratio()
        if self.current_book:
            self._render_chapter()
            if ratio_before is not None:
                self._set_scroll_ratio(ratio_before)
        self._update_text_style()

    def _scroll_ratio(self) -> Optional[float]:
        bar = self.text_browser.verticalScrollBar()
        if bar.maximum() <= 0:
            return None
        return bar.value() / bar.maximum()

    def _set_scroll_ratio(self, ratio: float):
        bar = self.text_browser.verticalScrollBar()
        target = int(bar.maximum() * max(0.0, min(1.0, ratio)))
        bar.setValue(target)

    def _cycle_theme(self):
        from ..resources.themes import THEMES
        keys = list(THEMES.keys())
        try:
            idx = keys.index(self.theme)
        except ValueError:
            idx = 0
        new_key = keys[(idx + 1) % len(keys)]
        self.apply_theme(new_key)
        from PySide6.QtWidgets import QToolTip
        QToolTip.showText(
            self.mapToGlobal(self.rect().center()),
            f"已切换到 {THEMES[new_key].name} 主题"
        )

    def _add_bookmark(self):
        if not self.current_book:
            return
        chapter = self.current_book.chapters[self.current_chapter_index]
        pos = self.current_book.current_position or chapter.start_pos
        note, ok = QInputDialog.getText(
            self, "添加书签", "备注（可选）:", text=chapter.title
        )
        if not ok:
            return
        bm = Bookmark(
            book_id=self.current_book.id,
            chapter_index=self.current_chapter_index,
            chapter_title=chapter.title,
            position=pos,
            note=note,
        )
        self.db.add_bookmark(bm)
        QMessageBox.information(self, "添加成功", f"已在「{chapter.title}」添加书签")

    # ---------- 进度 ----------
    def _update_slider(self):
        if not self.current_book:
            return
        progress = self.current_book.progress * 100
        self.progress_slider.setValue(int(progress))

    def _update_chapter_label(self):
        if not self.current_book or not self.current_book.chapters:
            self.chapter_label.setText("— / —")
            return
        total = len(self.current_book.chapters)
        self.chapter_label.setText(f"第 {self.current_chapter_index + 1} / {total} 章")

    def _auto_save_progress(self):
        if not self.current_book or not self.current_book.chapters:
            return
        chapter = self.current_book.chapters[self.current_chapter_index]
        # current_position 由 _on_scroll_changed 持续更新
        approx_pos = self.current_book.current_position or chapter.start_pos
        self.current_book.progress = min(1.0, approx_pos / max(1, self.current_book.total_chars))

        from datetime import datetime
        self.current_book.last_read_at = datetime.now().isoformat()
        self.db.update_book(self.current_book)
        self._update_slider()

    def _record_reading_session(self):
        if not self.current_book or not self.session_start:
            return
        from datetime import datetime
        duration = (datetime.now() - self.session_start).total_seconds()
        if duration > 5:  # 至少 5 秒
            self.db.record_reading(
                self.current_book.id, int(duration), self.session_chars_read
            )

    # ---------- 键盘事件 ----------
    def eventFilter(self, watched: QWidget, event) -> bool:
        """子控件事件过滤器：键盘事件先过匹配表，命中则自己处理并 consume

        这是修复"翻不到下/上一章"的关键。Qt 默认把按键事件发给焦点
        子控件；QTextBrowser 自带 PageDown/PageUp 滚动处理并 accept，
        父 ReaderView.keyPressEvent 永远收不到 → 章节切不动。

        实现：双层 fallback。
        1) 先用 shortcut_keys 表匹配（支持自定义快捷键）。
        2) 表为空/未匹配时，按硬编码高频键（PageDown/PageUp/Space/方向键）
           直接 dispatch，保证基本翻页永远可用。
        """
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.KeyPress:
            action = self._match_action(event)
            if not action:
                action = self._fallback_action(event)
            self._log_key(watched, event, action)
            if action:
                self._dispatch_action(action)
                event.accept()
                return True  # 事件已被消费，不传给子控件
        return super().eventFilter(watched, event)

    def _fallback_action(self, event: QKeyEvent) -> Optional[str]:
        """硬编码后备匹配：shortcut_keys 表为空/不匹配时保证基本翻页可用

        处理：PageDown/Right/Space → next_page
              PageUp/Left            → prev_page
        """
        # 无修饰键（避免误吞 Ctrl+C 等）
        mods = int(event.modifiers().value)
        ctrl_shift_alt = mods & (
            int(Qt.KeyboardModifier.ControlModifier.value)
            | int(Qt.KeyboardModifier.ShiftModifier.value)
            | int(Qt.KeyboardModifier.AltModifier.value)
        )
        if ctrl_shift_alt:
            return None
        key = int(event.key())
        NEXT_KEYS = {
            int(Qt.Key.Key_PageDown.value),
            int(Qt.Key.Key_Right.value),
            int(Qt.Key.Key_Space.value),
            int(Qt.Key.Key_Down.value),
        }
        PREV_KEYS = {
            int(Qt.Key.Key_PageUp.value),
            int(Qt.Key.Key_Left.value),
            int(Qt.Key.Key_Up.value),
        }
        if key in NEXT_KEYS:
            return "next_page"
        if key in PREV_KEYS:
            return "prev_page"
        return None

    def _log_key(self, watched, event, action):
        """键盘事件诊断日志：写到 %APPDATA%\\NovelReader\\keyevent.log

        写入失败静默（不影响功能）。每次启动清空旧日志。
        """
        try:
            from app.config import user_data_path
            log_path = user_data_path() / "keyevent.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists() or log_path.stat().st_size > 200_000:
                log_path.write_text("=== keyevent.log (每次启动清空) ===\n", encoding="utf-8")
            with open(log_path, "a", encoding="utf-8") as f:
                wname = watched.objectName() if hasattr(watched, "objectName") else type(watched).__name__
                focus = self.focusWidget()
                focus_name = focus.objectName() if focus and hasattr(focus, "objectName") else "?"
                f.write(
                    f"key={int(event.key())} mods={int(event.modifiers().value)} "
                    f"watched={wname} focus={focus_name} "
                    f"action={action!r} ch={self.current_chapter_index} "
                    f"bar={self.text_browser.verticalScrollBar().value()}"
                    f"/{self.text_browser.verticalScrollBar().maximum()} "
                    f"at_bottom={self._is_at_bottom()}\n"
                )
                # 详细比对信息（首次写 + 每 50 行）
                if log_path.stat().st_size < 2000:
                    f.write(f"  next_page_pairs={sorted(self.shortcut_keys.get('next_page', []))}\n")
                    f.write(f"  prev_page_pairs={sorted(self.shortcut_keys.get('prev_page', []))}\n")
        except Exception:
            pass

    def keyPressEvent(self, event: QKeyEvent):
        action = self._match_action(event)
        if not action:
            super().keyPressEvent(event)
            return
        # 阻止事件继续传播
        event.accept()
        self._dispatch_action(action)

    def _match_action(self, event: QKeyEvent) -> Optional[str]:
        """根据当前快捷键配置查找对应动作名

        改成直接比对 (modifier_mask, key) int 元组，避开 QKeySequence
        在 PySide6 中字符串解析不稳定的问题。

        关键陷阱：event.key() 在 PySide6 6.5+ 严格枚举模式下返回 Qt.Key
        枚举对象，与整数 16777239 比较会返回 False。必须显式转 int。
        """
        key = int(event.key())  # 显式 int，避开枚举严格比较
        if key == int(Qt.Key.Key_unknown.value):
            return None
        mods_mask = int(event.modifiers().value) & (
            int(Qt.KeyboardModifier.ControlModifier.value)
            | int(Qt.KeyboardModifier.ShiftModifier.value)
            | int(Qt.KeyboardModifier.AltModifier.value)
            | int(Qt.KeyboardModifier.MetaModifier.value)
        )
        for action, pairs in self.shortcut_keys.items():
            for m, k in pairs:
                if k == key and m == mods_mask:
                    return action
        return None

    def _dispatch_action(self, action: str):
        """执行快捷键对应的动作"""
        if not self.current_book:
            if action == "back":
                self._on_back_clicked()
            elif action == "toggle_settings":
                self.open_settings_requested.emit()
            return

        if action == "next_page":
            # 向下翻一屏：先内部滚动，到底则进入下一章
            self._scroll_forward()
        elif action == "prev_page":
            # 向上翻一屏：先内部滚动，到顶则进入上一章
            self._scroll_backward()
        elif action == "next_chapter":
            self._next_chapter()
        elif action == "prev_chapter":
            self._prev_chapter()
        elif action == "back":
            self._on_back_clicked()
        elif action == "toggle_chapter":
            self._toggle_chapter_panel()
        elif action == "add_bookmark":
            self._add_bookmark()
        elif action == "cycle_theme":
            self._cycle_theme()
        elif action == "font_size_up":
            self._change_font_size(1)
        elif action == "font_size_down":
            self._change_font_size(-1)
        elif action == "toggle_settings":
            self.open_settings_requested.emit()

    def _on_back_clicked(self):
        self._auto_save_progress()
        self.close_book()
        self.book_closed.emit()
