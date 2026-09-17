"""editor 数据层。不依赖 Qt，可独立测试。"""
from .widget_node import WidgetNode
from .widget_tree import WidgetTree
from .validator import ValidationError, validate, has_errors
from .csv_io import load_tree, save_tree, read_header

__all__ = [
    "WidgetNode",
    "WidgetTree",
    "ValidationError",
    "validate",
    "has_errors",
    "load_tree",
    "save_tree",
    "read_header",
]