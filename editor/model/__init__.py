"""editor 数据层。不依赖 Qt，可独立测试。"""
from .widget_node import WidgetNode
from .widget_tree import WidgetTree
from .validator import ValidationError, validate, has_errors
from .value_resolver import resolve, resolve_property, clear_control_cache
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
    list_functions_for_field,
)
from .function_editor import (
    FunctionLocation,
    locate_function,
    read_function_body,
    write_function_body,
    reload_module,
    guess_owner_class,
    get_module_name,
    function_exists,
    append_function,
    delete_function,
    clear_references,
)
from .props_utils import recompute_props_names
from .diff import (
    DiffReport, NodeDiff, FieldChange, diff_trees,
)
from .variant_registry import list_variants_for, default_variant_for
from .template_generator import generate_all, summarize, collect_function_names

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
    "generate_all",
    "summarize",
    "collect_function_names",
    "resolve",
    "resolve_property",
    "clear_control_cache",
    "FunctionLocation",
    "locate_function",
    "read_function_body",
    "write_function_body",
    "reload_module",
    "guess_owner_class",
    "get_module_name",
    "function_exists",
    "append_function",
    "delete_function",
    "clear_references",
    "list_functions_for_field",
]