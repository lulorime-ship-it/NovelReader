"""Qt 消息处理

PySide6 6.6+ 移除了随包发布的 fonts/ 目录，每次启动都会从 stderr 输出
"QFontDatabase: Cannot find font directory" 警告。这个警告是无害的（应用仍能
使用系统字体），但非常干扰阅读日志/测试输出。

本模块提供一个可注册的 handler，对该特定警告做静默处理。
"""
import sys
from PySide6.QtCore import qInstallMessageHandler, QtMsgType


def _default_handler(msg_type, ctx, msg):
    """Qt 默认处理 - 打印到 stderr"""
    type_names = {
        QtMsgType.QtDebugMsg:    "Qt Debug",
        QtMsgType.QtInfoMsg:     "Qt Info",
        QtMsgType.QtWarningMsg:  "Qt Warning",
        QtMsgType.QtCriticalMsg: "Qt Critical",
        QtMsgType.QtFatalMsg:    "Qt Fatal",
    }
    name = type_names.get(msg_type, "Qt")
    print(f"{name}: {msg}", file=sys.stderr)


def install_quiet_handler():
    """安装静默 handler：屏蔽 QFontDatabase 警告，其余消息保持默认行为

    必须在 QApplication 创建之前调用（qInstallMessageHandler 的语义要求）。
    """
    def handler(msg_type, ctx, msg):
        # 屏蔽 PySide6 6.6+ 的 fonts 目录缺失警告（无害但刷屏）
        if "QFontDatabase" in msg or "Cannot find font directory" in msg:
            return
        _default_handler(msg_type, ctx, msg)
    qInstallMessageHandler(handler)
