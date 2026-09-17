"""
从 WidgetTree 生成 obsScriptFramework_ 的插件骨架代码。

生成目标：
- plugins/ButtonFunction.py     按钮回调骨架
- plugins/ControlFunction.py    控件属性回调 / 自由属性回调骨架
- plugins/GlobalVariable.py     用户全局变量骨架
- plugins/widgetData.csv        当前编辑的 CSV（一起导出，便于整套使用）
"""
from datetime import datetime
from typing import Dict, List, Set, Tuple

from .widget_node import WidgetNode
from .widget_tree import WidgetTree


# ----------------------------------------------------------------------
# 采集：扫描树里所有的函数名
# ----------------------------------------------------------------------
def collect_function_names(tree: WidgetTree) -> Tuple[Set[str], Set[str]]:
    """
    返回 (button_callbacks, control_callbacks)。
    - button_callbacks：按钮点击回调
    - control_callbacks：控件属性回调（含 modified_callback 与自由属性值）
    """
    button_callbacks: Set[str] = set()
    control_callbacks: Set[str] = set()

    for node in tree.iter_all():
        # 按钮的 click_callback
        if node.widget_category == "BUTTON":
            cb = node.properties.get("click_callback")
            if _looks_like_func_name(cb):
                button_callbacks.add(cb)

        # modified_callback
        if node.modified_callback_enabled and _looks_like_func_name(node.modified_callback):
            control_callbacks.add(node.modified_callback)

        # 自由属性里的函数名
        for k, v in (node.properties or {}).items():
            if k == "click_callback":
                continue
            if _looks_like_func_name(v):
                control_callbacks.add(v)

    return button_callbacks, control_callbacks


def _looks_like_func_name(value) -> bool:
    """粗略判断字符串是不是一个合法的 Python 标识符（函数名）。"""
    if not isinstance(value, str):
        return False
    if not value:
        return False
    if not value.isidentifier():
        return False
    if value.startswith("X"):
        return False
    return True


# ----------------------------------------------------------------------
# 生成
# ----------------------------------------------------------------------
def _header(comment: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f'"""\n{comment}\n\n'
        f'由编辑器自动生成于 {now}\n'
        f'如需修改，请直接编辑本文件，不会被编辑器自动覆盖。\n'
        f'"""\n'
    )


def generate_button_function(button_callbacks: Set[str]) -> str:
    parts = [
        _header("按钮单击回调函数"),
        "from src.tool.addAliases import add_aliases, AliasMeta\n",
        "\n",
        "class BtnFunction(metaclass=AliasMeta):\n",
        "    def __init__(self, Log_manager, sys_c_d_m, control_manager, control_ui_updater_manager):\n",
        "        self.Log_manager = Log_manager\n",
        "        self.sys_common_data_manager = sys_c_d_m\n",
        "        self.control_manager = control_manager\n",
        "        self.control_ui_updater_manager = control_ui_updater_manager\n",
    ]

    if not button_callbacks:
        parts.append("    pass\n")
    else:
        for name in sorted(button_callbacks):
            parts.append(
                f"\n"
                f"    def {name}(self, *args, **kwargs):\n"
                f'        """按钮回调：{name}"""\n'
                f'        self.Log_manager.log_info("按钮 {name} 被点击")\n'
                f"        return True\n"
            )

    return "".join(parts) + "\n"


def generate_control_function(control_callbacks: Set[str]) -> str:
    parts = [
        _header("控件数据 get 函数 / 控件变动回调函数"),
        "from functools import lru_cache\n",
        "\n",
        "from src.tool.addClearCache import add_clear_cache, ClearableCache\n",
        "from src.tool.addAliases import add_aliases, AliasMeta\n",
        "\n",
        "\n",
        "class ControlDataSetFunction(ClearableCache, metaclass=AliasMeta):\n",
        '    """控件属性回调集合。每个方法是一个自由属性/变动回调的取值函数。"""\n',
    ]

    # 固定保留：default_true / default_false
    parts.append(
        "\n"
        "    @staticmethod\n"
        "    @lru_cache(maxsize=None)\n"
        "    @add_clear_cache\n"
        "    def default_true(*args, **kwargs):\n"
        "        return True\n"
        "\n"
        "    @staticmethod\n"
        "    @lru_cache(maxsize=None)\n"
        "    @add_clear_cache\n"
        "    def default_false(*args, **kwargs):\n"
        "        return False\n"
    )

    if not control_callbacks:
        parts.append(
            "\n"
            "    # 当前 CSV 里没有引用任何回调函数。\n"
            "    pass\n"
        )
    else:
        for name in sorted(control_callbacks):
            parts.append(
                "\n"
                "    @staticmethod\n"
                "    @lru_cache(maxsize=None)\n"
                "    @add_clear_cache\n"
                f"    def {name}(*args, **kwargs):\n"
                f'        """回调：{name}"""\n'
                f"        # TODO: 返回合适的值\n"
                f"        return True\n"
            )

    return "".join(parts) + "\n"


def generate_global_variable() -> str:
    return (
        _header("用户全局变量")
        + "\n"
        + "class GlobalVariable:\n"
        + '    """用户自定义的全局变量，可在回调函数中引用。"""\n'
        + "    pass\n"
    )


# ----------------------------------------------------------------------
# 汇总
# ----------------------------------------------------------------------
def generate_all(tree: WidgetTree) -> Dict[str, str]:
    """
    生成所有文件内容。
    返回 {相对路径: 文件内容}。
    """
    buttons, controls = collect_function_names(tree)
    return {
        "plugins/ButtonFunction.py": generate_button_function(buttons),
        "plugins/ControlFunction.py": generate_control_function(controls),
        "plugins/GlobalVariable.py": generate_global_variable(),
    }


def summarize(tree: WidgetTree) -> Dict[str, int]:
    """生成统计摘要，用于 UI 预览。"""
    buttons, controls = collect_function_names(tree)
    return {
        "button_callbacks": len(buttons),
        "control_callbacks": len(controls),
        "total_nodes": len(tree),
    }