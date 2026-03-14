"""控件数据get函数"""
import json
from functools import lru_cache
from .tool.addClearCache import add_clear_cache

class ControlDataSetFunction:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.sys_c_d_m = kwargs['a_s_g_v'].sys_c_d_m

    @add_clear_cache
    @staticmethod
    @lru_cache(maxsize=None)
    def test():
        return True

    @add_clear_cache
    @staticmethod
    @lru_cache(maxsize=None)
    def test1():
        return True

    @add_clear_cache
    @lru_cache(maxsize=None)
    def get_common_group_fold(self) -> dict[str, int]:
        """
        获取可折叠分组框所对应属性集名称的折叠状态
        :return: 属性集名称：【折叠：0，展开：1】
        """
        widget_visibility_dict = {}
        widget_visibility_setting = self.sys_c_d_m.get_data("system", "groupingBoxFolding")
        if not widget_visibility_setting:
            widget_visibility_dict_ = json.dumps({}, ensure_ascii=False)
            self.sys_c_d_m.add_data("system", "groupingBoxFolding", widget_visibility_dict_, 1)
        widget_visibility_dict_list = self.sys_c_d_m.get_data("system", "groupingBoxFolding")
        for widget_visibility in json.loads(widget_visibility_dict_list[0]):
            widget_visibility_dict[widget_visibility] = int(json.loads(widget_visibility_dict_list[0])[widget_visibility])
        return widget_visibility_dict
