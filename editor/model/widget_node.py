"""
控件树节点数据模型。
每个 WidgetNode 对应 widgetData.csv 里的一行控件定义。
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Iterator


# 这些字段有专门的结构化存储，不放进 properties 字典
_CORE_FIELDS = {
    "control_name",
    "widget_category",
    "object_name",
    "original_name",
    "description",
    "long_description",
    "widget_variant",
    "modified_callback_enabled",
    "modified_callback",
    "props_name",
    "group_props_name",
    "level",
    "source_line",
}


@dataclass
class WidgetNode:
    """
    控件树节点。

    核心字段（强类型）：
        control_name: 全局唯一标识
        widget_category: 控件分类（如 "CHECKBOX"）
        object_name: 分类内唯一对象名（不含 → 前缀）
        props_name: 所属属性集名
        description / long_description: 展示文本
        group_props_name: 仅分组框有，子控件的 props_name 指向它
        widget_variant: 变体字符串（如 "INT_SLIDER"），也可是 None
        modified_callback_enabled / modified_callback: 值变化回调
        source_line: 源 CSV 行号（导入时记录）
        level: 在树中的深度（根为 0）

    其他所有 CSV 字段（suffix, min_val, filter_str, url, checked 等）
    统一放到 properties 字典里，保持灵活性。
    """
    control_name: str = ""
    widget_category: str = ""
    object_name: str = ""
    props_name: str = "props"

    description: str = ""
    long_description: str = ""

    group_props_name: Optional[str] = None
    widget_variant: Optional[str] = None

    modified_callback_enabled: bool = False
    modified_callback: Optional[str] = None
    """CSV 中配置的回调函数名（原始字符串）"""
    modified_callback_display: Optional[str] = None
    """用于展示的回调名，通常等同于 modified_callback"""

    source_line: int = 0
    level: int = 0

    properties: Dict[str, Any] = field(default_factory=dict)

    children: List["WidgetNode"] = field(default_factory=list)
    parent: Optional["WidgetNode"] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # 树操作
    # ------------------------------------------------------------------
    def add_child(self, child: "WidgetNode", index: Optional[int] = None) -> None:
        """把 child 挂到本节点下。如果 index 为 None 则追加到末尾。"""
        if child.parent is not None:
            child.parent.remove_child(child)
        child.parent = self
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
        self._recompute_levels()

    def remove_child(self, child: "WidgetNode") -> None:
        """从本节点移除 child。"""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self._recompute_levels()

    def iter_subtree(self) -> Iterator["WidgetNode"]:
        """深度优先遍历（含自身）。"""
        yield self
        for c in self.children:
            yield from c.iter_subtree()

    def _recompute_levels(self) -> None:
        """从本节点向下重算 level。"""
        for c in self.children:
            c.level = self.level + 1
            c._recompute_levels()

    # ------------------------------------------------------------------
    # 序列化
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典（供调试或 JSON 序列化）。"""
        return {
            "control_name": self.control_name,
            "widget_category": self.widget_category,
            "object_name": self.object_name,
            "props_name": self.props_name,
            "description": self.description,
            "long_description": self.long_description,
            "group_props_name": self.group_props_name,
            "widget_variant": self.widget_variant,
            "modified_callback_enabled": self.modified_callback_enabled,
            "modified_callback": self.modified_callback,
            "source_line": self.source_line,
            "level": self.level,
            "properties": dict(self.properties),
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_parsed_dict(cls, d: Dict[str, Any]) -> "WidgetNode":
        """
        从 ControlTemplateParser 的输出字典构建节点（不含 children）。
        children 由调用方递归构建。
        """
        # 合并所有分组：group_0 在 properties，其他在 group_properties
        merged: Dict[str, Any] = {}
        merged.update(d.get("properties", {}) or {})
        for group_props in (d.get("group_properties") or {}).values():
            merged.update(group_props or {})

        node = cls(
            control_name=merged.get("control_name", "") or "",
            widget_category=d.get("widget_category", "") or "",
            object_name=d.get("object_name", "") or "",
            props_name=d.get("props_name", "props") or "props",
            description=merged.get("description", "") or "",
            long_description=merged.get("long_description", "") or "",
            group_props_name=d.get("group_props_name"),
            widget_variant=merged.get("widget_variant"),
            modified_callback_enabled=bool(merged.get("modified_callback_enabled", False)),
            modified_callback=merged.get("modified_callback"),
            source_line=d.get("source_line", 0),
            level=d.get("level", 0),
        )

        # 其他字段进 properties
        for k, v in merged.items():
            if k in _CORE_FIELDS:
                continue
            if v is None:
                continue
            node.properties[k] = v

        return node

    # ------------------------------------------------------------------
    # 便捷属性
    # ------------------------------------------------------------------
    @property
    def is_group(self) -> bool:
        return self.widget_category == "GROUP"

    @property
    def is_root(self) -> bool:
        return self.parent is None

    def __repr__(self) -> str:
        return (
            f"WidgetNode(control_name={self.control_name!r}, "
            f"category={self.widget_category!r}, "
            f"level={self.level}, "
            f"children={len(self.children)})"
        )