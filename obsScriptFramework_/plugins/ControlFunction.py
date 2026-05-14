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

    @staticmethod
    def test_url_value():
        v = "https://www.tcptest.cn/http"
        return v

    @staticmethod
    def test_checked_value():
        v = True
        return v

    @staticmethod
    def test_min_val_value():
        v = 0
        return v

    @staticmethod
    def test_max_val_value():
        v = 100
        return v

    @staticmethod
    def test_step_value():
        v = 1
        return v

    @staticmethod
    def test_info_type_value():
        v = "NORMAL"
        return v

    @staticmethod
    def test_text_value():
        v = "这是一段文本测试"
        return v

    @staticmethod
    def test_path_text_value():
        v = "C:\\"
        return v

    @staticmethod
    def test_label_value():
        v = "这是组合框标签测试"
        return v

    @staticmethod
    def test_value_value():
        v = "这是组合框值测试"
        return v

    @staticmethod
    def test_items_value():
        v = {
            "label":"这是组合框/列表框元素标签测试",
            "value":"这是组合框/列表框元素值测试"
        }
        return v

    @staticmethod
    def test_color_alpha_value():
        v = 0xFF
        return v

    @staticmethod
    def test_color_red_value():
        v = 0xFF
        return v

    @staticmethod
    def test_color_green_value():
        v = 0xFF
        return v

    @staticmethod
    def test_color_blue_value():
        v = 0xFF
        return v

    @staticmethod
    def test_font_face_value():
        v = "Kai"
        return v

    @staticmethod
    def test_font_size_value():
        v = 36
        return v

    @staticmethod
    def test_font_style_value():
        v = "Regular"
        return v

    @staticmethod
    def test_font_bold_value():
        v = False
        return v

    @staticmethod
    def test_font_italic_value():
        v = False
        return v

    @staticmethod
    def test_font_underline_value():
        v = False
        return v

    @staticmethod
    def test_font_strikeout_value():
        v = False
        return v

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


