"""QUndoCommand 子类：封装控件树的结构变更，支持撤销/重做。"""
from typing import Optional

from PySide6.QtGui import QUndoCommand

from editor.model import WidgetNode, WidgetTree, recompute_props_names

# ----------------------------------------------------------------------
# EditFieldCommand 的命令 id 分配表
#
# Qt 的 QUndoCommand::id() 签名是 int id() const（32 位有符号），
# 所以不能直接用 Python 的 hash()（可能超出范围）。
# 这里用全局计数器给每个 (node_id, field) 分配稳定的 32 位 id。
# ----------------------------------------------------------------------
_EDIT_FIELD_IDS: dict = {}
_NEXT_EDIT_FIELD_ID: int = 1


def _get_edit_field_id(node, field: str,
                       property_name: Optional[str] = None) -> int:
    global _NEXT_EDIT_FIELD_ID
    key = (id(node), field, property_name)
    if key not in _EDIT_FIELD_IDS:
        _EDIT_FIELD_IDS[key] = _NEXT_EDIT_FIELD_ID
        _NEXT_EDIT_FIELD_ID += 1
        if _NEXT_EDIT_FIELD_ID >= 0x7FFFFFFF:
            _NEXT_EDIT_FIELD_ID = 1
    return _EDIT_FIELD_IDS[key]

class AddNodeCommand(QUndoCommand):
    """添加节点。props_name 由位置自动推导。"""

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
        # 按位置推导 props_name
        recompute_props_names(self._tree, self._node)

    def undo(self):
        self._tree.remove(self._node)


class RemoveNodeCommand(QUndoCommand):
    """删除节点（连同子树）。"""

    def __init__(self, tree: WidgetTree, node: WidgetNode):
        super().__init__(f"删除控件 {node.control_name}")
        self._tree = tree
        self._node = node
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
    """
    移动节点到新位置（同父或跨父）。
    移动后自动重算 props_name，undo 时恢复原值。
    """

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

        # 记录移动前整棵子树的 props_name（用于 undo）
        self._old_props_map = {
            n.control_name: n.props_name for n in node.iter_subtree()
        }

    def redo(self):
        self._tree.move(self._node, self._new_parent, self._new_index)
        # 按新位置推导 props_name
        recompute_props_names(self._tree, self._node)

    def undo(self):
        self._tree.move(self._node, self._old_parent, self._old_index)
        # 恢复旧的 props_name
        for n in self._node.iter_subtree():
            old = self._old_props_map.get(n.control_name)
            if old is not None:
                n.props_name = old


class EditFieldCommand(QUndoCommand):
    """
    编辑控件单个字段。
    同一个 (node, field) 上的连续编辑会通过 mergeWith 合并为一条。

    重要：mergeWith 返回 True 时，Qt 会丢弃新命令，也不会调用新命令的 redo()。
    因此合并时必须手动 setattr + 通知回调，否则属性值会停留在旧值。
    """

    def __init__(self, node, field, old_value, new_value, notify_callback):
        super().__init__(f"编辑 {node.control_name}.{field}")
        self._node = node
        self._field = field
        self._old_value = old_value
        self._new_value = new_value
        self._notify = notify_callback

    def id(self):
        # 相同 (node, field) 的命令可以合并
        # 注意：必须返回 32 位以内 int，Qt 侧 id() 是 C++ int
        return _get_edit_field_id(self._node, self._field)

    def mergeWith(self, other):
        if not isinstance(other, EditFieldCommand):
            return False
        if other._node is not self._node or other._field != self._field:
            return False
        # 保留自己的 old_value，只更新 new_value
        self._new_value = other._new_value
        # Qt 不会调用 other.redo()，所以这里必须手动应用
        setattr(self._node, self._field, self._new_value)
        if self._notify:
            self._notify(self._node, self._field)
        return True

    def redo(self):
        setattr(self._node, self._field, self._new_value)
        if self._notify:
            self._notify(self._node, self._field)

    def undo(self):
        setattr(self._node, self._field, self._old_value)
        if self._notify:
            self._notify(self._node, self._field)