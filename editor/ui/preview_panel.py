"""模拟 OBS 脚本控件面板的预览。"""
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QComboBox, QGroupBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QSizePolicy,
)

from editor.model import WidgetTree, WidgetNode


# ----------------------------------------------------------------------
# 内部基类：处理"点击发出节点"逻辑
# ----------------------------------------------------------------------
class _ClickableBase:
    """
    给 QWidget 子类注入"点击发出 node_clicked"能力的辅助方法。
    不是真正的 mixin，而是通过 installEventFilter 到所有子控件。
    """

    def _install_click_forwarding(self, node, signal_emitter):
        self._node = node
        self._signal_emitter = signal_emitter
        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            try:
                self._signal_emitter.emit(self._node)
            except Exception:
                pass
        return super().eventFilter(obj, event)


# ----------------------------------------------------------------------
# 单个控件行
# ----------------------------------------------------------------------
class _PreviewRow(_ClickableBase, QFrame):
    """一行预览：label + value widget（或仅一个控件）。"""

    clicked = Signal(object)  # WidgetNode

    def __init__(self, node: WidgetNode, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(6)

        self._install_click_forwarding(node, self.clicked)

    # ---- 布局辅助 ----
    def add_single(self, widget: QWidget):
        """整行只有一个控件（如 CheckBox / Button）。"""
        self._layout.addWidget(widget)
        self._layout.addStretch()
        widget.installEventFilter(self)

    def add_label(self, text: str, width: int = 140):
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setStyleSheet("color: #888;")
        self._layout.addWidget(label)

    def add_value(self, widget: QWidget):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(widget, 1)
        widget.installEventFilter(self)

    def add_value_pair(self, w1: QWidget, w2: QWidget):
        """路径框：输入框 + 浏览按钮。"""
        w1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(w1, 1)
        self._layout.addWidget(w2)
        w1.installEventFilter(self)
        w2.installEventFilter(self)


class _PreviewGroup(_ClickableBase, QGroupBox):
    """分组框预览。"""

    clicked = Signal(object)

    def __init__(self, node: WidgetNode, parent=None):
        super().__init__(parent)
        title = node.description or node.object_name or node.control_name
        if node.widget_variant == "CHECKABLE":
            self.setCheckable(True)
            self.setChecked(True)
        self.setTitle(title)
        self.setStyleSheet("QGroupBox { margin-top: 8px; }")

        self._install_click_forwarding(node, self.clicked)


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

        # 顶部提示
        self._hint = QLabel("模拟 OBS 控件预览（点击任意控件 → 选中对应节点）")
        self._hint.setStyleSheet(
            "color: #888; padding: 6px; font-size: 11px;"
        )
        self._hint.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._hint)

        # 滚动区
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
        """重建整个预览。"""
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
                # 插到 stretch 之前
                self._host_layout.insertWidget(
                    self._host_layout.count() - 1, w
                )

    def select_by_control_name(self, name: str) -> None:
        """高亮并滚动到指定控件。"""
        # 移除旧高亮
        if self._highlighted and self._highlighted in self._widgets:
            self._set_highlight(self._widgets[self._highlighted], False)

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
        while self._host_layout.count() > 1:  # 保留末尾 stretch
            item = self._host_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _set_highlight(self, w: QWidget, on: bool) -> None:
        if on:
            w.setStyleSheet(
                "border: 1px solid #3a7ebf; border-radius: 3px;"
                " background-color: rgba(58, 126, 191, 0.08);"
            )
        else:
            # 恢复默认样式
            if isinstance(w, QGroupBox):
                w.setStyleSheet("QGroupBox { margin-top: 8px; }")
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
            cb.setChecked(True)
            row.add_single(cb)

        elif cat == "DIGITALBOX":
            row.add_label(label)
            row.add_value(self._make_digital_widget(variant, node))

        elif cat == "TEXTBOX":
            row.add_label(label)
            row.add_value(self._make_text_widget(variant))

        elif cat == "BUTTON":
            btn = QPushButton(label)
            if variant == "URL":
                url = node.properties.get("url", "")
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
            line = QLineEdit("C:\\")
            line.setReadOnly(True)
            btn = QPushButton("...")
            btn.setFixedWidth(32)
            row.add_value_pair(line, btn)

        elif cat == "COLORBOX":
            row.add_label(label)
            color_btn = QPushButton()
            color_btn.setFixedSize(60, 22)
            color_btn.setStyleSheet(
                "background-color: #EA80FF; border: 1px solid #888;"
                " border-radius: 2px;"
            )
            row.add_value(color_btn)

        elif cat == "FONTBOX":
            row.add_label(label)
            font_btn = QPushButton()
            font_btn.setText("Kai 36 Regular")
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
        if variant in ("FLOAT", "FLOAT_SLIDER"):
            w = QDoubleSpinBox()
            w.setRange(0.0, 100.0)
            w.setValue(50.0)
        else:
            w = QSpinBox()
            w.setRange(0, 100)
            w.setValue(50)
        suffix = node.properties.get("suffix", "")
        if suffix:
            w.setSuffix(str(suffix))
        return w

    def _make_text_widget(self, variant: Optional[str]) -> QWidget:
        if variant == "INFO":
            label = QLabel("这是一段只读文本")
            label.setStyleSheet(
                "color: #888; padding: 4px; "
                "background: rgba(0,0,0,0.05); border-radius: 2px;"
            )
            return label
        if variant == "PASSWORD":
            w = QLineEdit()
            w.setEchoMode(QLineEdit.Password)
            w.setText("password")
            return w
        if variant == "MULTILINE":
            w = QPlainTextEdit()
            w.setPlainText("多行文本内容")
            w.setFixedHeight(60)
            return w
        w = QLineEdit("文本内容")
        return w

    def _populate_combo(self, combo: QComboBox, node: WidgetNode) -> None:
        items = node.properties.get("items", [])
        if not isinstance(items, list) or not items:
            combo.addItem("（无选项）")
            return
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("label", item.get("value", "")))
                value = item.get("value")
                combo.addItem(text, value)
        if combo.count() == 0:
            combo.addItem("（无选项）")

    def _populate_list(self, list_widget: QListWidget, node: WidgetNode) -> None:
        items = node.properties.get("items", [])
        if not isinstance(items, list) or not items:
            list_widget.addItem(QListWidgetItem("（无项目）"))
            return
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("value", item.get("label", "")))
                list_widget.addItem(QListWidgetItem(text))

    # ------------------------------------------------------------------
    # 内部：点击转发
    # ------------------------------------------------------------------
    def _on_clicked(self, node: WidgetNode) -> None:
        self.node_clicked.emit(node)