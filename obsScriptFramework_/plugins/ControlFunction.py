"""控件数据get函数"""
import json
from functools import lru_cache
from .tool.addClearCache import add_clear_cache, ClearableCache
from .tool.addAliases import add_aliases, AliasMeta

class ControlDataSetFunction(ClearableCache, metaclass=AliasMeta):
    """获得计算控件自由属性值的缓存回调函数"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.sys_c_d_m = kwargs['a_s_g_v'].sys_c_d_m

    @add_clear_cache
    @lru_cache(maxsize=None)
    def get_common_group_fold(self) -> dict[str, int]:
        """
        获取可折叠分组框所对应属性集名称的折叠状态
        :return: 属性集名称：【折叠：0，展开：1】
        """
        widget_visibility_dict = {}
        widget_visibility_setting = self.sys_c_d_m.get_data("system", "group_checked")
        if not widget_visibility_setting:
            widget_visibility_dict_ = json.dumps({}, ensure_ascii=False)
            self.sys_c_d_m.add_data("system", "group_checked", widget_visibility_dict_, 1)
        widget_visibility_dict_list = self.sys_c_d_m.get_data("system", "group_checked")
        for widget_visibility in json.loads(widget_visibility_dict_list[0]):
            widget_visibility_dict[widget_visibility] = int(json.loads(widget_visibility_dict_list[0])[widget_visibility])
        return widget_visibility_dict

    @staticmethod
    @add_clear_cache
    @lru_cache(maxsize=None)
    def test(**kwargs):
        return True

    @staticmethod
    @add_clear_cache
    @lru_cache(maxsize=None)
    def test1(**kwargs):
        return True

    @staticmethod
    @add_clear_cache
    @lru_cache(maxsize=None)
    def default_true(**kwargs):
        return True

    @staticmethod
    @add_clear_cache
    @lru_cache(maxsize=None)
    def default_false(**kwargs):
        return False
