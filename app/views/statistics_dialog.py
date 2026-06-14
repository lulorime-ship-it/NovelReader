"""阅读统计对话框 - 展示阅读时长、字数、书籍数等"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtGui import QFont


class StatCard(QFrame):
    """单个统计卡片"""
    def __init__(self, title: str, value: str, unit: str = "", accent: str = "#6366f1", parent=None):
        super().__init__(parent)
        self.setObjectName("bookCard")
        self.setStyleSheet(
            f"QFrame#bookCard {{ background: white; border: 1px solid #e4e7ed; border-radius: 10px; }}"
        )
        self.setFixedSize(180, 100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(title_label)

        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        value_layout.setAlignment(Qt.AlignBottom)

        value_label = QLabel(value)
        value_font = QFont("Microsoft YaHei", 22)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {accent};")
        value_layout.addWidget(value_label)

        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding-bottom: 4px;")
            value_layout.addWidget(unit_label)
        value_layout.addStretch()
        layout.addLayout(value_layout)
        layout.addStretch()


class StatisticsDialog(QDialog):
    """阅读统计弹窗"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("阅读统计")
        self.setFixedSize(620, 280)
        self._build_ui()
        self._load_stats()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📊 阅读统计")
        title_font = QFont("Microsoft YaHei", 16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.today_duration_card = StatCard("今日阅读", "0", "分钟", "#6366f1")
        self.today_chars_card = StatCard("今日字数", "0", "字", "#10b981")
        self.total_duration_card = StatCard("累计时长", "0", "小时", "#f59e0b")
        self.total_chars_card = StatCard("累计字数", "0", "字", "#ec4899")
        self.books_card = StatCard("书架数量", "0", "本", "#8b5cf6")
        self.read_books_card = StatCard("已读书籍", "0", "本", "#06b6d4")

        grid.addWidget(self.today_duration_card, 0, 0)
        grid.addWidget(self.today_chars_card, 0, 1)
        grid.addWidget(self.total_duration_card, 0, 2)
        grid.addWidget(self.total_chars_card, 1, 0)
        grid.addWidget(self.books_card, 1, 1)
        grid.addWidget(self.read_books_card, 1, 2)
        layout.addLayout(grid)
        layout.addStretch()

    def _load_stats(self):
        today = self.db.get_today_reading()
        total = self.db.get_total_stats()

        self._update_card(self.today_duration_card, f"{int(today['duration'] // 60)}")
        self._update_card(self.today_chars_card, f"{today['chars']:,}")
        self._update_card(self.total_duration_card, f"{total['duration'] // 3600}")
        self._update_card(self.total_chars_card, f"{total['chars']:,}")
        self._update_card(self.books_card, f"{total['total_books']}")
        self._update_card(self.read_books_card, f"{total['books_read']}")

    def _update_card(self, card: StatCard, value: str):
        # 找到 value_label 并更新（第二个 QLabel）
        for i in range(card.layout().count()):
            item = card.layout().itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    sub = item.layout().itemAt(j).widget()
                    if isinstance(sub, QLabel):
                        # 大字号的那个
                        f = sub.font()
                        if f.pointSize() > 14 or f.bold():
                            sub.setText(value)
                            return
