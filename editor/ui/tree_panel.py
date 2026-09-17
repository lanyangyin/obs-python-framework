"""左侧控件树面板。支持拖拽排序，所有结构变更走 MoveNodeCommand。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel, QBrush, QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QAbstractItemView,
    QMenu, QApplication,
)
from editor.model import WidgetTree, WidgetNode


class _DragDropTreeView(QTreeView):
    """
    重写 dropEvent，不调用 super()，把拖放转换成信号。
    由 TreePanel 计算新的 (parent, index)，最终走 MoveNodeCommand。
    """

    # source_node, target_node (or None), drop_position_int
    drop_computed = Signal(object, object, int)

    def dropEvent(self, event):
        indexes = self.selectionModel().selectedIndexes()
        if not indexes:
            event.ignore()
            return

        source_item = self.model().itemFromIndex(indexes[0])
        source_node = (
            source_item.data(TreePanel.NODE_ROLE) if source_item else None
        )
        if source_node is None:
            event.ignore()
            return

        drop_index = self.indexAt(event.position().toPoint())
        pos = self.dropIndicatorPosition()

        target_item = (
            self.model().itemFromIndex(drop_index)
            if drop_index.isValid() else None
        )
        target_node = (
            target_item.data(TreePanel.NODE_ROLE) if target_item else None
        )
        pos_int = pos.value

        # 阻止 Qt 内置的 move 逻辑（它会直接改 QStandardItemModel，
        # 绕过我们的 WidgetTree 和 QUndoStack）
        event.accept()
        event.setDropAction(Qt.IgnoreAction)

        # 关键：把处理延后到事件循环下一轮。
        # 因为在 dropEvent 里同步重建 model 会让 Qt 内部拖放状态错乱，
        # 表现为"节点消失"（其实数据已经改了，只是视图没刷新正确）。
        from PySide6.QtCore import QTimer
        QTimer.singleShot(
            0,
            lambda: self.drop_computed.emit(source_node, target_node, pos_int),
        )


class TreePanel(QWidget):
    """控件树面板：QTreeView 展示 WidgetTree，支持拖拽排序。"""

    NODE_ROLE = Qt.UserRole + 1

    node_selected = Signal(object)                     # WidgetNode or None
    node_move_requested = Signal(object, object, int)  # source, new_parent, new_index
    # 右键菜单信号：由 MainWindow 接，复用已有 action
    context_add_requested = Signal(object)       # node or None（None 表示插到根末尾）
    context_add_child_requested = Signal(object) # parent_node（仅 GROUP）
    context_remove_requested = Signal(object)    # node
    context_move_up_requested = Signal(object)   # node
    context_move_down_requested = Signal(object) # node

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tree: WidgetTree = None

        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["控件树"])

        self._view = _DragDropTreeView()
        self._view.setModel(self._model)
        self._view.setHeaderHidden(True)
        self._view.setEditTriggers(QTreeView.NoEditTriggers)
        self._view.setSelectionBehavior(QTreeView.SelectRows)
        self._view.setAlternatingRowColors(True)

        # 启用内部移动拖放
        self._view.setDragEnabled(True)
        self._view.setAcceptDrops(True)
        self._view.setDropIndicatorShown(True)
        self._view.setDragDropMode(QAbstractItemView.InternalMove)
        self._view.setDefaultDropAction(Qt.MoveAction)

        self._view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._view.drop_computed.connect(self._on_drop_computed)

        # 右键菜单
        self._view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._view.customContextMenuRequested.connect(self._on_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._view)

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def load_tree(self, tree: WidgetTree) -> None:
        self._tree = tree
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["控件树"])

        root = self._model.invisibleRootItem()
        for node in tree.roots():
            root.appendRow(self._build_item(node))

        self._view.expandAll()
        if tree.roots():
            first_index = self._model.index(0, 0)
            self._view.setCurrentIndex(first_index)

    def refresh_node_label(self, node: WidgetNode) -> None:
        item = self._find_item_by_node(node)
        if item is not None:
            item.setText(self._format_label(node))
            item.setToolTip(self._format_tooltip(node))

    def select_by_control_name(self, control_name: str) -> bool:
        for item in self._iter_items():
            node = item.data(self.NODE_ROLE)
            if node is not None and node.control_name == control_name:
                self._view.setCurrentIndex(item.index())
                self._view.scrollTo(item.index())
                return True
        return False

    def apply_validation(self, errors) -> None:
        from editor.logging_config import get_logger, log_exception
        log = get_logger()
        try:
            by_name = {}
            for e in errors:
                by_name.setdefault(e.control_name, []).append(e)

            for item in self._iter_items():
                node = item.data(self.NODE_ROLE)
                if node is None:
                    continue
                node_errors = by_name.get(node.control_name, [])
                if any(e.severity == "error" for e in node_errors):
                    self._set_item_color(item, "#c44")
                elif any(e.severity == "warning" for e in node_errors):
                    self._set_item_color(item, "#c80")
                else:
                    self._set_item_color(item, None)
        except Exception as e:
            log_exception(log, "apply_validation 失败", e)
            raise

    # ------------------------------------------------------------------
    # 内部：构建
    # ------------------------------------------------------------------
    def _build_item(self, node: WidgetNode) -> QStandardItem:
        item = QStandardItem(self._format_label(node))
        item.setData(node, self.NODE_ROLE)
        item.setToolTip(self._format_tooltip(node))
        # 允许拖拽 & 作为 drop target
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
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

    # ------------------------------------------------------------------
    # 内部：遍历 / 工具
    # ------------------------------------------------------------------
    def _iter_items(self):
        root = self._model.invisibleRootItem()
        for i in range(root.rowCount()):
            yield from self._iter_subtree(root.child(i))

    def _iter_subtree(self, item):
        if item is None:
            return
        yield item
        for i in range(item.rowCount()):
            yield from self._iter_subtree(item.child(i))

    def _find_item_by_node(self, node):
        for item in self._iter_items():
            if item.data(self.NODE_ROLE) is node:
                return item
        return None

    def _set_item_color(self, item, hex_color):
        if hex_color is None:
            item.setForeground(QBrush())
        else:
            item.setForeground(QBrush(QColor(hex_color)))

    # ------------------------------------------------------------------
    # 信号处理
    # ------------------------------------------------------------------
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

    def _on_drop_computed(self, source_node, target_node, pos_int):
        """把 drop 位置转换成 (new_parent, new_index)，发信号给主窗口。"""
        if self._tree is None:
            return

        pos = QAbstractItemView.DropIndicatorPosition(pos_int)

        # 1. 计算 siblings 和 raw_target_idx（移除 source 之前的索引）
        is_append = False
        if target_node is None:
            new_parent = None
            siblings = self._tree.roots()
            raw_target_idx = len(siblings)
            is_append = True
        elif pos == QAbstractItemView.OnItem:
            if target_node.is_group:
                new_parent = target_node
                siblings = target_node.children
                raw_target_idx = len(siblings)
                is_append = True
            else:
                # 非 GROUP 不支持放进去，退化为放到它后面
                new_parent = target_node.parent
                siblings = (
                    new_parent.children if new_parent is not None
                    else self._tree.roots()
                )
                raw_target_idx = siblings.index(target_node) + 1
        elif pos == QAbstractItemView.AboveItem:
            new_parent = target_node.parent
            siblings = (
                new_parent.children if new_parent is not None
                else self._tree.roots()
            )
            raw_target_idx = siblings.index(target_node)
        elif pos == QAbstractItemView.BelowItem:
            new_parent = target_node.parent
            siblings = (
                new_parent.children if new_parent is not None
                else self._tree.roots()
            )
            raw_target_idx = siblings.index(target_node) + 1
        else:
            return

        # 2. 防御：不能把节点放进自己的子树
        if new_parent is not None:
            p = new_parent
            while p is not None:
                if p is source_node:
                    return
                p = p.parent

        # 3. 修正：同一父级且 source 在 target 之前时，移除 source 会让索引 -1
        new_index = raw_target_idx
        if source_node.parent is new_parent and not is_append:
            try:
                source_idx = siblings.index(source_node)
            except ValueError:
                source_idx = -1
            if 0 <= source_idx < raw_target_idx:
                new_index = raw_target_idx - 1

        # 4. 空操作检测
        if source_node.parent is new_parent:
            try:
                current_idx = siblings.index(source_node)
            except ValueError:
                current_idx = -1
            if current_idx == new_index:
                return

        self.node_move_requested.emit(source_node, new_parent, new_index)

    # ------------------------------------------------------------------
    # 右键菜单
    # ------------------------------------------------------------------
    def _on_context_menu(self, pos):
        """在树视图的 pos 位置弹出右键菜单。"""
        index = self._view.indexAt(pos)

        # 先选中被点击的节点（无节点则清空选中）
        if index.isValid():
            self._view.setCurrentIndex(index)
            item = self._model.itemFromIndex(index)
            node = item.data(self.NODE_ROLE) if item else None
        else:
            self._view.clearSelection()
            self._view.setCurrentIndex(self._model.index(-1, -1))
            node = None

        menu = QMenu(self)

        # 新建（同级 / 子级）
        act_add = menu.addAction("新建控件")
        act_add.triggered.connect(
            lambda: self.context_add_requested.emit(node)
        )

        act_add_child = menu.addAction("新建子控件")
        can_add_child = node is not None and node.is_group
        act_add_child.setEnabled(can_add_child)
        act_add_child.triggered.connect(
            lambda: self.context_add_child_requested.emit(node)
        )

        menu.addSeparator()

        # 删除
        act_remove = menu.addAction("删除")
        act_remove.setEnabled(node is not None)
        act_remove.triggered.connect(
            lambda: self.context_remove_requested.emit(node)
        )

        # 上移 / 下移
        can_up, can_down = self._calc_move_states(node)
        act_up = menu.addAction("上移")
        act_up.setEnabled(can_up)
        act_up.triggered.connect(
            lambda: self.context_move_up_requested.emit(node)
        )

        act_down = menu.addAction("下移")
        act_down.setEnabled(can_down)
        act_down.triggered.connect(
            lambda: self.context_move_down_requested.emit(node)
        )

        menu.addSeparator()

        # 展开 / 折叠
        act_expand = menu.addAction("展开全部")
        act_expand.triggered.connect(self._view.expandAll)

        act_collapse = menu.addAction("折叠全部")
        act_collapse.triggered.connect(self._view.collapseAll)

        menu.addSeparator()

        # 复制 control_name
        act_copy = menu.addAction("复制 control_name")
        act_copy.setEnabled(node is not None)
        act_copy.triggered.connect(
            lambda: self._copy_control_name(node)
        )

        menu.exec(self._view.viewport().mapToGlobal(pos))

    def _calc_move_states(self, node):
        """返回 (can_up, can_down)。"""
        if node is None or self._tree is None:
            return False, False
        parent = node.parent
        siblings = parent.children if parent is not None else self._tree.roots()
        try:
            idx = siblings.index(node)
        except ValueError:
            return False, False
        return idx > 0, idx < len(siblings) - 1

    def _copy_control_name(self, node):
        if node is None:
            return
        QApplication.clipboard().setText(node.control_name)