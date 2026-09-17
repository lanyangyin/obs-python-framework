"""
对比两棵 WidgetTree，生成差异报告。

用于「保存前确认」——当前内存中的树 vs 磁盘上的 CSV。
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional

from .widget_node import WidgetNode
from .widget_tree import WidgetTree


# 参与对比的结构化字段
COMPARED_FIELDS = [
    "widget_category",
    "object_name",
    "props_name",
    "description",
    "long_description",
    "group_props_name",
    "widget_variant",
    "modified_callback_enabled",
    "modified_callback",
]


@dataclass
class FieldChange:
    field: str
    old: Any
    new: Any


@dataclass
class NodeDiff:
    control_name: str
    widget_category: str
    field_changes: List[FieldChange] = field(default_factory=list)


@dataclass
class DiffReport:
    added: List[WidgetNode] = field(default_factory=list)
    removed: List[WidgetNode] = field(default_factory=list)
    modified: List[NodeDiff] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.modified)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    def summary(self) -> str:
        if self.is_empty:
            return "无变化"
        return (
            f"新增 {len(self.added)} / "
            f"删除 {len(self.removed)} / "
            f"修改 {len(self.modified)}"
        )


def diff_trees(old_tree: Optional[WidgetTree],
               new_tree: WidgetTree) -> DiffReport:
    """
    生成 old_tree -> new_tree 的差异报告。
    内置按钮不参与对比（它们由框架运行时动态创建）。
    """
    from .csv_io import is_builtin_control

    def _visible(node):
        return not is_builtin_control(node.control_name)

    report = DiffReport()

    if old_tree is None:
        report.added = [n for n in new_tree.iter_all() if _visible(n)]
        return report

    old_index = {n.control_name: n for n in old_tree.iter_all() if _visible(n)}
    new_index = {n.control_name: n for n in new_tree.iter_all() if _visible(n)}

    # old_index = {n.control_name: n for n in old_tree.iter_all()}
    # new_index = {n.control_name: n for n in new_tree.iter_all()}

    for name, node in new_index.items():
        if name not in old_index:
            report.added.append(node)

    for name, node in old_index.items():
        if name not in new_index:
            report.removed.append(node)

    for name in new_index:
        if name not in old_index:
            continue
        old_node = old_index[name]
        new_node = new_index[name]
        changes = _diff_node(old_node, new_node)
        if changes:
            report.modified.append(NodeDiff(
                control_name=name,
                widget_category=new_node.widget_category,
                field_changes=changes,
            ))

    # 稳定排序，便于比对
    report.added.sort(key=lambda n: n.control_name)
    report.removed.sort(key=lambda n: n.control_name)
    report.modified.sort(key=lambda d: d.control_name)
    return report


def _diff_node(old_node: WidgetNode, new_node: WidgetNode) -> List[FieldChange]:
    changes: List[FieldChange] = []

    for f in COMPARED_FIELDS:
        old_v = getattr(old_node, f, None)
        new_v = getattr(new_node, f, None)
        if old_v != new_v:
            changes.append(FieldChange(field=f, old=old_v, new=new_v))

    # 自由属性
    old_props = old_node.properties or {}
    new_props = new_node.properties or {}
    all_keys = set(old_props) | set(new_props)
    for k in sorted(all_keys):
        old_v = old_props.get(k)
        new_v = new_props.get(k)
        if old_v != new_v:
            changes.append(FieldChange(field=f"prop::{k}", old=old_v, new=new_v))

    return changes


def _fmt(value: Any) -> str:
    """把值格式化成单行字符串，用于展示。"""
    if value is None:
        return "（空）"
    if value == "":
        return "（空串）"
    if isinstance(value, bool):
        return "true" if value else "false"
    s = str(value)
    if len(s) > 80:
        return s[:77] + "..."
    return s