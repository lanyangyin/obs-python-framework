import obspython as obs

class ButtonFunction:
    def __init__(self, log_obj):
        self.log_obj = log_obj

    def top(self, *args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        self.log_obj.log_info(f"【{'顶部'}】按钮被触发")
        return True

    def bottom(self, *args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        self.log_obj.log_info(f"【{'底部'}】按钮被触发")
        return True


