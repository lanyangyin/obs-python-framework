"""右侧属性面板：根据选中的控件节点显示/编辑属性。"""
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QCheckBox, QComboBox, QScrollArea, QFrame, QSizePolicy,
    QHBoxLayout, QSpacerItem,
)

from editor.model import (
    WidgetNode, WidgetTree,
    list_control_functions, list_all_function_names,
)


# 字段编辑顺序（先核心字段，再自由属性）
CORE_FIELD_ORDER = [
    "control_name",
    "widget_category",
    "object_name",
    "props_name",
    "group_props_name",
    "description",
    "long_description",
    "widget_variant",
    "modified_callback_enabled",
    "modified_callback",
    "source_line",
    "level",
]

# 只读字段
READONLY_FIELDS = {"widget_category", "source_line", "level", "props_name"}

# 字段显示名（中文友好）
FIELD_LABELS = {
    "control_name": "控件名 (control_name)",
    "widget_category": "分类 (widget_category)",
    "object_name": "对象名 (object_name)",
    "props_name": "属性集 (props_name)",
    "group_props_name": "子属性集 (group_props_name)",
    "description": "简短描述",
    "long_description": "详细描述",
    "widget_variant": "变体 (widget_variant)",
    "modified_callback_enabled": "启用变动回调",
    "modified_callback": "变动回调函数名",
    "source_line": "源 CSV 行号",
    "level": "层级",
}

# 已知的"函数名"字段：这些字段编辑时提供下拉建议
FUNCTION_FIELD_NAMES = {
    "modified_callback",
    "visible", "enabled",
    "checked",
    "min_val", "max_val", "step", "digital",
    "info_type",
    "text",
    "label", "value", "items",
    "color_alpha", "color_red", "color_green", "color_blue",
    "font_face", "font_size", "font_style",
    "font_bold", "font_italic", "font_underline", "font_strikeout",
    "path_text",
}


class PropertyPanel(QWidget):
    """属性编辑面板。"""

    # 某个字段被编辑后发出，参数：(node, field_name, old_value, new_value)
    field_edit_committed = Signal(object, str, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node: Optional[WidgetNode] = None
        self._tree: Optional[WidgetTree] = None
        self._editors: Dict[str, QWidget] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # 顶部提示（无选中时显示）
        self._hint_label = QLabel("选中左侧控件后，属性将在这里显示。")
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        outer.addWidget(self._hint_label)

        # 滚动区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._form_host = QWidget()
        self._form_layout = QFormLayout(self._form_host)
        self._form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._form_layout.setContentsMargins(12, 12, 12, 12)
        self._form_layout.setSpacing(8)

        self._scroll.setWidget(self._form_host)
        outer.addWidget(self._scroll)

        self._scroll.hide()

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def set_tree(self, tree: Optional[WidgetTree]):
        """主窗口在加载/重载 tree 后调用，供 props_name 下拉使用。"""
        self._tree = tree

    def set_node(self, node: Optional[WidgetNode]):
        """主窗口在选中变化时调用。"""
        self._current_node = node
        if node is None:
            self._show_hint()
        else:
            self._show_form(node)

    def current_node(self) -> Optional[WidgetNode]:
        """返回当前显示的节点。"""
        return self._current_node

    def refresh_field(self, field: str) -> None:
        """
        从 node 重新读取指定字段的值，写回编辑器（不触发信号）。
        支持 "prop::xxx" 形式（自由属性）与普通字段名。
        用于 undo / redo 后同步界面。
        """
        if self._current_node is None:
            return
        editor = self._editors.get(field)
        if editor is None:
            return

        if field.startswith("prop::"):
            prop_name = field[len("prop::"):]
            new_value = self._current_node.properties.get(prop_name)
        else:
            new_value = getattr(self._current_node, field, None)

        text = str(new_value) if new_value is not None else ""

        editor.blockSignals(True)
        try:
            if isinstance(editor, QLineEdit):
                editor.setText(text)
            elif isinstance(editor, QCheckBox):
                editor.setChecked(bool(new_value))
            elif isinstance(editor, QComboBox):
                editor.setCurrentText(text)
        finally:
            editor.blockSignals(False)

    # ------------------------------------------------------------------
    # 内部：显示/隐藏
    # ------------------------------------------------------------------
    def _show_hint(self):
        self._clear_form()
        self._scroll.hide()
        self._hint_label.show()

    def _show_form(self, node: WidgetNode):
        self._hint_label.hide()
        self._scroll.show()
        self._clear_form()
        self._populate_form(node)

    def _clear_form(self):
        """清空所有表单项。"""
        while self._form_layout.rowCount() > 0:
            self._form_layout.removeRow(0)
        self._editors.clear()

    # ------------------------------------------------------------------
    # 表单填充
    # ------------------------------------------------------------------
    def _populate_form(self, node: WidgetNode):
        # 1. 核心字段
        for field in CORE_FIELD_ORDER:
            if not hasattr(node, field):
                continue
            value = getattr(node, field)
            editor = self._make_editor(node, field, value)
            if editor is None:
                continue
            self._editors[field] = editor
            self._form_layout.addRow(FIELD_LABELS.get(field, field), editor)

        # 2. 分隔线
        self._form_layout.addRow(self._make_separator())

        # 3. 自由属性（properties）
        if node.properties:
            header = QLabel("自由属性")
            header.setStyleSheet("font-weight: 600; color: #555; margin-top: 6px;")
            self._form_layout.addRow(header)
            for prop_name, prop_value in node.properties.items():
                editor = self._make_property_editor(node, prop_name, prop_value)
                self._editors[f"prop::{prop_name}"] = editor
                self._form_layout.addRow(prop_name, editor)

    # ------------------------------------------------------------------
    # 编辑器工厂
    # ------------------------------------------------------------------
    def _make_editor(self, node: WidgetNode, field: str, value: Any) -> Optional[QWidget]:
        # 只读
        if field in READONLY_FIELDS:
            label = QLabel(str(value) if value is not None else "")
            label.setStyleSheet("color: #666;")
            return label

        # 布尔
        if field == "modified_callback_enabled":
            editor = QCheckBox()
            editor.setChecked(bool(value))
            editor.toggled.connect(
                lambda checked: self._on_field_changed(node, field, checked)
            )
            return editor

        # props_name 只读：由控件在树中的位置自动推导
        if field == "props_name":
            editor = QLineEdit()
            editor.setText(str(value) if value is not None else "")
            editor.setReadOnly(True)
            editor.setStyleSheet("color: #666; background: #f0f0f0;")
            editor.setToolTip("由控件在树中的位置自动推导，请通过拖拽调整层级。")
            return editor

        # modified_callback → 可编辑下拉
        if field == "modified_callback":
            editor = QComboBox()
            editor.setEditable(True)
            editor.addItem("")  # 空选项
            for name in list_control_functions():
                editor.addItem(name)
            editor.setCurrentText(str(value) if value else "")
            editor.currentTextChanged.connect(
                lambda text: self._on_field_changed(node, field, text or None)
            )
            return editor

        # 其他 → 单行文本
        editor = QLineEdit()
        editor.setText(str(value) if value is not None else "")
        editor.textEdited.connect(
            lambda text: self._on_field_changed(node, field, text)
        )
        return editor

    def _make_property_editor(self, node: WidgetNode, prop_name: str, value: Any) -> QWidget:
        if prop_name in FUNCTION_FIELD_NAMES:
            editor = QComboBox()
            editor.setEditable(True)
            editor.addItem("")
            for name in list_all_function_names():
                editor.addItem(name)
            editor.setCurrentText(str(value) if value is not None else "")
            editor.currentTextChanged.connect(
                lambda text, pn=prop_name: self._on_property_changed(node, pn, text)
            )
            return editor
        editor = QLineEdit()
        editor.setText(str(value) if value is not None else "")
        editor.textEdited.connect(
            lambda text, pn=prop_name: self._on_property_changed(node, pn, text)
        )
        return editor

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ccc;")
        return line

    # ------------------------------------------------------------------
    # 字段变动
    # ------------------------------------------------------------------
    def _on_field_changed(self, node: WidgetNode, field: str, value: Any):
        old_value = getattr(node, field, None)
        if old_value == value:
            return
        # 只发信号，由主窗口决定是否 push 到 undo stack
        # 值的真正写入由 EditFieldCommand.redo() 完成
        self.field_edit_committed.emit(node, field, old_value, value)

    def _on_property_changed(self, node: WidgetNode, prop_name: str, value: str):
        old_value = node.properties.get(prop_name)
        new_value = value if value != "" else None
        if old_value == new_value:
            return
        # 用 "prop::" 前缀区分结构化字段与自由属性
        self.field_edit_committed.emit(
            node, f"prop::{prop_name}", old_value, new_value
        )