"""
从 obsScriptFramework_ 的 plugins 中提取可用的回调函数名，
供编辑器做下拉建议。

- ControlFunction.ControlDataSetFunction -> 自由属性 / modified_callback
- ButtonFunction.BtnFunction -> 按钮点击回调
"""
from typing import List


def list_control_functions() -> List[str]:
    """
    返回 ControlDataSetFunction 上所有可用的公共方法名（不含私有方法）。
    若导入失败，返回空列表。
    """
    try:
        from plugins.ControlFunction import ControlDataSetFunction
    except Exception:
        return []
    return _list_public_callables(ControlDataSetFunction)


def list_button_functions() -> List[str]:
    """
    返回 BtnFunction 上所有可用的公共方法名（不含私有方法）。
    若导入失败，返回空列表。
    """
    try:
        from plugins.ButtonFunction import BtnFunction
    except Exception:
        return []
    return _list_public_callables(BtnFunction)


def list_all_function_names() -> List[str]:
    """合并两组函数名，去重后排序。"""
    names = set(list_control_functions()) | set(list_button_functions())
    return sorted(names)


def _list_public_callables(cls) -> List[str]:
    """遍历类上所有不以 '_' 开头的可调用属性。"""
    names = []
    for name in dir(cls):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(cls, name)
        except Exception:
            continue
        if callable(attr):
            names.append(name)
    return sorted(names)