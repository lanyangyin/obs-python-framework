"""
编辑 obsScriptFramework_ 里回调函数的源码。

涉及两个文件：
- plugins/ControlFunction.py -> ControlDataSetFunction
- plugins/ButtonFunction.py  -> BtnFunction
"""
import ast
import importlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_log = logging.getLogger("editor")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PLUGINS_DIR = _PROJECT_ROOT / "obsScriptFramework_" / "plugins"

CONTROL_FILE = _PLUGINS_DIR / "ControlFunction.py"
BUTTON_FILE = _PLUGINS_DIR / "ButtonFunction.py"

MODULE_MAP = {
    "ControlDataSetFunction": (CONTROL_FILE, "plugins.ControlFunction"),
    "BtnFunction": (BUTTON_FILE, "plugins.ButtonFunction"),
}


@dataclass
class FunctionLocation:
    source_path: Path
    module_name: str
    class_name: str
    function_name: str
    body_start_line: int
    body_end_line: int
    indent: int
    signature: str


def _parse_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")
    source = path.read_text(encoding="utf-8")
    return source, ast.parse(source)


def _find_class(tree, class_name: str):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def _find_function(class_node, func_name: str):
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == func_name:
                return item
    return None


def locate_function(function_name: str,
                    owner_class: str = "ControlDataSetFunction") -> FunctionLocation:
    """在指定类里定位方法。失败时抛 FileNotFoundError / ValueError。"""
    if owner_class not in MODULE_MAP:
        raise ValueError(f"未知的类：{owner_class}")

    source_path, module_name = MODULE_MAP[owner_class]
    source, tree = _parse_file(source_path)

    class_node = _find_class(tree, owner_class)
    if class_node is None:
        raise ValueError(f"文件中未找到类 '{owner_class}'：{source_path}")

    func_node = _find_function(class_node, function_name)
    if func_node is None:
        raise ValueError(f"类 '{owner_class}' 中未找到方法 '{function_name}'")

    if not func_node.body:
        raise ValueError(f"方法 '{function_name}' 没有函数体")

    body_start = func_node.body[0].lineno
    body_end = func_node.end_lineno
    indent = func_node.body[0].col_offset

    source_lines = source.splitlines()
    sig_start = func_node.lineno - 1
    for dec in func_node.decorator_list:
        sig_start = min(sig_start, dec.lineno - 1)
    signature = "\n".join(source_lines[sig_start: body_start - 1])

    return FunctionLocation(
        source_path=source_path,
        module_name=module_name,
        class_name=owner_class,
        function_name=function_name,
        body_start_line=body_start,
        body_end_line=body_end,
        indent=indent,
        signature=signature,
    )


def read_function_body(loc: FunctionLocation) -> str:
    """读取函数体（去掉外层缩进）。"""
    source = loc.source_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    raw = lines[loc.body_start_line - 1: loc.body_end_line]

    result = []
    for line in raw:
        if not line.strip():
            result.append("")
        elif len(line) >= loc.indent:
            result.append(line[loc.indent:])
        else:
            result.append(line.lstrip())
    return "\n".join(result)


def write_function_body(loc: FunctionLocation, new_body: str) -> None:
    """用新的函数体替换源码。new_body 不含外层缩进。"""
    source = loc.source_path.read_text(encoding="utf-8")
    lines = source.splitlines()

    indent_str = " " * loc.indent
    new_lines = []
    for line in new_body.splitlines():
        if not line.strip():
            new_lines.append("")
        else:
            new_lines.append(indent_str + line)

    if not new_lines:
        new_lines = [indent_str + "pass"]

    result_lines = (
        lines[: loc.body_start_line - 1]
        + new_lines
        + lines[loc.body_end_line:]
    )
    loc.source_path.write_text("\n".join(result_lines) + "\n", encoding="utf-8")


def reload_module(module_name: str) -> None:
    """重载模块，让新代码生效。"""
    if module_name not in sys.modules:
        importlib.import_module(module_name)
        return
    importlib.reload(sys.modules[module_name])


def guess_owner_class(field_key: str, function_name: str) -> str:
    """
    根据字段名判断函数属于哪个类。
    - modified_callback / click_callback -> BtnFunction
    - 其他（含自由属性）-> ControlDataSetFunction
    """
    key = field_key or ""
    # 自由属性带 "prop::" 前缀
    if key.startswith("prop::"):
        key = key[len("prop::"):]
    if key in ("modified_callback", "click_callback"):
        return "BtnFunction"
    return "ControlDataSetFunction"