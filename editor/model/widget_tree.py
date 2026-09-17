"""
控件树容器。维护根节点列表 + control_name 索引 + 已用 group_props_name 集合。
"""
from typing import List, Dict, Optional, Set, Iterator

from .widget_node import WidgetNode


class WidgetTree:
    """
    控件树。

    不变量：
    - 所有节点的 control_name 全局唯一
    - 所有分组框的 group_props_name 全局唯一
    - 基础分组名 "props" 永远可用（作为默认属性集）
    """

    BASIC_GROUP_PROPS_NAME = "props"

    def __init__(self) -> None:
        self._roots: List[WidgetNode] = []
        self._index: Dict[str, WidgetNode] = {}
        self._group_props_names: Set[str] = {self.BASIC_GROUP_PROPS_NAME}
        self._group_props_owner: Dict[str, str] = {}   # group_props_name -> control_name

    # ------------------------------------------------------------------
    # 添加 / 移除 / 移动
    # ------------------------------------------------------------------
    def add_root(self, node: WidgetNode, index: Optional[int] = None) -> None:
        """添加根节点。"""
        self._register(node)
        node.parent = None
        node.level = 0
        if index is None:
            self._roots.append(node)
        else:
            self._roots.insert(index, node)

    def add_child(self, parent: WidgetNode, node: WidgetNode,
                  index: Optional[int] = None) -> None:
        """添加为 parent 的子节点。"""
        if parent is None:
            raise ValueError("parent 不能为 None，添加根节点请用 add_root")
        self._register(node)
        parent.add_child(node, index)

    def remove(self, node: WidgetNode) -> None:
        """移除节点（连同其子树）。"""
        for sub in node.iter_subtree():
            self._index.pop(sub.control_name, None)
            if sub.is_group and sub.group_props_name:
                self._group_props_names.discard(sub.group_props_name)
                # 只有当拥有者是 sub 自己时才移除，避免误删其他节点的记录
                if self._group_props_owner.get(sub.group_props_name) == sub.control_name:
                    self._group_props_owner.pop(sub.group_props_name, None)

        if node.parent is not None:
            node.parent.remove_child(node)
        else:
            if node in self._roots:
                self._roots.remove(node)

    def move(self, node: WidgetNode, new_parent: Optional[WidgetNode],
             index: Optional[int] = None) -> None:
        """
        移动节点到新位置。
        new_parent=None 表示移动到根级。
        """
        # 防御：不能移动到自己的子树下
        if new_parent is not None:
            p = new_parent
            while p is not None:
                if p is node:
                    raise ValueError(f"不能把节点 '{node.control_name}' 移动到自己的子树下")
                p = p.parent

        # 先摘除
        if node.parent is not None:
            node.parent.remove_child(node)
        elif node in self._roots:
            self._roots.remove(node)

        # 再挂载
        if new_parent is None:
            self.add_root(node, index)
        else:
            self.add_child(new_parent, node, index)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def find(self, control_name: str) -> Optional[WidgetNode]:
        return self._index.get(control_name)

    def roots(self) -> List[WidgetNode]:
        return list(self._roots)

    def iter_all(self) -> Iterator[WidgetNode]:
        """深度优先遍历整棵树。"""
        for r in self._roots:
            yield from r.iter_subtree()

    def iter_breadth_first(self) -> Iterator[WidgetNode]:
        """广度优先遍历，方便 UI 树展示。"""
        from collections import deque
        q = deque(self._roots)
        while q:
            node = q.popleft()
            yield node
            q.extend(node.children)

    def group_props_names(self) -> Set[str]:
        """所有已注册的 group_props_name（含基础 "props"）。"""
        return set(self._group_props_names)

    def all_control_names(self) -> Set[str]:
        return set(self._index.keys())

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, control_name: str) -> bool:
        return control_name in self._index

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _register(self, node: WidgetNode) -> None:
        """
        注册到索引。

        - control_name 冲突但指向同一个对象时，视为「自己覆盖自己」，跳过。
        - group_props_name 冲突但拥有者是同一个 control_name 时，同样跳过。
        """
        if not node.control_name:
            raise ValueError(f"节点的 control_name 不能为空：{node!r}")

        existing = self._index.get(node.control_name)
        if existing is not None and existing is not node:
            raise ValueError(
                f"control_name '{node.control_name}' 已存在"
                f"（source_line={existing.source_line}）"
            )
        self._index[node.control_name] = node

        if node.is_group and node.group_props_name:
            owner = self._group_props_owner.get(node.group_props_name)
            if owner is not None and owner != node.control_name:
                raise ValueError(
                    f"group_props_name '{node.group_props_name}' 已被 "
                    f"'{owner}' 使用"
                )
            self._group_props_names.add(node.group_props_name)
            self._group_props_owner[node.group_props_name] = node.control_name

    def __repr__(self) -> str:
        return (
            f"WidgetTree(roots={len(self._roots)}, "
            f"total_nodes={len(self._index)}, "
            f"group_props_names={sorted(self._group_props_names)})"
        )