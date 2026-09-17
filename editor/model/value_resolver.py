"""
把 WidgetNode.properties 里的"函数名字符串"解析成真实值。

properties 里存的是回调函数名（如 "digital_reference_data"），
需要调用 ControlDataSetFunction 上对应的方法才能拿到实际值。
"""
import logging
from typing import Any, Optional

_log = logging.getLogger("editor")


def _get_cdsf_class():
    """尝试获取 ControlDataSetFunction 类。不可用时返回 None。"""
    try:
        from plugins.ControlFunction import ControlDataSetFunction
        return ControlDataSetFunction
    except Exception:
        return None


def clear_control_cache() -> None:
    """清理 ControlDataSetFunction 的缓存，让下次解析拿到最新值。"""
    cls = _get_cdsf_class()
    if cls is None:
        return
    try:
        clear = getattr(cls, "clear", None)
        if callable(clear):
            clear()
    except Exception as e:
        _log.debug(f"清理 ControlDataSetFunction 缓存失败: {e}")


def resolve(function_name: str, control_name: Optional[str] = None,
            default: Any = None) -> Any:
    """
    通过函数名调用 ControlDataSetFunction 上的静态方法，返回值。
    失败时返回 default。
    """
    if not function_name or not isinstance(function_name, str):
        return default
    if not function_name.isidentifier():
        return default

    cls = _get_cdsf_class()
    if cls is None:
        return default

    func = getattr(cls, function_name, None)
    if not callable(func):
        return default

    # 优先带 control_name（回调函数通常需要它）
    try:
        return func(control_name=control_name) if control_name else func()
    except TypeError:
        # 不接受 control_name 的函数
        try:
            return func()
        except Exception as e:
            _log.debug(f"调用 {function_name}() 失败: {e}")
            return default
    except Exception as e:
        _log.debug(
            f"调用 {function_name}(control_name={control_name}) 失败: {e}"
        )
        return default


def resolve_property(node, prop_name: str, default: Any = None) -> Any:
    """
    从 node.properties[prop_name] 拿到函数名，解析成真实值。
    - 若 properties 里存的是函数名（str）→ 调用函数
    - 若存的是值本身 → 直接返回
    - 若不存在 → 返回 default
    """
    if node is None:
        return default
    value = (node.properties or {}).get(prop_name)
    if value is None:
        return default
    if isinstance(value, str):
        if not value.isidentifier():
            # 看起来不像函数名，直接当值返回
            return value
        return resolve(value, control_name=node.control_name, default=default)
    return value