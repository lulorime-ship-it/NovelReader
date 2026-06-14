"""书籍网格视图 - 自适应布局的书籍列表"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy
)

from ..models.book import Book
from .book_card import BookCard


class FlowLayout(QGridLayout):
    """简单的流式网格布局 - 固定 6 列"""
    COLUMNS = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalSpacing(20)
        self.setVerticalSpacing(20)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)


class BookGridView(QWidget):
    """书籍网格 - 展示书架中所有书籍的卡片网格"""
    book_opened = Signal(int)  # 点击了某本书
    book_deleted = Signal(int)  # 请求删除某本书
    book_favorited = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.books: list[Book] = []
        self.cards: list[BookCard] = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)

        # 内容容器
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)
        self.main_layout.setAlignment(Qt.AlignTop)

        # 网格
        self.grid = FlowLayout()
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.main_layout.addLayout(self.grid)

        # 空状态
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(12)

        self.empty_icon = QLabel("📚")
        empty_icon_font = self.empty_icon.font()
        empty_icon_font.setPointSize(64)
        self.empty_icon.setFont(empty_icon_font)
        self.empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_icon)

        self.empty_title = QLabel("书架空空如也")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_title)

        self.empty_subtitle = QLabel("点击右上角“导入书籍”添加你想读的小说")
        self.empty_subtitle.setObjectName("emptySubtitle")
        self.empty_subtitle.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_subtitle)

        self.empty_widget.setVisible(False)
        self.main_layout.addWidget(self.empty_widget)

    def set_books(self, books: list[Book]):
        """设置书籍列表"""
        self.books = books
        # 清除旧卡片
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()

        if not books:
            self.empty_widget.setVisible(True)
            return
        self.empty_widget.setVisible(False)

        # 添加新卡片
        cols = FlowLayout.COLUMNS
        for i, book in enumerate(books):
            card = BookCard(book)
            card.clicked.connect(self.book_opened)
            card.delete_requested.connect(self.book_deleted)
            row, col = divmod(i, cols)
            self.grid.addWidget(card, row, col)
            self.cards.append(card)
