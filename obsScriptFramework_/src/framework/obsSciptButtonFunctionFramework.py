"""按钮触发函数框架"""
from typing import Callable, Any


class ObsScriptButtonFunctionFramework:
    def __init__(self, BtnFunction, log):
        self.BtnFunction = BtnFunction
        self.log = log

    def select(self, button_name: str) -> Callable[[Any, Any], Any]:
        def build_bf(ps, p):
            try:
                getattr(self.BtnFunction, button_name)()
            except AttributeError:
                self.log.log_error(f"未找到名为【{button_name}】的回调函数")

        return build_bf