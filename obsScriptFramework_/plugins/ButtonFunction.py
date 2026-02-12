from .tool.addAliases import add_aliases, AliasMeta

class BtnFunction(metaclass=AliasMeta):
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def top(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("top")

    def bottom(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("bottom")

    def test(self):
        self.ObsScriptGlobalVariable.Log_manager.log_info("test")
