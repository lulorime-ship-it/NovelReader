"""小说阅读器 - 应用入口"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from app.config import (
    DB_PATH, COVER_DIR, LOG_DIR, ROOT_DIR
)
from app.models import Database
from app.controllers import LibraryController
from app.views import MainWindow
from app.utils.qt_message_handler import install_quiet_handler


def main():
    # 屏蔽 PySide6 6.6+ 的 QFontDatabase fonts 目录缺失警告（无害但刷屏）
    install_quiet_handler()

    # 高 DPI 适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("小说阅读器")
    app.setApplicationDisplayName("小说阅读器")
    app.setOrganizationName("NovelReader")

    # 默认字体
    default_font = QFont("Microsoft YaHei", 10)
    app.setFont(default_font)

    # 初始化数据目录
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化数据层 & 业务层
    db = Database(DB_PATH)
    controller = LibraryController(db, COVER_DIR)

    # 创建主窗口
    window = MainWindow(db, controller)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
