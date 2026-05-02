"""控件数据get函数"""
import json
from functools import lru_cache
from .tool.addClearCache import add_clear_cache, ClearableCache
from .tool.addAliases import add_aliases, AliasMeta

class ControlDataSetFunction(ClearableCache, metaclass=AliasMeta):
    """获得计算控件自由属性值的缓存回调函数"""
    def __init__(self, sys_c_d_m, control_manager):
        self.sys_c_d_m = sys_c_d_m
        self.control_manager = control_manager

    @lru_cache(maxsize=None)
    @add_clear_cache
    def get_common_group_fold(self, *args, **kwargs) -> set[str]:
        """
        获取已折叠分组框所对应属性集名称的集合
        :return: 属性集名称集合
        """
        widget_visibility_less_list = self.sys_c_d_m.get_data("system", "group_not_checked")
        widget_visibility_less_set = set(widget_visibility_less_list)
        return widget_visibility_less_set

    @lru_cache(maxsize=None)
    @add_clear_cache
    def group_foldless_is(self, *args, **kwargs) -> bool:
        """
        获取控件是否展开
        :param args:
        :param kwargs:
            control_name
        :return: 是否展开
        """
        ControlDataSetFunction.clear()
        control_name = kwargs["control_name"]
        widget = self.control_manager.get_widget_by_control_name(control_name)
        group_props_name = widget.group_props_name
        widget_visibility_less_set = self.get_common_group_fold(control_name)
        return group_props_name not in widget_visibility_less_set

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def default_true(*args, **kwargs):
        return True

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def default_false(*args, **kwargs):
        return False

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def test_checkBox_checked(*args, **kwargs):
        return False

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def test(*args, **kwargs):
        return True

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def test1(*args, **kwargs):
        return True


