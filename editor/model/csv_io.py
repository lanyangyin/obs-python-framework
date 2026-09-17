"""
CSV 读写：直接复用 obsScriptFramework_ 的 ControlTemplateParser。

- load_tree: 调用 parser.parse_csv_files -> 构建 WidgetTree
- save_tree: 遍历 WidgetTree -> 按模板 HEADER 生成 CSV 行
"""
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# 复用框架的解析器
from src.tool.scriptCsv2Json import ControlTemplateParser

from .widget_node import WidgetNode
from .widget_tree import WidgetTree


# ------------------------------------------------------------------
# 导入
# ------------------------------------------------------------------
def load_tree(template_path: str, data_path: str,
              initial_props_name: str = "props") -> WidgetTree:
    """
    从两个 CSV 文件加载控件树。

    :param template_path: widgetAttributeDefinitionData.csv 路径
    :param data_path: widgetData.csv 路径
    :param initial_props_name: 根级控件默认的 props_name
    :return: WidgetTree 实例
    :raises ValueError: 解析失败（文件为空、表头不一致、字段缺失等）
    """
    parser = ControlTemplateParser()
    result = parser.parse_csv_files(template_path, data_path,
                                    initial_props_name=initial_props_name)

    tree = WidgetTree()

    def _build(node_dict: Dict[str, Any], parent: Optional[WidgetNode]) -> WidgetNode:
        node = WidgetNode.from_parsed_dict(node_dict)
        if parent is None:
            tree.add_root(node)
        else:
            tree.add_child(parent, node)
        for child_dict in node_dict.get("children", []) or []:
            _build(child_dict, node)
        return node

    for root_dict in result.get("tree", []) or []:
        _build(root_dict, None)

    return tree


# ------------------------------------------------------------------
# 导出
# ------------------------------------------------------------------
def read_header(template_path: str) -> List[str]:
    """读取模板文件的第一行作为 HEADER。"""
    with open(template_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def save_tree(tree: WidgetTree, template_path: str, data_path: str) -> None:
    """
    把 WidgetTree 序列化回 widgetData.csv。

    :param tree: 控件树
    :param template_path: widgetAttributeDefinitionData.csv 路径（用于读 HEADER）
    :param data_path: 输出的 widgetData.csv 路径
    """
    header = read_header(template_path)
    rows: List[List[str]] = [header]

    for node in tree.iter_all():
        rows.append(_node_to_row(node, header))

    with open(data_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def _node_to_row(node: WidgetNode, header: List[str]) -> List[str]:
    """
    把一个节点序列化成一行 CSV。

    以 header 为骨架，把节点各字段填到对应列。
    分组标记列（"|" / "||"）留空。
    """
    row = [""] * len(header)

    # 计算所有可写的列：把 node 的核心字段和 properties 合并
    values: Dict[str, str] = {
        "control_name": node.control_name,
        "widget_category": node.widget_category,
        "object_name": "→" * node.level + node.object_name,
        "description": node.description,
        "long_description": node.long_description,
        "widget_variant": node.widget_variant or "",
        "modified_callback_enabled": _to_csv_scalar(node.modified_callback_enabled),
        "modified_callback": node.modified_callback or "",
        "props_name": node.props_name,
        "group_props_name": node.group_props_name or "",
    }

    # 把 properties 里的字段并入
    for k, v in node.properties.items():
        values[k] = _to_csv_scalar(v)

    for i, col_name in enumerate(header):
        if col_name in ("|", "||"):
            continue  # 分组标记列留空
        if col_name in values:
            row[i] = values[col_name]

    return row


def _to_csv_scalar(value: Any) -> str:
    """把 Python 值转成 CSV 单元格字符串。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    # 列表、字典等复杂类型，用 JSON 序列化
    import json
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)