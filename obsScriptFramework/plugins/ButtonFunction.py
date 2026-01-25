class BtnFunction:
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def top(self, *args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]

    def bottom(self, *args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]

    def test(self, *args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        self.ObsScriptGlobalVariable.Log_manager.log_info("test")
