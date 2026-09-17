"""
根据控件在树中的位置，重新计算 props_name。

规则（与 ControlTemplateParser 的推导逻辑保持一致）：
- 根级控件的 props_name = 基础分组名（默认 "props"）
- 子控件的 props_name = parent.props_name
- 但若 parent 是 GROUP 且有 group_props_name，
  则子控件的 props_name = parent.group_props_name
- 递归处理整棵子树
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .widget_node import WidgetNode
    from .widget_tree import WidgetTree


def recompute_props_names(tree: "WidgetTree", node: "WidgetNode") -> None:
    """
    根据 node 在 tree 中的新位置，重新计算它及整棵子树的 props_name。
    node 必须已经在树中（parent 已设好）。
    """
    if node.parent is None:
        target = tree.BASIC_GROUP_PROPS_NAME  # "props"
    else:
        target = _target_props_for_child_of(node.parent)

    _apply_recursive(node, target)


def _target_props_for_child_of(parent: "WidgetNode") -> str:
    """给定父节点，返回其直接子控件应有的 props_name。"""
    if parent.is_group and parent.group_props_name:
        return parent.group_props_name
    return parent.props_name


def _apply_recursive(node: "WidgetNode", props_name: str) -> None:
    """递归设置 node 及其子树的 props_name。"""
    node.props_name = props_name
    # 如果 node 自己是 GROUP，它的子控件的 props_name 应指向它自己的 group_props_name
    if node.is_group and node.group_props_name:
        child_props = node.group_props_name
    else:
        child_props = props_name
    for child in node.children:
        _apply_recursive(child, child_props)