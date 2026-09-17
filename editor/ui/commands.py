"""QUndoCommand 子类：封装控件树的结构变更，支持撤销/重做。"""
from typing import Optional

from PySide6.QtGui import QUndoCommand

from editor.model import WidgetNode, WidgetTree


class AddNodeCommand(QUndoCommand):
    """添加节点。"""

    def __init__(self, tree: WidgetTree, node: WidgetNode,
                 parent: Optional[WidgetNode], index: int):
        super().__init__(f"添加控件 {node.control_name}")
        self._tree = tree
        self._node = node
        self._parent = parent
        self._index = index

    def redo(self):
        if self._parent is None:
            self._tree.add_root(self._node, self._index)
        else:
            self._tree.add_child(self._parent, self._node, self._index)

    def undo(self):
        self._tree.remove(self._node)


class RemoveNodeCommand(QUndoCommand):
    """删除节点（连同子树）。"""

    def __init__(self, tree: WidgetTree, node: WidgetNode):
        super().__init__(f"删除控件 {node.control_name}")
        self._tree = tree
        self._node = node
        # 记录原始位置用于撤销
        self._original_parent = node.parent
        if self._original_parent is not None:
            self._original_index = self._original_parent.children.index(node)
        else:
            self._original_index = tree.roots().index(node)

    def redo(self):
        self._tree.remove(self._node)

    def undo(self):
        if self._original_parent is None:
            self._tree.add_root(self._node, self._original_index)
        else:
            self._tree.add_child(self._original_parent, self._node, self._original_index)


class MoveNodeCommand(QUndoCommand):
    """移动节点到新位置（同父或跨父）。"""

    def __init__(self, tree: WidgetTree, node: WidgetNode,
                 new_parent: Optional[WidgetNode], new_index: int):
        super().__init__(f"移动控件 {node.control_name}")
        self._tree = tree
        self._node = node
        self._new_parent = new_parent
        self._new_index = new_index
        self._old_parent = node.parent
        if self._old_parent is not None:
            self._old_index = self._old_parent.children.index(node)
        else:
            self._old_index = tree.roots().index(node)

    def redo(self):
        self._tree.move(self._node, self._new_parent, self._new_index)

    def undo(self):
        self._tree.move(self._node, self._old_parent, self._old_index)