"""关于对话框 - 作者信息、捐赠信息、二维码"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget,
    QGridLayout, QPushButton, QSizePolicy
)

from .. import __version__
from ..config import (
    AUTHOR_NAME, AUTHOR_EMAIL, DONATION_ADDRESSES, DONATION_QR_FILES,
    donation_qr_path
)


class AboutDialog(QDialog):
    """关于对话框：项目介绍 + 作者信息 + 捐赠信息（含二维码）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 小说阅读器")
        self.setMinimumSize(720, 600)
        self.resize(820, 680)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 滚动区域（以防窗口较小）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(18)

        # ----- 标题块 -----
        title = QLabel(f"小说阅读器 v{__version__}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1e293b;")
        layout.addWidget(title)

        subtitle = QLabel("基于 PySide6 构建的现代化本地小说阅读器")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(subtitle)

        # ----- 功能特性 -----
        features_box = QFrame()
        features_box.setObjectName("aboutSection")
        features_layout = QVBoxLayout(features_box)
        features_layout.setContentsMargins(16, 12, 16, 12)
        features_layout.setSpacing(6)
        features_title = QLabel("📚 主要功能")
        features_title.setStyleSheet("font-weight: 600; color: #1e293b; font-size: 13px;")
        features_layout.addWidget(features_title)
        for line in [
            "本地 txt 书籍导入、智能分章",
            "多套主题（明亮 / 暗黑 / 羊皮纸 / 护眼绿）",
            "阅读进度、书签、阅读时长与字数统计",
            "快捷键可自定义（设置 → 快捷键）",
            "按章阅读，滚到章节边界自动跳转上/下一章",
        ]:
            bullet = QLabel(f"• {line}")
            bullet.setStyleSheet("color: #475569; font-size: 12px;")
            features_layout.addWidget(bullet)
        layout.addWidget(features_box)

        # ----- 作者信息 -----
        author_box = QFrame()
        author_box.setObjectName("aboutSection")
        author_layout = QVBoxLayout(author_box)
        author_layout.setContentsMargins(16, 12, 16, 12)
        author_layout.setSpacing(4)
        author_title = QLabel("👤 作者")
        author_title.setStyleSheet("font-weight: 600; color: #1e293b; font-size: 13px;")
        author_layout.addWidget(author_title)
        author_line1 = QLabel(f"作者：{AUTHOR_NAME}")
        author_line1.setStyleSheet("color: #1e293b; font-size: 13px;")
        author_layout.addWidget(author_line1)
        author_line2 = QLabel(f"邮箱：{AUTHOR_EMAIL}")
        author_line2.setStyleSheet("color: #475569; font-size: 12px;")
        author_line2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        author_layout.addWidget(author_line2)
        layout.addWidget(author_box)

        # ----- 捐赠信息（含二维码） -----
        donate_box = QFrame()
        donate_box.setObjectName("aboutSection")
        donate_layout = QVBoxLayout(donate_box)
        donate_layout.setContentsMargins(16, 14, 16, 14)
        donate_layout.setSpacing(8)

        donate_title = QLabel("❤️  捐献支持")
        donate_title.setStyleSheet("font-weight: 600; color: #1e293b; font-size: 13px;")
        donate_layout.addWidget(donate_title)

        donate_intro = QLabel(
            "如果您觉得这个工具对您有帮助，欢迎通过以下方式捐献支持开发："
        )
        donate_intro.setWordWrap(True)
        donate_intro.setStyleSheet("color: #475569; font-size: 12px;")
        donate_layout.addWidget(donate_intro)

        # 二维码区域：横向并排展示
        qr_grid = QGridLayout()
        qr_grid.setSpacing(14)
        qr_grid.setContentsMargins(0, 6, 0, 0)

        for col, (label, addr) in enumerate(DONATION_ADDRESSES.items()):
            qr_grid.addWidget(self._build_qr_card(label, addr), 0, col)

        donate_layout.addLayout(qr_grid)

        qr_hint = QLabel("扫描各钱包二维码查看对应地址。")
        qr_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        donate_layout.addWidget(qr_hint)
        layout.addWidget(donate_box)

        # ----- 版权 -----
        copyright_label = QLabel(
            "© 2026 Novel Reader. Inspired by Koodo Reader & Legado."
        )
        copyright_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label, 0, Qt.AlignHCenter)

        layout.addStretch()

        # ----- 关闭按钮 -----
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(28, 0, 28, 16)
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primaryButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        outer.addLayout(btn_row)

    def _build_qr_card(self, label: str, address: str) -> QFrame:
        """单个钱包的二维码卡片"""
        card = QFrame()
        card.setObjectName("qrCard")
        card.setFixedWidth(200)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignHCenter)

        # 标题
        title = QLabel(label)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: 600; color: #1e293b; font-size: 12px;")
        card_layout.addWidget(title)

        # 二维码图片
        img_label = QLabel()
        img_label.setFixedSize(160, 160)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;"
        )
        qr_file = DONATION_QR_FILES.get(label, "")
        qr_path = donation_qr_path(qr_file) if qr_file else None
        if qr_path and qr_path.exists():
            pixmap = QPixmap(str(qr_path))
            img_label.setPixmap(
                pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            img_label.setText("(二维码缺失)")
            img_label.setStyleSheet(
                "background-color: #f1f5f9; border: 1px dashed #cbd5e1; "
                "border-radius: 6px; color: #94a3b8; font-size: 11px;"
            )
        card_layout.addWidget(img_label, 0, Qt.AlignHCenter)

        # 地址（可复制）
        addr_label = QLabel(address)
        addr_label.setWordWrap(True)
        addr_label.setAlignment(Qt.AlignCenter)
        addr_label.setStyleSheet(
            "color: #475569; font-size: 9px; font-family: Consolas, monospace;"
        )
        addr_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        addr_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        card_layout.addWidget(addr_label)

        return card
