"""模拟 OBS 脚本控件面板的预览。"""
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QComboBox, QGroupBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QSizePolicy,
)

from editor.model import WidgetTree, WidgetNode, resolve_property, clear_control_cache

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
    """根据 info_type 值返回文字颜色。"""
    # info_type 可能是 TextBoxInfoVariant 枚举、int、或字符串
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
# 单个控件行
# ----------------------------------------------------------------------
class _PreviewRow(QFrame):
    """
    一行预览：label + value widget（或仅一个控件）。

    点击处理：覆写 mousePressEvent；所有子控件设
    `WA_TransparentForMouseEvents`，让事件直接落到 Row 上。
    """

    clicked = Signal(object)  # WidgetNode

    def __init__(self, node: WidgetNode, parent=None):
        super().__init__(parent)
        self._node = node
        self.setFrameShape(QFrame.NoFrame)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(6)

    # ---- 点击 ----
    def mousePressEvent(self, event):
        self.clicked.emit(self._node)
        event.accept()

    # ---- 布局辅助 ----
    def add_single(self, widget: QWidget):
        """整行只有一个控件（如 CheckBox / Button）。"""
        self._layout.addWidget(widget)
        self._layout.addStretch()
        self._make_transparent(widget)

    def add_label(self, text: str, width: int = 140):
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setStyleSheet("color: #888;")
        self._layout.addWidget(label)
        self._make_transparent(label)

    def add_value(self, widget: QWidget):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(widget, 1)
        self._make_transparent(widget)

    def add_value_pair(self, w1: QWidget, w2: QWidget):
        """路径框：输入框 + 浏览按钮。"""
        w1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(w1, 1)
        self._layout.addWidget(w2)
        self._make_transparent(w1)
        self._make_transparent(w2)

    @staticmethod
    def _make_transparent(widget: QWidget):
        """让 widget 及其所有后代的鼠标事件穿透到 Row。"""
        widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        for child in widget.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)


# ----------------------------------------------------------------------
# 分组框
# ----------------------------------------------------------------------
class _PreviewGroup(QGroupBox):
    """
    分组框预览。CHECKABLE 变体支持折叠/展开。

    点击处理：
    - 标题区（顶部约 22px）→ 选中节点 + 切换勾选
    - 内容区空白 → 只选中节点
    - 子控件（Row）会自己接收点击，不会冒泡到 Group
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

        if self._is_checkable:
            self.setCheckable(True)
            self.setChecked(True)
            self.toggled.connect(self._on_toggled)

    # ---- 点击 ----
    def mousePressEvent(self, event):
        if self._is_checkable and event.pos().y() < self.TITLE_HEIGHT:
            # 标题区：切换勾选 + 选中节点
            self.setChecked(not self.isChecked())
            self.clicked.emit(self._node)
        else:
            # 内容区空白：只选中节点
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

    node_clicked = Signal(object)  # WidgetNode

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tree: Optional[WidgetTree] = None
        self._widgets: Dict[str, QWidget] = {}
        self._highlighted: Optional[str] = None

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
    def load_tree(self, tree: Optional[WidgetTree]) -> None:
        clear_control_cache()
        self._tree = tree
        self._widgets.clear()
        self._highlighted = None
        self._clear()

        if tree is None:
            self._hint.setText("（未加载控件树）")
            return

        self._hint.setText(
            f"模拟 OBS 控件预览（{len(tree)} 个控件，点击任意控件 → 选中节点）"
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

    def _on_refresh(self):
        """重新解析所有控件的真实数值。"""
        if self._tree is not None:
            self.load_tree(self._tree)

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
            if isinstance(w, QGroupBox):
                w.setStyleSheet("QGroupBox { margin-top: 10px; }")
            else:
                w.setStyleSheet("")

    # ------------------------------------------------------------------
    # 内部：构建
    # ------------------------------------------------------------------
    def _build_node(self, node: WidgetNode) -> Optional[QWidget]:
        if node.widget_category == "GROUP":
            return self._build_group(node)
        return self._build_leaf(node)

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
        row = _PreviewRow(node)
        row.clicked.connect(self._on_clicked)

        cat = node.widget_category
        variant = node.widget_variant
        label = node.description or node.object_name or node.control_name

        if cat == "CHECKBOX":
            cb = QCheckBox(label)
            checked = _to_bool(resolve_property(node, "checked", True))
            cb.setChecked(checked)
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
            color_btn.setFixedSize(60, 22)
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
        min_val = _to_number(resolve_property(node, "min_val", 0), default=0)
        max_val = _to_number(resolve_property(node, "max_val", 100), default=100)
        step = _to_number(resolve_property(node, "step", 1), default=1)
        value = _to_number(resolve_property(node, "digital", 50), default=50)

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

        # 应用当前值
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
    # 内部：特殊控件的展示
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