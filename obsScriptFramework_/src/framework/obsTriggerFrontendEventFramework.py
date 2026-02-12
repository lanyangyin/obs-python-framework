"""前端事件触发管理框架头"""
from ..data.ExplanatoryDictionary import *

class TriggerFrontendEvent:
    """前端事件触发管理器"""
    def __init__(self, BtnFunction, **kwargs):
        """

        :param kwargs:
        """
        self.BtnFunction = BtnFunction
        self.allow_execution = True
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def event_callback(self):
        def trigger_frontend_event(event):
            """前端事件触发回调"""
            self.ObsScriptGlobalVariable.Log_manager.log_info(f"监测到obs前端事件: {information4frontend_event[event]}")
            if self.allow_execution:
                self.allow_execution = False
                self.ObsScriptGlobalVariable.Log_manager.log_info("允许执行前端事件回调")
                try:
                    getattr(self.BtnFunction, FrontendEvent(event).name)
                except AttributeError:
                    self.ObsScriptGlobalVariable.Log_manager.log_debug(f"未找到【{FrontendEvent(event).name}】回调函数")
                self.allow_execution = True
            else:
                self.ObsScriptGlobalVariable.Log_manager.log_debug("正在执行其他的前端事件回调，禁止执行")
        return trigger_frontend_event

