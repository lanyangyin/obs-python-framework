"""按钮回调函数框架"""
from typing import Callable, Any


class ModifiedFunction:

    def __init__(self, BtnFunction, **kwargs):
        self.BtnFunction = BtnFunction
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]
        self.allow_execution = True

    def property_modified(self, property_name) -> Callable[[Any, Any, Any], None]:
        def build_pm(ps, p, st=None):
            self.ObsScriptGlobalVariable.Log_manager.log_info(f"监测到控件变动: {property_name}")
            if property_name == "e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083":
                self.allow_execution = True
                self.ObsScriptGlobalVariable.Log_manager.log_info("允许执行控件修改回调")
            elif property_name == "e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083":
                self.allow_execution = False
                self.ObsScriptGlobalVariable.Log_manager.log_info("禁止执行控件修改回调")
            elif self.allow_execution:
                try:
                    getattr(self.BtnFunction, property_name)()
                except AttributeError:
                    self.ObsScriptGlobalVariable.Log_manager.log_error(f"未找到【{property_name}】对应的按钮回调函数")
        return build_pm