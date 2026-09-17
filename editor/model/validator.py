"""
控件树校验器。
独立于 obsScriptFramework_ 的 ControlManager，只复用其校验规则，
避免 editor 依赖 OBS 运行时。
"""
from dataclasses import dataclass
from typing import List, Set, Dict, Optional

from .widget_node import WidgetNode
from .widget_tree import WidgetTree


@dataclass
class ValidationError:
    """一条校验错误。"""
    control_name: str
    field: str
    message: str
    severity: str = "error"   # "error" / "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.control_name}.{self.field}: {self.message}"


# 保留名称：基础分组
RESERVED_CONTROL_NAMES = {"group"}

# 字段适用范围（与 UIUpdater 的属性适用性一致）
# key: (widget_category, widget_variant)，value: 不支持的字段集合
UNSUPPORTED_FIELDS: Dict[tuple, Set[str]] = {
    ("GROUP", "NORMAL"): {"checked"},
    ("TEXTBOX", "DEFAULT"): {"info_type"},
    ("TEXTBOX", "PASSWORD"): {"info_type"},
    ("TEXTBOX", "MULTILINE"): {"info_type"},
}


def validate(tree: WidgetTree) -> List[ValidationError]:
    """
    对整棵树做全面校验。返回按严重程度排序的错误列表。

    校验规则：
    1. control_name 非空，全局唯一，不为保留名
    2. group_props_name 非空且全局唯一，且不等于所属 group 的 props_name
    3. 每个控件的 props_name 必须来自某个 group 的 group_props_name（含基础 "props"）
    4. group_props_name 必须被某个子控件引用（孤儿分组警告）
    5. 自由属性组合法性：不支持的属性出现时给出警告
    6. 必填字段（根据模板）非空——MVP 阶段先不做，由 csv_io 保证
    """
    from .csv_io import is_builtin_control

    errors: List[ValidationError] = []

    # ---------- 1. control_name 唯一性 ----------
    seen_control_names: Dict[str, WidgetNode] = {}
    for node in tree.iter_all():
        if is_builtin_control(node.control_name):
            continue
        if not node.control_name:
            errors.append(ValidationError(
                control_name="<unknown>", field="control_name",
                message=f"第 {node.source_line} 行控件缺少 control_name",
            ))
            continue
        if node.control_name in RESERVED_CONTROL_NAMES:
            errors.append(ValidationError(
                control_name=node.control_name, field="control_name",
                message=f"control_name '{node.control_name}' 是保留名称",
            ))
        if node.control_name in seen_control_names:
            prev = seen_control_names[node.control_name]
            errors.append(ValidationError(
                control_name=node.control_name, field="control_name",
                message=f"control_name 重复，已在第 {prev.source_line} 行出现",
            ))
        else:
            seen_control_names[node.control_name] = node

    # ---------- 2. group_props_name 校验 ----------
    seen_group_names: Dict[str, WidgetNode] = {}
    for node in tree.iter_all():
        if is_builtin_control(node.control_name):
            continue
        if not node.is_group:
            continue
        gpn = node.group_props_name
        if not gpn:
            errors.append(ValidationError(
                control_name=node.control_name, field="group_props_name",
                message="分组框缺少 group_props_name",
            ))
            continue
        if gpn == node.props_name:
            errors.append(ValidationError(
                control_name=node.control_name, field="group_props_name",
                message=f"group_props_name '{gpn}' 不能等于所属 props_name",
            ))
        if gpn in seen_group_names:
            prev = seen_group_names[gpn]
            errors.append(ValidationError(
                control_name=node.control_name, field="group_props_name",
                message=f"group_props_name '{gpn}' 重复，已在 '{prev.control_name}' 使用",
            ))
        else:
            seen_group_names[gpn] = node

    # ---------- 3. props_name 有效性 ----------
    available_props = tree.group_props_names()  # 含基础 "props"
    for node in tree.iter_all():
        if is_builtin_control(node.control_name):
            continue
        if node.props_name not in available_props:
            errors.append(ValidationError(
                control_name=node.control_name, field="props_name",
                message=(
                    f"props_name '{node.props_name}' 无效。"
                    f"可用值: {sorted(available_props)}"
                ),
            ))

    # ---------- 4. 孤儿 group_props_name（警告） ----------
    used_props: Set[str] = set()
    for node in tree.iter_all():
        if is_builtin_control(node.control_name):
            continue
        used_props.add(node.props_name)
    for gpn, node in seen_group_names.items():
        if gpn not in used_props:
            errors.append(ValidationError(
                control_name=node.control_name, field="group_props_name",
                message=f"group_props_name '{gpn}' 未被任何子控件使用",
                severity="warning",
            ))

    # ---------- 5. 自由属性适用性（警告） ----------
    for node in tree.iter_all():
        if is_builtin_control(node.control_name):
            continue
        variant = node.widget_variant
        unsupported = UNSUPPORTED_FIELDS.get((node.widget_category, variant), set())
        for prop_name in node.properties.keys():
            if prop_name in unsupported:
                errors.append(ValidationError(
                    control_name=node.control_name, field=prop_name,
                    message=(
                        f"控件类型 {node.widget_category}/{variant} 不支持属性 "
                        f"'{prop_name}'，运行时会被跳过"
                    ),
                    severity="warning",
                ))

    # ---------- 排序：error 优先，然后按 control_name ----------
    errors.sort(key=lambda e: (0 if e.severity == "error" else 1, e.control_name))
    return errors


def has_errors(errors: List[ValidationError]) -> bool:
    return any(e.severity == "error" for e in errors)