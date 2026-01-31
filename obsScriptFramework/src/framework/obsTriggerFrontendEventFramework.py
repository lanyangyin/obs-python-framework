"""前端事件触发管理框架头"""
from ..data.ExplanatoryDictionary import *

class TriggerFrontendEvent:
    """前端事件触发管理器"""
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def event_callback(self):
        def trigger_frontend_event(event):
            """前端事件触发回调"""
            self.ObsScriptGlobalVariable.Log_manager.log_info(f"监测到obs前端事件: {information4frontend_event[event]}")
            if self.ObsScriptGlobalVariable.causeOfTheFrontDeskIncident:
                self.ObsScriptGlobalVariable.Log_manager.log_info(
                    f"此次 事件 由【{self.ObsScriptGlobalVariable.causeOfTheFrontDeskIncident}】引起"
                )
            pass

        return trigger_frontend_event

