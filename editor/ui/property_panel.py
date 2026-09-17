"""右侧属性面板：根据选中的控件节点显示/编辑属性。"""
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QCheckBox, QComboBox, QScrollArea, QFrame, QSizePolicy,
    QHBoxLayout, QSpacerItem, QToolButton, QMessageBox,
    QSpinBox, QDoubleSpinBox,
)
from editor.model import (
    WidgetNode, WidgetTree,
    list_control_functions, list_all_function_names,
    list_variants_for, list_functions_for_field, list_button_functions,
)
from editor.ui.collapsible_section import CollapsibleSection

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
    "click_callback",
    "url",
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


class _FunctionNameEditor(QWidget):
    """函数名字段编辑器：可编辑下拉 + 点击 {} 按钮编辑函数体。"""

    textChanged = Signal(str)
    editRequested = Signal()

    def __init__(self, current_text: str, candidates, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.addItem("")
        for c in candidates:
            self._combo.addItem(c)
        self._combo.setCurrentText(current_text or "")
        self._combo.currentTextChanged.connect(self.textChanged)
        layout.addWidget(self._combo, 1)

        self._edit_btn = QToolButton()
        self._edit_btn.setText("{}")
        self._edit_btn.setToolTip("点击编辑函数体")
        self._edit_btn.setFixedWidth(28)
        self._edit_btn.clicked.connect(self._on_edit_btn_clicked)
        layout.addWidget(self._edit_btn)

    def set_candidates(self, candidates):
        """更新下拉候选，保留当前文本。"""
        current = self._combo.currentText()
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("")
        for c in candidates:
            self._combo.addItem(c)
        self._combo.setCurrentText(current)
        self._combo.blockSignals(False)

    def text(self) -> str:
        return self._combo.currentText()

    def setText(self, text: str):
        self._combo.blockSignals(True)
        self._combo.setCurrentText(text or "")
        self._combo.blockSignals(False)

    def blockSignals(self, b):
        super().blockSignals(b)
        self._combo.blockSignals(b)
        self._edit_btn.blockSignals(b)

    def _on_edit_btn_clicked(self, checked=False):
        """QToolButton.clicked 带一个 bool 参数，用一个中间方法转发。"""
        self.editRequested.emit()

def _make_readonly_widget(widget: QWidget) -> None:
    """
    递归把 widget 及直接子控件设为只读/禁用，保留可读性。
    用于内置按钮（框架动态创建、不应被编辑器修改）。
    """
    if isinstance(widget, QLineEdit):
        widget.setReadOnly(True)
        widget.setStyleSheet("color: #666; background: #f0f0f0;")
    elif isinstance(widget, QComboBox):
        widget.setEnabled(False)
        widget.setEditable(False)
    elif isinstance(widget, (QCheckBox, QSpinBox, QDoubleSpinBox, QToolButton)):
        widget.setEnabled(False)

    # 只遍历直接子控件，避免 O(n^2)
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        _make_readonly_widget(child)

class PropertyPanel(QWidget):
    """属性编辑面板。"""

    # 某个字段被编辑后发出，参数：(node, field_name, old_value, new_value)
    field_edit_committed = Signal(object, str, object, object)
    # 分组折叠状态变化，参数：(section_key, expanded)
    section_toggled = Signal(str, bool)
    # 双击函数名字段 → 请求编辑函数体
    # 参数：(node, function_name, field_key)
    function_edit_requested = Signal(object, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node: Optional[WidgetNode] = None
        self._tree: Optional[WidgetTree] = None
        self._editors: Dict[str, QWidget] = {}
        self._search_text: str = ""

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

        # 搜索栏（有选中时显示）
        self._search_bar = QWidget()
        search_layout = QHBoxLayout(self._search_bar)
        search_layout.setContentsMargins(8, 6, 8, 2)
        search_layout.setSpacing(4)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("搜索字段（名称 / 值）...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_edit)

        self._search_clear_btn = QToolButton()
        self._search_clear_btn.setText("×")
        self._search_clear_btn.setToolTip("清空搜索")
        self._search_clear_btn.setAutoRaise(True)
        self._search_clear_btn.clicked.connect(
            lambda: self._search_edit.setText("")
        )
        search_layout.addWidget(self._search_clear_btn)

        outer.addWidget(self._search_bar)
        self._search_bar.hide()

        # 滚动区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        # 滚动区内的容器，纵向排布两个 CollapsibleSection
        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(4, 4, 4, 4)
        host_layout.setSpacing(8)

        # --- 结构化字段 section ---
        self._core_section = CollapsibleSection("结构化字段", expanded=True)
        self._core_form_host = QWidget()
        self._core_form = QFormLayout(self._core_form_host)
        self._core_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._core_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._core_form.setContentsMargins(0, 0, 0, 0)
        self._core_form.setSpacing(6)
        self._core_section.set_content(self._core_form_host)
        host_layout.addWidget(self._core_section)

        # --- 自由属性 section ---
        self._free_section = CollapsibleSection("自由属性", expanded=True)
        self._free_form_host = QWidget()
        self._free_form = QFormLayout(self._free_form_host)
        self._free_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._free_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._free_form.setContentsMargins(0, 0, 0, 0)
        self._free_form.setSpacing(6)
        self._free_section.set_content(self._free_form_host)
        host_layout.addWidget(self._free_section)

        host_layout.addStretch()

        self._scroll.setWidget(host)
        outer.addWidget(self._scroll)

        self._scroll.hide()

        # 展开/折叠状态变化时通知主窗口（用于持久化）
        self._core_section.toggled.connect(
            lambda v: self.section_toggled.emit("core", v)
        )
        self._free_section.toggled.connect(
            lambda v: self.section_toggled.emit("free", v)
        )

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
            if isinstance(editor, _FunctionNameEditor):
                editor.setText(text)
            elif isinstance(editor, QLineEdit):
                editor.setText(text)
            elif isinstance(editor, QCheckBox):
                editor.setChecked(bool(new_value))
            elif isinstance(editor, QComboBox):
                editor.setCurrentText(text)
        finally:
            editor.blockSignals(False)

    def refresh_function_candidates(self):
        """重新加载所有函数名字段的下拉候选。"""
        from editor.model import list_functions_for_field
        for key, editor in self._editors.items():
            if not isinstance(editor, _FunctionNameEditor):
                continue
            # key 可能是 "modified_callback" 或 "prop::xxx"
            editor.set_candidates(list_functions_for_field(key))

    # ------------------------------------------------------------------
    # 内部：显示/隐藏
    # ------------------------------------------------------------------
    def _show_hint(self):
        self._clear_form()
        self._scroll.hide()
        self._hint_label.show()
        self._search_bar.hide()

    def _show_form(self, node: WidgetNode):
        self._hint_label.hide()
        self._scroll.show()
        self._search_bar.show()
        self._rebuild_form()

    def _rebuild_form(self):
        """按当前 _search_text 重建表单。"""
        self._clear_form()
        if self._current_node is None:
            return
        self._populate_form(self._current_node, self._search_text)

        # 内置按钮：全部属性设为只读（可查看不可修改）
        from editor.model.csv_io import is_builtin_control
        if is_builtin_control(self._current_node.control_name):
            for editor in self._editors.values():
                _make_readonly_widget(editor)

    def _clear_form(self):
        """清空两个分组的表单项。"""
        for form in (self._core_form, self._free_form):
            while form.rowCount() > 0:
                form.removeRow(0)
        self._editors.clear()

    # ------------------------------------------------------------------
    # 表单填充
    # ------------------------------------------------------------------
    def _populate_form(self, node: WidgetNode, search: str = ""):
        search_lower = search.lower().strip()
        filter_active = bool(search_lower)

        # 1. 结构化字段
        core_count = 0
        for field in CORE_FIELD_ORDER:
            if not hasattr(node, field):
                continue
            value = getattr(node, field)
            label = FIELD_LABELS.get(field, field)
            if filter_active and not self._field_matches(
                field, label, value, search_lower
            ):
                continue
            editor = self._make_editor(node, field, value)
            if editor is None:
                continue
            self._editors[field] = editor
            self._core_form.addRow(label, editor)
            core_count += 1

        if core_count == 0:
            hint = QLabel(
                "（无匹配的结构化字段）" if filter_active else "（无结构化字段）"
            )
            hint.setStyleSheet("color: #888; font-style: italic;")
            self._core_form.addRow(hint)
            if filter_active:
                self._core_section.set_expanded(True)
        self._core_section.set_count(core_count)

        # 2. 自由属性
        free_count = 0
        if node.properties:
            for prop_name, prop_value in node.properties.items():
                if filter_active and not self._field_matches(
                    prop_name, prop_name, prop_value, search_lower
                ):
                    continue
                editor = self._make_property_editor(node, prop_name, prop_value)
                self._editors[f"prop::{prop_name}"] = editor
                self._free_form.addRow(prop_name, editor)
                free_count += 1

        if free_count == 0:
            hint_text = (
                "（无匹配的自由属性）" if filter_active else "（无自由属性）"
            )
            hint = QLabel(hint_text)
            hint.setStyleSheet("color: #888; font-style: italic;")
            self._free_form.addRow(hint)
            if filter_active:
                self._free_section.set_expanded(True)
        self._free_section.set_count(free_count)

        # 3. 过滤时如果有匹配，自动展开对应 section
        if filter_active:
            if core_count > 0 and not self._core_section.is_expanded():
                self._core_section.set_expanded(True)
            if free_count > 0 and not self._free_section.is_expanded():
                self._free_section.set_expanded(True)

    @staticmethod
    def _field_matches(field_key: str, label: str, value, search_lower: str) -> bool:
        """字段是否匹配搜索词（匹配 字段名 / 标签 / 值 之一）。"""
        # 字段名
        if search_lower in field_key.lower():
            return True
        # 显示标签
        if search_lower in label.lower():
            return True
        # 值
        if value is not None:
            try:
                if search_lower in str(value).lower():
                    return True
            except Exception:
                pass
        return False

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

        # widget_variant → 根据 category 可编辑下拉
        if field == "widget_variant":
            editor = QComboBox()
            editor.setEditable(True)
            editor.addItem("")
            for name in list_variants_for(node.widget_category):
                editor.addItem(name)
            editor.setCurrentText(str(value) if value else "")
            editor.currentTextChanged.connect(
                lambda text: self._on_field_changed(node, field, text or None)
            )
            return editor

        # modified_callback → 可编辑下拉
        if field == "modified_callback":
            editor = _FunctionNameEditor(
                str(value) if value else "",
                list_button_functions(),
            )
            editor.textChanged.connect(
                lambda text: self._on_field_changed(node, field, text or None)
            )
            editor.editRequested.connect(
                lambda e=editor, f=field: self.function_edit_requested.emit(
                    node, e.text(), f
                )
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
        # 布尔值 → 按场景选择展示方式
        if isinstance(value, bool):
            from editor.model.csv_io import is_builtin_control
            if is_builtin_control(node.control_name):
                # 内置控件：只读展示，文本形式更直观
                label = QLabel("True" if value else "False")
                label.setStyleSheet(
                    "color: #666; font-family: Consolas, monospace;"
                )
                return label
            cb = QCheckBox()
            cb.setChecked(value)
            cb.toggled.connect(
                lambda checked, pn=prop_name: self._on_property_changed(
                    node, pn, checked
                )
            )
            return cb

        # 函数名字段 → 带 {} 按钮的下拉
        if prop_name in FUNCTION_FIELD_NAMES:
            editor = _FunctionNameEditor(
                str(value) if value is not None else "",
                list_functions_for_field(f"prop::{prop_name}"),
            )
            editor.textChanged.connect(
                lambda text, pn=prop_name: self._on_property_changed(node, pn, text)
            )
            editor.editRequested.connect(
                lambda e=editor, pn=prop_name: self.function_edit_requested.emit(
                    node, e.text(), f"prop::{pn}"
                )
            )
            return editor

        # 其他 → 单行文本
        editor = QLineEdit()
        editor.setText(str(value) if value is not None else "")
        editor.textEdited.connect(
            lambda text, pn=prop_name: self._on_property_changed(node, pn, text)
        )
        return editor

    def set_section_expanded(self, section_key: str, expanded: bool):
        if section_key == "core":
            self._core_section.set_expanded(expanded)
        elif section_key == "free":
            self._free_section.set_expanded(expanded)

    def get_section_expanded(self, section_key: str) -> bool:
        if section_key == "core":
            return self._core_section.is_expanded()
        if section_key == "free":
            return self._free_section.is_expanded()
        return True
    # ------------------------------------------------------------------
    # 字段变动
    # ------------------------------------------------------------------
    def _on_search_changed(self, text: str):
        self._search_text = text
        if self._current_node is not None:
            self._rebuild_form()

    def _on_field_changed(self, node: WidgetNode, field: str, value: Any):
        old_value = getattr(node, field, None)
        if old_value == value:
            return
        # 只发信号，由主窗口决定是否 push 到 undo stack
        # 值的真正写入由 EditFieldCommand.redo() 完成
        self.field_edit_committed.emit(node, field, old_value, value)

    def _on_property_changed(self, node: WidgetNode, prop_name: str, value):
        old_value = node.properties.get(prop_name)

        # 布尔值直接保留
        if isinstance(value, bool):
            new_value = value
        else:
            # 空字符串 → 视为删除该属性
            new_value = value if value != "" else None

        if old_value == new_value:
            return
        self.field_edit_committed.emit(
            node, f"prop::{prop_name}", old_value, new_value
        )