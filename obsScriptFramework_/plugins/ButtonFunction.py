"""
按钮单击回调函数/控件变动回调函数
"""
import json

from .ControlFunction import ControlDataSetFunction
from .tool.addAliases import add_aliases, AliasMeta

class BtnFunction(metaclass=AliasMeta):
    def __init__(self, Log_manager, sys_c_d_m, control_manager):
        """

        :param Log_manager:
        :param sys_c_d_m:
        :param control_manager:
        """
        self.Log_manager = Log_manager
        self.sys_c_d_m = sys_c_d_m
        self.control_manager = control_manager

    def top(self, *args, **kwargs):
        """第一个控件的变动回调"""
        self.Log_manager.log_info("top")

    def bottom(self, *args, **kwargs):
        """最后一个控件的变动回调"""
        self.Log_manager.log_info("bottom")

    def modified_group_fold(self, *args, **kwargs):
        ControlDataSetFunction.clear()
        control_name = kwargs["control_name"]
        widget = self.control_manager.get_widget_by_control_name(control_name)
        group_props_name = widget.group_props_name
        widget_visibility_less_list = self.sys_c_d_m.get_data("system", "group_not_checked")
        if not widget_visibility_less_list:
            self.sys_c_d_m.add_data("system", "group_not_checked", group_props_name, 999)
        else:
            if group_props_name in widget_visibility_less_list:
                self.sys_c_d_m.remove_data("system", "group_not_checked", group_props_name)
            else:
                self.sys_c_d_m.add_data("system", "group_not_checked", group_props_name)

    @add_aliases("test_digitalBox")
    def test(self, *args, **kwargs):
        self.Log_manager.log_info("test")

