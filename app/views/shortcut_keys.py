"""快捷键字符串 -> QKeySequence 解析

PySide6 中 QKeySequence("PageDown") 返回空序列，
必须用 Qt.Key_* 常量构造。DEFAULT_SHORTCUTS 中的字符串
（"PageDown", "Ctrl+Right" 等）需要在这里转换。
"""
from PySide6.QtCore import Qt, QKeyCombination
from PySide6.QtGui import QKeySequence


def _build_key_map():
    """构造键名 -> Qt.Key int 映射表"""
    m = {
        # 方向键
        "Right":     int(Qt.Key.Key_Right.value),
        "Left":      int(Qt.Key.Key_Left.value),
        "Up":        int(Qt.Key.Key_Up.value),
        "Down":      int(Qt.Key.Key_Down.value),
        # 翻页
        "PageDown":  int(Qt.Key.Key_PageDown.value),
        "PageUp":    int(Qt.Key.Key_PageUp.value),
        # 特殊
        "Space":     int(Qt.Key.Key_Space.value),
        "Escape":    int(Qt.Key.Key_Escape.value),
        "Esc":       int(Qt.Key.Key_Escape.value),
        "Tab":       int(Qt.Key.Key_Tab.value),
        "Enter":     int(Qt.Key.Key_Return.value),
        "Return":    int(Qt.Key.Key_Return.value),
        "Backspace": int(Qt.Key.Key_Backspace.value),
        "Delete":    int(Qt.Key.Key_Delete.value),
        "Home":      int(Qt.Key.Key_Home.value),
        "End":       int(Qt.Key.Key_End.value),
        "Insert":    int(Qt.Key.Key_Insert.value),
        # 功能键
        "F1":  int(Qt.Key.Key_F1.value),   "F2":  int(Qt.Key.Key_F2.value),
        "F3":  int(Qt.Key.Key_F3.value),   "F4":  int(Qt.Key.Key_F4.value),
        "F5":  int(Qt.Key.Key_F5.value),   "F6":  int(Qt.Key.Key_F6.value),
        "F7":  int(Qt.Key.Key_F7.value),   "F8":  int(Qt.Key.Key_F8.value),
        "F9":  int(Qt.Key.Key_F9.value),   "F10": int(Qt.Key.Key_F10.value),
        "F11": int(Qt.Key.Key_F11.value),  "F12": int(Qt.Key.Key_F12.value),
        # 符号
        "+":   int(Qt.Key.Key_Plus.value),
        "-":   int(Qt.Key.Key_Minus.value),
        "=":   int(Qt.Key.Key_Equal.value),
        ",":   int(Qt.Key.Key_Comma.value),
        ".":   int(Qt.Key.Key_Period.value),
        "/":   int(Qt.Key.Key_Slash.value),
        "[":   int(Qt.Key.Key_BracketLeft.value),
        "]":   int(Qt.Key.Key_BracketRight.value),
    }
    # A-Z: 0x41 + offset
    for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        m[c] = 0x41 + i
    # 0-9: 0x30 + offset
    for i in range(10):
        m[str(i)] = 0x30 + i
    return m


_KEY_NAME_TO_QT = _build_key_map()

_MOD_NAME_TO_QT = {
    "Ctrl":    int(Qt.KeyboardModifier.ControlModifier.value),
    "Control": int(Qt.KeyboardModifier.ControlModifier.value),
    "Shift":   int(Qt.KeyboardModifier.ShiftModifier.value),
    "Alt":     int(Qt.KeyboardModifier.AltModifier.value),
    "Meta":    int(Qt.KeyboardModifier.MetaModifier.value),
    "Win":     int(Qt.KeyboardModifier.MetaModifier.value),
    "Cmd":     int(Qt.KeyboardModifier.MetaModifier.value),
}


def parse_shortcut_int(text: str) -> tuple[int, int] | None:
    """把 "Ctrl+Right" / "PageDown" 解析为 (modifier_mask, key) 整数对

    与 QKeyEvent.modifiers().value / QKeyEvent.key() 直接比对。
    """
    if not text:
        return None
    text = str(text).strip()
    if not text:
        return None

    parts = [p.strip() for p in text.split("+") if p.strip()]
    if not parts:
        return None

    mods = 0
    key_val: int | None = None
    for p in parts:
        if p in _MOD_NAME_TO_QT:
            mods |= _MOD_NAME_TO_QT[p]
        elif p in _KEY_NAME_TO_QT:
            key_val = _KEY_NAME_TO_QT[p]
        else:
            # fallback: 试 QKeySequence 字符串解析（极少见）
            seq = QKeySequence(p)
            if not seq.isEmpty():
                return None
            return None

    if key_val is None:
        return None
    return (mods, key_val)


def parse_shortcut_string(text: str) -> QKeySequence | None:
    """把 "Ctrl+Right" / "PageDown" 解析为 QKeySequence（保留兼容 API）"""
    pair = parse_shortcut_int(text)
    if pair is None:
        return None
    mods_int, key_int = pair
    try:
        return QKeySequence(QKeyCombination(Qt.KeyboardModifier(mods_int), Qt.Key(key_int)))
    except (TypeError, AttributeError, ValueError):
        return QKeySequence(mods_int | key_int)
