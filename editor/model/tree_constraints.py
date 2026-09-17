"""
控件树的布局约束：内置按钮固定在树的顶部和底部，
用户控件不能通过移动/拖拽越过它们。
"""
from typing import Optional

from .widget_node import WidgetNode
from .widget_tree import WidgetTree
from .csv_io import is_builtin_control


def is_builtin(node: Optional[WidgetNode]) -> bool:
    return node is not None and is_builtin_control(node.control_name)


def _find_root_bounds(tree: WidgetTree, exclude: Optional[WidgetNode]):
    """
    返回根级列表中（排除 source 后）第一个/最后一个非内置节点的位置。
    - lower: 第一个非内置节点的 index
    - upper: 最后一个非内置节点的 index + 1（即可插入的最大位置）
    若列表里没有非内置节点，返回 (None, None)。
    """
    roots = tree.roots()
    others = [r for r in roots if r is not exclude]

    lower = None
    for i, r in enumerate(others):
        if not is_builtin(r):
            lower = i
            break

    if lower is None:
        return None, None

    upper = None
    for i in range(len(others) - 1, -1, -1):
        if not is_builtin(others[i]):
            upper = i + 1
            break

    return lower, upper


def clamp_root_insert_index(tree: WidgetTree,
                            source: Optional[WidgetNode],
                            target_index: int) -> Optional[int]:
    """
    计算根级插入的合法 index。
    :param source: 被移动的节点，None 表示新建节点
    :param target_index: 期望插入位置（source 移除后的列表中的 index）
    :return: 合法 index，或 None 表示越界
    """
    lower, upper = _find_root_bounds(tree, exclude=source)
    if lower is None:
        # 没有非内置节点，就没有约束
        return max(0, target_index)
    if target_index < lower or target_index > upper:
        return None
    return target_index


def is_move_allowed(tree: WidgetTree,
                    source: WidgetNode,
                    new_parent: Optional[WidgetNode],
                    new_index: int) -> bool:
    """检查移动是否被允许。"""
    # 内置控件不能被移动
    if is_builtin(source):
        return False

    # 非根级：允许（未来可加"禁止把内置放进分组"之类的约束）
    if new_parent is not None:
        return True

    # 根级：检查是否越过内置按钮
    return clamp_root_insert_index(tree, source, new_index) is not None