"""模拟 OBS 脚本控件面板的预览。"""
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QComboBox, QGroupBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QSizePolicy,
)

from editor.model import (
    WidgetTree, WidgetNode, resolve_property, clear_control_cache,
)


# ----------------------------------------------------------------------
# 类型转换辅助
# ----------------------------------------------------------------------
def _to_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "1", "yes", "y", "on"):
            return True
        if s in ("false", "0", "no", "n", "off"):
            return False
    return default


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_number(value, default: float = 0.0):
    try:
        if isinstance(value, (int, float)):
            return value
        return float(value)
    except (TypeError, ValueError):
        return default


def _info_type_color(info_type) -> str:
    val = info_type
    if hasattr(val, "value"):
        val = val.value
    if hasattr(val, "name"):
        name = val.name
    else:
        name = str(val).upper()
    if "ERROR" in name:
        return "#c44"
    if "WARNING" in name:
        return "#c80"
    return "#3a7ebf"


# ----------------------------------------------------------------------
# visible / enabled 状态
# ----------------------------------------------------------------------
_STATE_NORMAL = "normal"
_STATE_INVISIBLE = "invisible"
_STATE_DISABLED = "disabled"
_STATE_BOTH = "both"


def _compute_state(visible: bool, enabled: bool) -> str:
    if visible and enabled:
        return _STATE_NORMAL
    if not visible and enabled:
        return _STATE_INVISIBLE
    if visible and not enabled:
        return _STATE_DISABLED
    return _STATE_BOTH


def _style_for_state(state: str, is_group: bool = False) -> str:
    base = "QGroupBox { margin-top: 10px; }" if is_group else ""

    if state == _STATE_NORMAL:
        return base

    if state == _STATE_INVISIBLE:
        # 仅 visible=False：红色细虚线
        if is_group:
            return (base +
                "QGroupBox {"
                "  border: 1px dashed #c44;"
                "  background-color: rgba(204, 68, 68, 0.10);"
                "  border-radius: 4px;"
                "  padding-top: 4px;"
                "}")
        return ("border: 1px dashed #c44;"
                " background-color: rgba(204, 68, 68, 0.10);"
                " border-radius: 3px;")

    if state == _STATE_DISABLED:
        # 仅 enabled=False：明显灰底
        if is_group:
            return (base +
                "QGroupBox {"
                "  background-color: rgba(120, 120, 120, 0.18);"
                "  border-radius: 4px;"
                "  padding-top: 4px;"
                "}")
        return ("background-color: rgba(120, 120, 120, 0.18);"
                " border-radius: 3px;")

    # BOTH：红虚线 + 灰底
    if is_group:
        return (base +
            "QGroupBox {"
            "  border: 2px dashed #c44;"
            "  background-color: rgba(120, 120, 120, 0.22);"
            "  border-radius: 4px;"
            "  padding-top: 4px;"
            "}")
    return ("border: 2px dashed #c44;"
            " background-color: rgba(120, 120, 120, 0.22);"
            " border-radius: 3px;")


def _apply_disabled_children(widget: QWidget) -> None:
    """把 widget 的所有后代设为 disabled，视觉灰显。"""
    for child in widget.findChildren(QWidget):
        child.setEnabled(False)

def _style_combo_popup(combo: QComboBox) -> None:
    """
    强制 QComboBox 的下拉列表使用不透明背景。

    QComboBox 的下拉是一个独立顶层 view（QListView），
    全局 QSS 里的 `QComboBox QAbstractItemView` 选择器有时不生效，
    所以直接给 view 单独设置样式。

    颜色优先从全局 QSS 化的 app 取调色板，不依赖 EditorSettings，
    保证在切主题时无需重新构造 combo 也能跟随。
    """
    view = combo.view()
    if view is None:
        return

    view.setAttribute(Qt.WA_TranslucentBackground, False)
    view.setAutoFillBackground(True)

    try:
        from PySide6.QtGui import QPalette as _QPalette
        palette = combo.palette()
        bg = palette.color(_QPalette.ColorRole.Base).name()
        fg = palette.color(_QPalette.ColorRole.Text).name()
        sel_bg = palette.color(_QPalette.ColorRole.Highlight).name()
        sel_fg = palette.color(_QPalette.ColorRole.HighlightedText).name()
    except Exception:
        # 兜底：硬编码浅色
        bg, fg, sel_bg, sel_fg = "#ffffff", "#1e1e1e", "#3a7ebf", "#ffffff"

    view.setStyleSheet(
        "QListView {"
        f"  background-color: {bg};"
        f"  color: {fg};"
        f"  selection-background-color: {sel_bg};"
        f"  selection-color: {sel_fg};"
        "  border: 1px solid #888;"
        "  outline: 0;"
        "}"
        "QListView::item {"
        "  padding: 4px 8px;"
        "}"
        "QListView::item:hover {"
        f"  background-color: {sel_bg};"
        f"  color: {sel_fg};"
        "}"
    )

    combo.setAttribute(Qt.WA_TranslucentBackground, False)


# ----------------------------------------------------------------------
# 单个控件行
# ----------------------------------------------------------------------
class _PreviewRow(QFrame):
    """
    一行预览：label + value widget。

    - 点击子控件或行本身 → clicked.emit(node)
    - 子控件保留自身交互（如 QComboBox 下拉、QListWidget 滚动）
    - tooltip 显示 long_description
    """

    clicked = Signal(object)  # WidgetNode

    def __init__(self, node: WidgetNode, label_color: str = "#888888",
                 parent=None):
        super().__init__(parent)
        self._node = node
        self._label_color = label_color
        self.setFrameShape(QFrame.NoFrame)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(6)

        # 整行 tooltip
        tip = node.long_description or node.description or node.control_name
        self.setToolTip(tip)

    # ---- 点击 ----
    def mousePressEvent(self, event):
        self.clicked.emit(self._node)
        event.accept()

    # ---- 事件过滤：子控件被点击时也触发 clicked ----
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            try:
                self.clicked.emit(self._node)
            except Exception:
                pass
        return super().eventFilter(obj, event)

    # ---- 布局辅助 ----
    def add_single(self, widget: QWidget):
        self._layout.addWidget(widget)
        self._layout.addStretch()
        self._watch(widget)

    def add_label(self, text: str, width: int = 140):
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setStyleSheet(f"color: {self._label_color};")
        self._layout.addWidget(label)
        self._watch(label)

    def add_value(self, widget: QWidget):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(widget, 1)
        self._watch(widget)

    def add_value_pair(self, w1: QWidget, w2: QWidget):
        w1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(w1, 1)
        self._layout.addWidget(w2)
        self._watch(w1)
        self._watch(w2)

    def _watch(self, widget: QWidget):
        """给 widget 及其后代设 tooltip + 装 eventFilter。"""
        if widget is None:
            return
        tip = self._node.long_description or self._node.description or self._node.control_name
        widget.setToolTip(tip)
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.setToolTip(tip)
            child.installEventFilter(self)


# ----------------------------------------------------------------------
# 分组框
# ----------------------------------------------------------------------
class _PreviewGroup(QGroupBox):
    """
    分组框预览。CHECKABLE 变体支持折叠/展开。

    - 点击标题区（顶部约 22px）→ 选中节点 + 切换勾选
    - 点击内容区空白 → 只选中节点
    - 子控件（Row）自己接收点击，不会冒泡到 Group
    """

    clicked = Signal(object)
    TITLE_HEIGHT = 22

    def __init__(self, node: WidgetNode, parent=None):
        super().__init__(parent)
        self._node = node
        self._is_checkable = (node.widget_variant == "CHECKABLE")

        title = node.description or node.object_name or node.control_name
        self.setTitle(title)
        self.setStyleSheet("QGroupBox { margin-top: 10px; }")

        tip = node.long_description or node.description or node.control_name
        self.setToolTip(tip)

        if self._is_checkable:
            self.setCheckable(True)
            self.setChecked(True)
            self.toggled.connect(self._on_toggled)

    def mousePressEvent(self, event):
        if self._is_checkable and event.pos().y() < self.TITLE_HEIGHT:
            self.setChecked(not self.isChecked())
            self.clicked.emit(self._node)
        else:
            self.clicked.emit(self._node)
        event.accept()

    def _on_toggled(self, checked: bool):
        layout = self.layout()
        if layout is None:
            return
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setVisible(checked)


# ----------------------------------------------------------------------
# 主面板
# ----------------------------------------------------------------------
class PreviewPanel(QWidget):
    """模拟 OBS 脚本控件面板的预览。"""

    node_clicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tree: Optional[WidgetTree] = None
        self._widgets: Dict[str, QWidget] = {}
        self._highlighted: Optional[str] = None
        self._label_color: str = "#888888"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        self._hint = QLabel("模拟 OBS 控件预览")
        self._hint.setStyleSheet("color: #888; font-size: 11px;")
        header_layout.addWidget(self._hint)
        header_layout.addStretch()

        btn_refresh = QPushButton("刷新数值")
        btn_refresh.setFixedHeight(22)
        btn_refresh.setStyleSheet("font-size: 11px; padding: 0 8px;")
        btn_refresh.clicked.connect(self._on_refresh)
        header_layout.addWidget(btn_refresh)

        outer.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._host = QWidget()
        self._host_layout = QVBoxLayout(self._host)
        self._host_layout.setContentsMargins(12, 10, 12, 10)
        self._host_layout.setSpacing(4)
        self._host_layout.addStretch()

        self._scroll.setWidget(self._host)
        outer.addWidget(self._scroll)

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def set_label_color(self, color: str) -> None:
        """设置预览中控件标签颜色，立即生效。"""
        if color and color != self._label_color:
            self._label_color = color
            if self._tree is not None:
                self.load_tree(self._tree)

    def load_tree(self, tree: Optional[WidgetTree]) -> None:
        clear_control_cache()
        self._tree = tree
        self._widgets.clear()
        self._highlighted = None
        self._clear()

        if tree is None:
            self._hint.setText("（未加载控件树）")
            return

        # 统计状态
        n_invisible = 0
        n_disabled = 0
        n_both = 0
        for node in tree.iter_all():
            visible = _to_bool(resolve_property(node, "visible", True), default=True)
            enabled = _to_bool(resolve_property(node, "enabled", True), default=True)
            state = _compute_state(visible, enabled)
            if state == _STATE_INVISIBLE:
                n_invisible += 1
            elif state == _STATE_DISABLED:
                n_disabled += 1
            elif state == _STATE_BOTH:
                n_both += 1

        parts = [f"共 {len(tree)} 个控件"]
        if n_invisible:
            parts.append(f"隐藏 {n_invisible}")
        if n_disabled:
            parts.append(f"禁用 {n_disabled}")
        if n_both:
            parts.append(f"隐藏+禁用 {n_both}")
        self._hint.setText(
            "模拟 OBS 控件预览（" + "，".join(parts)
            + "；点击任意控件 → 选中节点）"
        )

        for node in tree.roots():
            w = self._build_node(node)
            if w is not None:
                self._host_layout.insertWidget(
                    self._host_layout.count() - 1, w
                )

    def select_by_control_name(self, name: str) -> None:
        if self._highlighted and self._highlighted in self._widgets:
            self._set_highlight(self._widgets[self._highlighted], False)

        if not name:
            self._highlighted = None
            return

        w = self._widgets.get(name)
        if w is None:
            self._highlighted = None
            return

        self._highlighted = name
        self._set_highlight(w, True)
        self._scroll.ensureWidgetVisible(w)

    # ------------------------------------------------------------------
    # 内部：清空 & 高亮
    # ------------------------------------------------------------------
    def _clear(self) -> None:
        while self._host_layout.count() > 1:
            item = self._host_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _set_highlight(self, w: QWidget, on: bool) -> None:
        if on:
            if isinstance(w, QGroupBox):
                w.setStyleSheet(
                    "QGroupBox {"
                    "  border: 2px solid #3a7ebf;"
                    "  background-color: rgba(58, 126, 191, 0.12);"
                    "  border-radius: 4px;"
                    "  margin-top: 12px;"
                    "  padding-top: 8px;"
                    "}"
                    "QGroupBox::title {"
                    "  color: #3a7ebf;"
                    "  font-weight: 600;"
                    "  subcontrol-origin: margin;"
                    "  subcontrol-position: top left;"
                    "  left: 10px;"
                    "}"
                )
            else:
                w.setStyleSheet(
                    "border: 2px solid #3a7ebf;"
                    " background-color: rgba(58, 126, 191, 0.15);"
                    " border-radius: 3px;"
                )
        else:
            state = w.property("_preview_state") or _STATE_NORMAL
            is_group = isinstance(w, QGroupBox)
            w.setStyleSheet(_style_for_state(state, is_group=is_group))

    # ------------------------------------------------------------------
    # 内部：构建
    # ------------------------------------------------------------------
    def _build_node(self, node: WidgetNode) -> Optional[QWidget]:
        visible = _to_bool(resolve_property(node, "visible", True), default=True)
        enabled = _to_bool(resolve_property(node, "enabled", True), default=True)
        state = _compute_state(visible, enabled)

        if node.widget_category == "GROUP":
            w = self._build_group(node)
        else:
            w = self._build_leaf(node)

        if w is None:
            return None

        is_group = (node.widget_category == "GROUP")
        w.setProperty("_preview_state", state)
        w.setStyleSheet(_style_for_state(state, is_group=is_group))

        if not enabled:
            _apply_disabled_children(w)

        return w

    def _build_group(self, node: WidgetNode) -> QWidget:
        box = _PreviewGroup(node)
        box.clicked.connect(self._on_clicked)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 16, 10, 10)
        layout.setSpacing(4)

        for child in node.children:
            cw = self._build_node(child)
            if cw is not None:
                layout.addWidget(cw)

        self._widgets[node.control_name] = box
        return box

    def _build_leaf(self, node: WidgetNode) -> QWidget:
        row = _PreviewRow(node, label_color=self._label_color)
        row.clicked.connect(self._on_clicked)

        cat = node.widget_category
        variant = node.widget_variant
        label = node.description or node.object_name or node.control_name

        if cat == "CHECKBOX":
            cb = QCheckBox(label)
            cb.setChecked(_to_bool(resolve_property(node, "checked", True), True))
            row.add_single(cb)

        elif cat == "DIGITALBOX":
            row.add_label(label)
            row.add_value(self._make_digital_widget(variant, node))

        elif cat == "TEXTBOX":
            row.add_label(label)
            row.add_value(self._make_text_widget(variant, node))

        elif cat == "BUTTON":
            btn = QPushButton(label)
            if variant == "URL":
                url = resolve_property(node, "url", "")
                btn.setToolTip(f"打开链接: {url}")
                btn.setText(f"{label}  🔗")
            row.add_single(btn)

        elif cat == "COMBOBOX":
            row.add_label(label)
            combo = QComboBox()
            combo.setEditable(variant == "EDITABLE")
            self._populate_combo(combo, node)
            _style_combo_popup(combo)
            row.add_value(combo)

        elif cat == "PATHBOX":
            row.add_label(label)
            path_text = str(resolve_property(node, "path_text", "C:\\") or "")
            line = QLineEdit(path_text)
            line.setReadOnly(True)
            btn = QPushButton("...")
            btn.setFixedWidth(32)
            row.add_value_pair(line, btn)

        elif cat == "COLORBOX":
            row.add_label(label)
            color_btn = QPushButton()
            color_btn.setMinimumHeight(22)
            color_btn.setStyleSheet(
                f"background-color: {self._make_color_hex(node)};"
                " border: 1px solid #888; border-radius: 2px;"
            )
            row.add_value(color_btn)

        elif cat == "FONTBOX":
            row.add_label(label)
            font_btn = QPushButton()
            font_btn.setText(self._make_font_text(node))
            font_btn.setStyleSheet("text-align: left; padding-left: 6px;")
            row.add_value(font_btn)

        elif cat == "LISTBOX":
            row.add_label(label)
            list_widget = QListWidget()
            list_widget.setFixedHeight(80)
            self._populate_list(list_widget, node)
            row.add_value(list_widget)

        else:
            row.add_single(QLabel(f"[{cat}] {label}"))

        self._widgets[node.control_name] = row
        return row

    # ------------------------------------------------------------------
    # 内部：控件填充
    # ------------------------------------------------------------------
    def _make_digital_widget(self, variant: Optional[str], node: WidgetNode) -> QWidget:
        min_val = _to_number(resolve_property(node, "min_val", 0), 0)
        max_val = _to_number(resolve_property(node, "max_val", 100), 100)
        step = _to_number(resolve_property(node, "step", 1), 1)
        value = _to_number(resolve_property(node, "digital", 50), 50)

        is_float = variant in ("FLOAT", "FLOAT_SLIDER")

        if is_float:
            w = QDoubleSpinBox()
            w.setRange(float(min_val), float(max_val))
            w.setSingleStep(float(step) if step else 1.0)
            w.setDecimals(2)
            w.setValue(float(value))
        else:
            w = QSpinBox()
            w.setRange(int(min_val), int(max_val))
            w.setSingleStep(int(step) if step else 1)
            w.setValue(int(value))

        suffix = node.properties.get("suffix", "")
        if suffix and suffix != "X":
            w.setSuffix(str(suffix))
        return w

    def _make_text_widget(self, variant: Optional[str], node: WidgetNode) -> QWidget:
        text = resolve_property(node, "text", "")
        text = str(text) if text is not None else ""

        if variant == "INFO":
            info_type = resolve_property(node, "info_type", None)
            label = QLabel(text or "（只读文本）")
            label.setWordWrap(True)
            color = _info_type_color(info_type)
            label.setStyleSheet(
                f"color: {color}; padding: 4px; "
                "background: rgba(0,0,0,0.05); border-radius: 2px;"
            )
            return label

        if variant == "PASSWORD":
            w = QLineEdit()
            w.setEchoMode(QLineEdit.Password)
            w.setText(text or "password")
            return w

        if variant == "MULTILINE":
            w = QPlainTextEdit()
            w.setPlainText(text or "")
            w.setFixedHeight(60)
            return w

        w = QLineEdit(text)
        return w

    def _populate_combo(self, combo: QComboBox, node: WidgetNode) -> None:
        items = resolve_property(node, "items", [])
        if not isinstance(items, list) or not items:
            combo.addItem("（无选项）")
            return

        current_value = resolve_property(node, "value", None)
        current_label = resolve_property(node, "label", None)

        for item in items:
            if isinstance(item, dict):
                text = str(item.get("label", item.get("value", "")))
                value = item.get("value")
                combo.addItem(text, value)

        if combo.count() == 0:
            combo.addItem("（无选项）")
            return

        if current_value is not None:
            idx = combo.findData(current_value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif current_label is not None:
            idx = combo.findText(str(current_label))
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _populate_list(self, list_widget: QListWidget, node: WidgetNode) -> None:
        items = resolve_property(node, "items", [])
        if not isinstance(items, list) or not items:
            list_widget.addItem(QListWidgetItem("（无项目）"))
            return
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("value", item.get("label", "")))
                it = QListWidgetItem(text)
                if item.get("hidden"):
                    it.setHidden(True)
                if item.get("selected"):
                    it.setSelected(True)
                list_widget.addItem(it)

    # ------------------------------------------------------------------
    # 内部：特殊控件展示
    # ------------------------------------------------------------------
    def _make_color_hex(self, node: WidgetNode) -> str:
        r = _to_int(resolve_property(node, "color_red", 255), 255)
        g = _to_int(resolve_property(node, "color_green", 255), 255)
        b = _to_int(resolve_property(node, "color_blue", 255), 255)
        return f"#{r:02X}{g:02X}{b:02X}"

    def _make_font_text(self, node: WidgetNode) -> str:
        face = resolve_property(node, "font_face", "Kai")
        size = _to_int(resolve_property(node, "font_size", 12), 12)
        style = resolve_property(node, "font_style", "Regular")
        face = str(face) if face else "Kai"
        style = str(style) if style else "Regular"
        return f"{face}  {size}  {style}"

    # ------------------------------------------------------------------
    # 内部：点击转发
    # ------------------------------------------------------------------
    def _on_clicked(self, node: WidgetNode) -> None:
        self.node_clicked.emit(node)

    def _on_refresh(self):
        if self._tree is not None:
            self.load_tree(self._tree)