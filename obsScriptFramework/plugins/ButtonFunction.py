from typing import Callable, Any


class BtnFunction:
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def specified(self, button_name: str) -> Callable[[Any, Any], Any]:
        def build_bf(ps, p):
            getattr(self, button_name)()
        return build_bf

    def top(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("top")

    def bottom(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("bottom")

    def test(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("test")
