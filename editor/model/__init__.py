"""editor 数据层。不依赖 Qt，可独立测试。"""
from .widget_node import WidgetNode
from .widget_tree import WidgetTree
from .validator import ValidationError, validate, has_errors
from .csv_io import (
    load_tree,
    save_tree,
    read_header,
    default_template_path,
    default_data_path,
    load_default_tree,
)
from .function_registry import (
    list_control_functions,
    list_button_functions,
    list_all_function_names,
)
from .props_utils import recompute_props_names
from .diff import (
    DiffReport, NodeDiff, FieldChange, diff_trees,
)
from .variant_registry import list_variants_for, default_variant_for

__all__ = [
    "WidgetNode",
    "WidgetTree",
    "ValidationError",
    "validate",
    "has_errors",
    "load_tree",
    "save_tree",
    "read_header",
    "default_template_path",
    "default_data_path",
    "load_default_tree",
    "list_control_functions",
    "list_button_functions",
    "list_all_function_names",
    "recompute_props_names",
    "DiffReport",
    "NodeDiff",
    "FieldChange",
    "diff_trees",
    "list_variants_for",
    "default_variant_for",
]