from .tool.addAliases import add_aliases, AliasMeta

class BtnFunction(metaclass=AliasMeta):
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        self.Log_manager = kwargs["a_s_g_v"].Log_manager

    def top(self):
        self.Log_manager.log_info("top")

    def bottom(self):
        self.Log_manager.log_info("bottom")

    @add_aliases("test_digitalBox")
    def test(self):
        self.Log_manager.log_info("test")
