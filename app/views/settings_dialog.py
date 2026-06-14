"""设置对话框 - 字体、字号、行间距、主题、页边距、快捷键"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QFontComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QButtonGroup, QFrame, QTabWidget, QWidget, QScrollArea, QKeySequenceEdit,
    QListWidget, QListWidgetItem
)

from ..config import DEFAULT_SETTINGS, DEFAULT_SHORTCUTS, SHORTCUT_ACTIONS
from ..resources.themes import THEMES as THEME_PRESETS


class ShortcutEditRow(QWidget):
    """单条动作的快捷键编辑行：动作名 + 多个 QKeySequenceEdit"""

    MAX_KEYS = 4  # 单个动作最多支持 4 个绑定

    def __init__(self, action: str, label: str, keys: list[str], parent=None):
        super().__init__(parent)
        self.action = action
        self.edits: list[QKeySequenceEdit] = []
        self._build_ui(label, keys)

    def _build_ui(self, label: str, keys: list[str]):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(4)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel(label)
        title_label.setStyleSheet("color: #1e293b; font-size: 13px; font-weight: 600;")
        title_label.setFixedWidth(120)
        title_row.addWidget(title_label)

        self.add_btn = QPushButton("＋ 添加键位")
        self.add_btn.setObjectName("iconButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        self.add_btn.clicked.connect(self._add_empty_edit)
        title_row.addWidget(self.add_btn)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("iconButton")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        self.reset_btn.clicked.connect(self._reset_defaults)
        title_row.addWidget(self.reset_btn)
        title_row.addStretch()
        outer.addLayout(title_row)

        # 键位编辑行容器
        self.keys_container = QWidget()
        self.keys_layout = QHBoxLayout(self.keys_container)
        self.keys_layout.setContentsMargins(120, 0, 0, 0)
        self.keys_layout.setSpacing(8)
        self.keys_layout.addStretch()
        outer.addWidget(self.keys_container)

        # 加载初始键位
        default_keys = DEFAULT_SHORTCUTS.get(self.action, [])
        for k in (keys or default_keys):
            self._append_edit(k)

    def _append_edit(self, key_str: str = ""):
        if len(self.edits) >= self.MAX_KEYS:
            return
        edit_row = QWidget()
        row_layout = QHBoxLayout(edit_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        edit = QKeySequenceEdit()
        edit.setMaximumSequenceLength(1)
        edit.setFixedWidth(150)
        if key_str:
            edit.setKeySequence(QKeySequence(key_str))
        self.edits.append(edit)
        row_layout.addWidget(edit)

        # 移除按钮
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("iconButton")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setToolTip("移除该键位")
        remove_btn.clicked.connect(lambda: self._remove_edit(edit_row, edit))
        row_layout.addWidget(remove_btn)

        # 插入到 stretch 之前
        self.keys_layout.insertWidget(self.keys_layout.count() - 1, edit_row)
        self._update_buttons()

    def _add_empty_edit(self):
        self._append_edit("")

    def _remove_edit(self, row_widget: QWidget, edit: QKeySequenceEdit):
        if edit in self.edits:
            self.edits.remove(edit)
        row_widget.setParent(None)
        row_widget.deleteLater()
        self._update_buttons()

    def _reset_defaults(self):
        # 移除全部现有编辑
        for edit in list(self.edits):
            for i in range(self.keys_layout.count()):
                item = self.keys_layout.itemAt(i)
                if item.widget() and item.widget().findChild(QKeySequenceEdit) is edit:
                    item.widget().setParent(None)
                    item.widget().deleteLater()
                    break
        self.edits.clear()
        for k in DEFAULT_SHORTCUTS.get(self.action, []):
            self._append_edit(k)
        self._update_buttons()

    def _update_buttons(self):
        self.add_btn.setEnabled(len(self.edits) < self.MAX_KEYS)

    def get_keys(self) -> list[str]:
        """返回当前所有非空键位（标准字符串形式）"""
        result = []
        for edit in self.edits:
            seq = edit.keySequence()
            # 既要 seq.isEmpty()，也要 toString() 非空 - 部分场景下
            # QKeySequenceEdit 处于"等待输入"状态时 isEmpty() 可能为 False
            s = seq.toString().strip()
            if s:
                result.append(s)
        return result

    def has_conflict(self) -> bool:
        """简单检测本行内是否有重复"""
        keys = self.get_keys()
        return len(keys) != len(set(keys))


class SettingsDialog(QDialog):
    """阅读设置对话框"""
    settings_changed = Signal(dict)

    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("阅读设置")
        self.setMinimumSize(560, 560)
        self.resize(620, 640)
        self.settings = dict(current_settings)
        # 拷贝一份 shortcuts，避免修改影响原值
        self.settings["shortcuts"] = dict(current_settings.get("shortcuts") or DEFAULT_SHORTCUTS)
        self.shortcut_rows: dict[str, ShortcutEditRow] = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        title = QLabel("⚙  阅读设置")
        title.setObjectName("settingsTitle")
        title.setStyleSheet(
            "color: #1e293b; font-size: 18px; font-weight: 700; padding: 16px 24px 8px 24px;"
        )
        layout.addWidget(title)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self._build_general_tab(), "通用")
        self.tabs.addTab(self._build_shortcut_tab(), "快捷键")
        layout.addWidget(self.tabs, 1)

        # 按钮
        btn_container = QFrame()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 12, 20, 16)

        hint_label = QLabel("设置会自动保存到数据库，下次启动生效")
        hint_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        btn_layout.addWidget(hint_label)
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("iconButton")
        cancel_btn.setStyleSheet("padding: 8px 18px; min-width: 80px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.ok_btn = QPushButton("保存")
        self.ok_btn.setObjectName("primaryButton")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(self.ok_btn)

        layout.addWidget(btn_container)

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        # 用滚动区域以防内容超出
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        container_outer = QVBoxLayout()
        container_outer.setContentsMargins(0, 0, 0, 0)

        inner_layout = QVBoxLayout(tab)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(16)

        # 字体设置组
        font_group = QGroupBox("字体")
        font_form = QFormLayout(font_group)
        font_form.setSpacing(10)
        font_form.setContentsMargins(12, 16, 12, 12)

        self.font_combo = QFontComboBox()
        self.font_combo.setEditable(False)
        font_form.addRow("字体:", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 36)
        self.font_size_spin.setSuffix(" px")
        font_form.addRow("字号:", self.font_size_spin)

        self.line_height_spin = QDoubleSpinBox()
        self.line_height_spin.setRange(1.2, 2.5)
        self.line_height_spin.setSingleStep(0.1)
        self.line_height_spin.setDecimals(1)
        font_form.addRow("行间距:", self.line_height_spin)

        self.page_margin_spin = QSpinBox()
        self.page_margin_spin.setRange(20, 80)
        self.page_margin_spin.setSuffix(" px")
        font_form.addRow("页边距:", self.page_margin_spin)

        inner_layout.addWidget(font_group)

        # 主题组
        theme_group = QGroupBox("主题")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setContentsMargins(12, 16, 12, 12)
        theme_layout.setSpacing(8)

        self.theme_buttons = QButtonGroup(self)
        self.theme_buttons.setExclusive(True)
        theme_btn_layout = QHBoxLayout()
        theme_btn_layout.setSpacing(6)
        for key, preset in THEME_PRESETS.items():
            btn = QPushButton(preset.name)
            btn.setObjectName("themeChip")
            btn.setCheckable(True)
            btn.setProperty("theme_key", key)
            btn.setCursor(Qt.PointingHandCursor)
            self.theme_buttons.addButton(btn)
            theme_btn_layout.addWidget(btn)
        theme_btn_layout.addStretch()
        theme_layout.addLayout(theme_btn_layout)

        theme_hint = QLabel("提示：阅读界面「🌗 主题」按钮可快速切换")
        theme_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        theme_layout.addWidget(theme_hint)

        inner_layout.addWidget(theme_group)
        inner_layout.addStretch()

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll)
        return wrapper

    def _build_shortcut_tab(self) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 顶部说明
        hint = QLabel(
            "💡 点击右侧输入框并按下希望设置的按键（支持组合键）。\n"
            "   每个动作最多可绑定 4 个键位；空键位将被忽略。"
        )
        hint.setStyleSheet(
            "color: #475569; font-size: 12px; padding: 12px 20px;"
            "background-color: #f1f5f9; border-bottom: 1px solid #e4e7ed;"
        )
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        form = QVBoxLayout(content)
        form.setContentsMargins(20, 12, 20, 12)
        form.setSpacing(8)

        shortcuts = self.settings.get("shortcuts") or DEFAULT_SHORTCUTS
        for action, label in SHORTCUT_ACTIONS:
            row = ShortcutEditRow(action, label, shortcuts.get(action, []))
            self.shortcut_rows[action] = row
            form.addWidget(row)

        # 全局操作按钮
        form.addSpacing(8)
        action_row = QHBoxLayout()
        reset_all_btn = QPushButton("🔄 恢复全部默认")
        reset_all_btn.setObjectName("iconButton")
        reset_all_btn.setCursor(Qt.PointingHandCursor)
        reset_all_btn.setStyleSheet("padding: 6px 14px;")
        reset_all_btn.clicked.connect(self._reset_all_shortcuts)
        action_row.addWidget(reset_all_btn)
        action_row.addStretch()
        form.addLayout(action_row)
        form.addStretch()

        return tab

    def _load_values(self):
        self.font_combo.setCurrentFont(self.settings.get("font_family", DEFAULT_SETTINGS["font_family"]))
        self.font_size_spin.setValue(int(self.settings.get("font_size", DEFAULT_SETTINGS["font_size"])))
        self.line_height_spin.setValue(float(self.settings.get("line_height", DEFAULT_SETTINGS["line_height"])))
        self.page_margin_spin.setValue(int(self.settings.get("page_margin", DEFAULT_SETTINGS["page_margin"])))

        current_theme = self.settings.get("theme", "light")
        for btn in self.theme_buttons.buttons():
            if btn.property("theme_key") == current_theme:
                btn.setChecked(True)
                break

    def _reset_all_shortcuts(self):
        for action, row in self.shortcut_rows.items():
            row._reset_defaults()

    def _on_ok(self):
        self.settings["font_family"] = self.font_combo.currentFont().family()
        self.settings["font_size"] = self.font_size_spin.value()
        self.settings["line_height"] = self.line_height_spin.value()
        self.settings["page_margin"] = self.page_margin_spin.value()

        checked = self.theme_buttons.checkedButton()
        if checked:
            self.settings["theme"] = checked.property("theme_key")

        # 收集快捷键
        shortcuts = {}
        for action, row in self.shortcut_rows.items():
            keys = row.get_keys()
            if keys:
                shortcuts[action] = keys
        self.settings["shortcuts"] = shortcuts

        self.settings_changed.emit(self.settings)
        self.accept()
