"""单本书籍卡片控件"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QMenu,
    QPushButton,
)
from pathlib import Path

from ..models.book import Book


class BookCard(QFrame):
    """书籍卡片 - 网格视图中的单本书

    交互：
    - 左键点击 → 打开阅读
    - 右键 → 弹出菜单（删除）
    - 悬停 → 右上角 ✕ 按钮变为红色高亮（点击触发删除）
    - 按钮常驻可见，作为发现性提示
    """
    clicked = Signal(int)  # 发送 book_id
    favorite_toggled = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, book: Book, parent=None):
        super().__init__(parent)
        self.book = book
        self.setObjectName("bookCard")
        self.setFixedSize(170, 260)
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()
        self._load_data()
        self.setMouseTracking(True)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # 顶部容器：仅放封面
        top_container = QFrame()
        top_container.setFixedSize(150, 200)

        # 封面
        self.cover_label = QLabel(top_container)
        self.cover_label.setFixedSize(150, 200)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet(
            "background-color: #f1f3f5; border-radius: 6px;"
        )
        self.cover_label.move(0, 0)

        layout.addWidget(top_container)

        # 删除按钮（覆盖在封面右上角，作为卡片直接子控件，
        # 不放进 layout，以免随 layout 自动显示）
        self.delete_btn = QPushButton("✕", self)
        self.delete_btn.setObjectName("cardDeleteBtn")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("从书架删除")
        # 卡片 margin 10 + 封面宽 150 - 按钮宽 22 - 右间距 4 = 134；上偏移 14
        self.delete_btn.move(134, 14)
        self.delete_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgba(0, 0, 0, 0.55);"
            "  color: white;"
            "  border: none;"
            "  border-radius: 11px;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  background-color: #dc2626;"
            "}"
        )
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        # 按钮作为发现性提示，常驻显示（半透明 + 右上角，不影响主视图）

        # 标题
        self.title_label = QLabel()
        self.title_label.setObjectName("bookTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.title_label)

        # 作者
        self.author_label = QLabel()
        self.author_label.setObjectName("bookAuthor")
        layout.addWidget(self.author_label)

        # 进度条 + 百分比
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(6)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("bookProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        progress_layout.addWidget(self.progress_bar, 1)

        self.progress_label = QLabel()
        self.progress_label.setObjectName("bookProgress")
        self.progress_label.setFixedWidth(40)
        self.progress_label.setAlignment(Qt.AlignRight)
        progress_layout.addWidget(self.progress_label, 0)

        layout.addLayout(progress_layout)

    def _load_data(self):
        self.title_label.setText(self.book.title or "未知标题")
        self.author_label.setText(self.book.author or "未知作者")

        # 加载封面
        if self.book.cover_path and Path(self.book.cover_path).exists():
            pixmap = QPixmap(self.book.cover_path)
            self.cover_label.setPixmap(
                pixmap.scaled(150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            # 占位封面
            self._draw_placeholder_cover()

        # 进度
        percent = int(self.book.progress * 100)
        self.progress_bar.setValue(percent)
        if percent > 0:
            self.progress_label.setText(f"{percent}%")
        else:
            self.progress_label.setText("未读")

    def _draw_placeholder_cover(self):
        pixmap = QPixmap(150, 200)
        pixmap.fill(QColor("#cbd5e1"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#64748b"))
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, self.book.title or "暂无封面")
        painter.end()
        self.cover_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.book.id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """鼠标进入时高亮删除按钮（按钮本身常驻显示）"""
        self.delete_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #dc2626;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 11px;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  background-color: #b91c1c;"
            "}"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时恢复半透明样式"""
        self.delete_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgba(0, 0, 0, 0.55);"
            "  color: white;"
            "  border: none;"
            "  border-radius: 11px;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  background-color: #dc2626;"
            "}"
        )
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        delete_action = QAction("🗑  从书架删除", menu)
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self.book.id)
        )
        menu.addAction(delete_action)
        menu.exec(event.globalPos())

    def _on_delete_clicked(self):
        """删除按钮直接发出请求（确认对话框由主窗口弹出）"""
        self.delete_requested.emit(self.book.id)
