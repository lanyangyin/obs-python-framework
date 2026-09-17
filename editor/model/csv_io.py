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

from pathlib import Path

# 项目根目录（editor/model/csv_io.py -> editor/model -> editor -> 项目根）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# 框架在运行时动态创建的两个内置按钮（不在 CSV 中）
# 名字是 UTF-8 编码的十六进制字符串
BUILTIN_BUTTONS = [
    {
        "control_name": "e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
        "description": "允许执行控件修改回调",
        "long_description": "允许执行控件修改回调",
        "widget_variant": "DEFAULT",
        "position": "top",
    },
    {
        "control_name": "e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
        "description": "禁止执行控件修改回调",
        "long_description": "禁止执行控件修改回调",
        "widget_variant": "DEFAULT",
        "position": "bottom",
    },
]

BUILTIN_CONTROL_NAMES = {b["control_name"] for b in BUILTIN_BUTTONS}


def is_builtin_control(control_name: str) -> bool:
    return control_name in BUILTIN_CONTROL_NAMES


def default_template_path() -> str:
    """返回 obsScriptFramework_ 内置的控件属性定义文件路径。"""
    return str(
        _PROJECT_ROOT / "obsScriptFramework_" / "src" / "data"
        / "widgetAttributeDefinitionData.csv"
    )


def default_data_path() -> str:
    """返回 obsScriptFramework_ 内置的 widgetData.csv 路径。"""
    return str(
        _PROJECT_ROOT / "obsScriptFramework_" / "plugins" / "widgetData.csv"
    )

# ------------------------------------------------------------------
# 导入
# ------------------------------------------------------------------
def load_tree(template_path: Optional[str] = None,
              data_path: Optional[str] = None,
              initial_props_name: str = "props") -> WidgetTree:
    """
    从两个 CSV 文件加载控件树。
    不传参数时使用 obsScriptFramework_ 内置的默认路径。
    """
    if template_path is None:
        template_path = default_template_path()
    if data_path is None:
        data_path = default_data_path()
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

    _inject_builtin_buttons(tree)
    return tree

def _inject_builtin_buttons(tree: WidgetTree) -> None:
    """
    往树里注入框架的两个内置按钮。
    - 若不存在 → 新建并添加
    - 若已存在（来自旧 CSV）→ 强制修正它们的 properties
    两种情况都确保 visible / enabled 固定为 False（与框架运行时一致）。
    """
    existing = tree.all_control_names()

    def _apply_builtin_props(node: WidgetNode, spec: dict) -> None:
        """强制设置内置按钮的关键属性。"""
        node.description = spec["description"]
        node.long_description = spec["long_description"]
        if spec.get("widget_variant") is not None:
            node.widget_variant = spec["widget_variant"]
        node.properties["visible"] = False
        node.properties["enabled"] = False
        # 其他按钮常见自由属性也初始化一下，避免属性面板只显示两项
        node.properties.setdefault("url", "")
        node.properties.setdefault("click_callback", "")

    def _create(spec: dict) -> WidgetNode:
        node = WidgetNode(
            control_name=spec["control_name"],
            widget_category="BUTTON",
            object_name=spec["control_name"],
            props_name="props",
            description=spec["description"],
            long_description=spec["long_description"],
            widget_variant=spec["widget_variant"],
        )
        _apply_builtin_props(node, spec)
        return node

    top = BUILTIN_BUTTONS[0]
    if top["control_name"] in existing:
        _apply_builtin_props(tree.find(top["control_name"]), top)
    else:
        tree.add_root(_create(top), 0)

    bottom = BUILTIN_BUTTONS[1]
    if bottom["control_name"] in existing:
        _apply_builtin_props(tree.find(bottom["control_name"]), bottom)
    else:
        tree.add_root(_create(bottom), len(tree.roots()))


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


def load_default_tree() -> WidgetTree:
    """加载框架内置的默认控件树，方便快速验证。"""
    return load_tree(default_template_path(), default_data_path())