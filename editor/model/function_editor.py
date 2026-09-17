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

from .._bootstrap import get_project_root

_log = logging.getLogger("editor")


def _plugins_dir() -> Path:
    return get_project_root() / "obsScriptFramework_" / "plugins"


def _module_map() -> dict:
    """每次调用都重新计算，保证 exe 运行时路径正确。"""
    plugins_dir = _plugins_dir()
    return {
        "ControlDataSetFunction": (
            plugins_dir / "ControlFunction.py",
            "plugins.ControlFunction",
        ),
        "BtnFunction": (
            plugins_dir / "ButtonFunction.py",
            "plugins.ButtonFunction",
        ),
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
    module_map = _module_map()
    if owner_class not in module_map:
        raise ValueError(f"未知的类：{owner_class}")

    source_path, module_name = module_map[owner_class]
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

def get_module_name(class_name: str) -> str:
    """根据类名返回模块名。"""
    module_map = _module_map()
    if class_name not in module_map:
        raise ValueError(f"未知的类：{class_name}")
    return module_map[class_name][1]


def function_exists(func_name: str, owner_class: str = "ControlDataSetFunction") -> bool:
    """检查函数是否存在于指定类中。"""
    try:
        locate_function(func_name, owner_class=owner_class)
        return True
    except (FileNotFoundError, ValueError):
        return False


def append_function(owner_class: str, func_name: str) -> FunctionLocation:
    """
    在指定类的末尾追加一个新方法，返回新方法的位置信息。
    - 若函数已存在 → 抛 ValueError
    - 函数名不合法 → 抛 ValueError
    """
    if not func_name.isidentifier():
        raise ValueError(f"函数名不合法：{func_name}")

    module_map = _module_map()
    if owner_class not in module_map:
        raise ValueError(f"未知的类：{owner_class}")

    source_path, _ = module_map[owner_class]
    source, tree = _parse_file(source_path)

    class_node = _find_class(tree, owner_class)
    if class_node is None:
        raise ValueError(f"文件中未找到类 '{owner_class}'：{source_path}")

    if _find_function(class_node, func_name) is not None:
        raise ValueError(f"函数 '{func_name}' 已存在")

    # 找类的最后一个方法的结束位置（用于插入新代码）
    last_end = class_node.lineno
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (item.end_lineno or item.lineno) > last_end:
                last_end = item.end_lineno or item.lineno

    # 生成方法代码（带 4 空格缩进）
    if owner_class == "BtnFunction":
        new_code_lines = [
            f"    def {func_name}(self, *args, **kwargs):",
            f'        """按钮回调：{func_name}"""',
            f'        self.Log_manager.log_info("按钮 {func_name} 被点击")',
            f"        return True",
        ]
    else:
        # ControlDataSetFunction 的方法遵循静态方法 + lru_cache + add_clear_cache 模板
        new_code_lines = [
            "    @staticmethod",
            "    @lru_cache(maxsize=None)",
            "    @add_clear_cache",
            f"    def {func_name}(*args, **kwargs):",
            f'        """回调：{func_name}"""',
            f"        # TODO: 实现具体逻辑",
            f"        return True",
        ]

    lines = source.splitlines()
    insert_pos = last_end  # 在最后一行之后插入

    # 插入内容：一个空行 + 新方法所有行
    payload = [""] + new_code_lines

    result_lines = lines[:insert_pos] + payload + lines[insert_pos:]
    source_path.write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    # 返回新位置
    return locate_function(func_name, owner_class=owner_class)

def delete_function(owner_class: str,
                    func_name: str) -> FunctionLocation:
    """
    从类中删除一个方法（含装饰器行）。
    返回被删除方法的位置信息（用于日志）。
    """
    module_map = _module_map()
    if owner_class not in module_map:
        raise ValueError(f"未知的类：{owner_class}")

    # 定位并取源码结构
    loc = locate_function(func_name, owner_class=owner_class)

    source_path, _ = module_map[owner_class]
    source, tree = _parse_file(source_path)
    class_node = _find_class(tree, owner_class)
    func_node = _find_function(class_node, func_name)
    if func_node is None:
        raise ValueError(f"类 '{owner_class}' 中未找到方法 '{func_name}'")

    # 起始行（包含所有装饰器）
    start_line = func_node.lineno
    for dec in func_node.decorator_list:
        start_line = min(start_line, dec.lineno)
    end_line = func_node.end_lineno or func_node.lineno

    # 删除 [start_line, end_line]，并尝试多删后面的一个空行
    lines = source.splitlines()
    del_end = end_line
    if del_end < len(lines) and not lines[del_end].strip():
        del_end += 1

    del lines[start_line - 1: del_end]

    source_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return loc


def clear_references(tree, func_name: str) -> int:
    """
    清空树中所有引用 func_name 的字段：
    - 结构化字段 modified_callback
    - 自由属性 click_callback / visible / enabled / items 等
    返回被清空的引用数。
    """
    count = 0

    def _maybe_clear(container, key):
        nonlocal count
        if container.get(key) == func_name:
            container.pop(key, None)
            count += 1

    for node in tree.iter_all():
        # 结构化字段
        if node.modified_callback == func_name:
            node.modified_callback = None
            node.modified_callback_enabled = False
            count += 1

        # 自由属性：清空值而不删 key（保留字段在属性面板显示）
        props = node.properties or {}
        for key in list(props.keys()):
            if props.get(key) == func_name:
                props[key] = ""
                count += 1

    return count