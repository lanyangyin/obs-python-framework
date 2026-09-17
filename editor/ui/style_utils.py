"""
把 EditorSettings 转成 QSS 字符串。
只对编辑器自身的 UI 生效；校验标色等语义色不在 QSS 里。
"""
from editor.settings_manager import EditorSettings


def build_qss(s: EditorSettings) -> str:
    """生成全局 QSS。"""
    # 字体：用户未指定时留空，让 Qt 用系统默认
    font_rule = ""
    if s.font_family or s.font_size > 0:
        parts = []
        if s.font_family:
            parts.append(f'font-family: "{s.font_family}";')
        if s.font_size > 0:
            parts.append(f"font-size: {s.font_size}pt;")
        font_rule = " ".join(parts)

    return f"""
/* ---------- 全局 ---------- */
QWidget {{
    color: {s.foreground};
    background-color: {s.background};
    {font_rule}
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
    background-color: {s.input_background};
    color: {s.input_foreground};
    border: 1px solid {s.accent};
    border-radius: 2px;
    padding: 2px 4px;
}}
QLineEdit:read-only {{
    background-color: {s.background};
    color: {s.label_foreground};
}}

QComboBox QAbstractItemView {{
    background-color: {s.input_background};
    color: {s.input_foreground};
    selection-background-color: {s.accent};
    selection-color: #ffffff;
}}

/* ---------- 树 ---------- */
QTreeView {{
    background-color: {s.tree_background};
    color: {s.tree_foreground};
    alternate-background-color: {s.property_background};
    selection-background-color: {s.accent};
    selection-color: #ffffff;
    outline: 0;
}}
QTreeView::item:hover {{
    background-color: {s.accent}33;
}}

/* ---------- 属性面板 ---------- */
QScrollArea {{
    background-color: {s.property_background};
    color: {s.property_foreground};
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: {s.property_background};
    color: {s.property_foreground};
}}

/* 属性面板左侧标签（QLabel 在 QFormLayout 的 label 位） */
QFormLayout QLabel {{
    color: {s.label_foreground};
}}

/* ---------- 按钮 / 工具栏 ---------- */
QPushButton {{
    background-color: {s.input_background};
    color: {s.input_foreground};
    border: 1px solid {s.accent};
    border-radius: 3px;
    padding: 4px 10px;
}}
QPushButton:hover {{
    background-color: {s.accent};
    color: #ffffff;
}}
QPushButton:disabled {{
    color: {s.label_foreground};
    border-color: {s.label_foreground};
}}

QToolBar {{
    background-color: {s.background};
    border: none;
}}

QStatusBar {{
    background-color: {s.background};
    color: {s.foreground};
}}

/* ---------- 滚动条（轻量） ---------- */
QScrollBar:vertical {{
    background: {s.background};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {s.label_foreground};
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def apply_to_app(app, settings: EditorSettings) -> None:
    """把 QSS 应用到整个应用。"""
    app.setStyleSheet(build_qss(settings))