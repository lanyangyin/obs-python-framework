"""左侧控件树面板。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView

from editor.model import WidgetTree, WidgetNode


class TreePanel(QWidget):
    """控件树面板：用 QTreeView 展示 WidgetTree。"""

    node_selected = Signal(object)   # 发出 WidgetNode 或 None

    NODE_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["控件树"])

        self._view = QTreeView()
        self._view.setModel(self._model)
        self._view.setHeaderHidden(True)
        self._view.setEditTriggers(QTreeView.NoEditTriggers)
        self._view.setSelectionBehavior(QTreeView.SelectRows)
        self._view.setAlternatingRowColors(True)
        self._view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._view)

    # ------------------------------------------------------------------
    # 对外
    # ------------------------------------------------------------------
    def load_tree(self, tree: WidgetTree) -> None:
        """重新加载整棵树。"""
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["控件树"])

        root = self._model.invisibleRootItem()
        for node in tree.roots():
            root.appendRow(self._build_item(node))

        self._view.expandAll()
        if tree.roots():
            first_index = self._model.index(0, 0)
            self._view.setCurrentIndex(first_index)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _build_item(self, node: WidgetNode) -> QStandardItem:
        item = QStandardItem(self._format_label(node))
        item.setData(node, self.NODE_ROLE)
        item.setToolTip(self._format_tooltip(node))
        for c in node.children:
            item.appendRow(self._build_item(c))
        return item

    @staticmethod
    def _format_label(node: WidgetNode) -> str:
        parts = [node.object_name or node.control_name or "<unnamed>"]
        parts.append(f"({node.widget_category})")
        if node.is_group and node.group_props_name:
            parts.append(f"[group: {node.group_props_name}]")
        elif node.props_name and node.props_name != "props":
            parts.append(f"[props: {node.props_name}]")
        return " ".join(parts)

    @staticmethod
    def _format_tooltip(node: WidgetNode) -> str:
        lines = [
            f"control_name: {node.control_name}",
            f"object_name: {node.object_name}",
            f"widget_category: {node.widget_category}",
            f"props_name: {node.props_name}",
        ]
        if node.group_props_name:
            lines.append(f"group_props_name: {node.group_props_name}")
        if node.widget_variant:
            lines.append(f"widget_variant: {node.widget_variant}")
        if node.source_line:
            lines.append(f"source_line: {node.source_line}")
        return "\n".join(lines)

    def _on_selection_changed(self, selected, deselected):
        indexes = self._view.selectionModel().selectedIndexes()
        if not indexes:
            self.node_selected.emit(None)
            return
        item = self._model.itemFromIndex(indexes[0])
        if item is None:
            self.node_selected.emit(None)
            return
        self.node_selected.emit(item.data(self.NODE_ROLE))

    def refresh_node_label(self, node) -> None:
        """刷新指定节点在树中的显示文本。"""
        item = self._find_item_by_node(node)
        if item is not None:
            item.setText(self._format_label(node))
            item.setToolTip(self._format_tooltip(node))

    def _find_item_by_node(self, node):
        """深度优先查找树中持有指定 WidgetNode 的 QStandardItem。"""
        root = self._model.invisibleRootItem()
        for i in range(root.rowCount()):
            found = self._search_item(root.child(i), node)
            if found is not None:
                return found
        return None

    def _search_item(self, item, node):
        if item is None:
            return None
        if item.data(self.NODE_ROLE) is node:
            return item
        for i in range(item.rowCount()):
            found = self._search_item(item.child(i), node)
            if found is not None:
                return found
        return None