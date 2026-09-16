import os
from typing import Any, Dict, List, Callable

import obspython as obs

from plugins.tool.parseColor import int_to_color_str
from ..data.obsScriptControlData import (
    WidgetCategory,
    CheckBoxData,
    DigitalBoxData,
    TextBoxData,
    ButtonData,
    ComboBoxData,
    PathBoxData,
    GroupData,
    DigitalBoxVariant,
    TextBoxVariant,
    ComboBoxVariant,
    GroupVariant,
    TextBoxInfoVariant,
    ListBoxData,
    ColorBoxData,
    FontBoxData,
    ColorBoxVariant,
)

# ------------------------------------------------------------------
# 模块级注册表
# ------------------------------------------------------------------
# 之所以放在类外，是因为 Python 3.9 的 classmethod 对象在类体内不可直接调用，
# 无法作为装饰器使用（`@register_ui_handler(...)` 会抛 TypeError）。
# 放在模块级后，装饰器语法在所有 Python 版本下都能工作。
_UI_HANDLERS: Dict[WidgetCategory, Callable] = {}


def register_ui_handler(category: WidgetCategory):
    """
    装饰器：把函数注册为某类控件的 UI 更新处理器。

    用法：
        @register_ui_handler(WidgetCategory.CHECKBOX)
        def _update_checkbox(self, w): ...

    同一个 WidgetCategory 只能注册一次，重复注册会抛 ValueError。
    """
    def decorator(func: Callable) -> Callable:
        existing = _UI_HANDLERS.get(category)
        if existing is not None:
            raise ValueError(
                f"[UIUpdater] WidgetCategory.{category.name} 已经注册了处理器 "
                f"'{existing.__name__}'，不能再注册 '{func.__name__}'。"
            )
        _UI_HANDLERS[category] = func
        return func
    return decorator


class UIUpdater:
    """
    OBS 脚本 UI 更新器，负责将控件数据模型的状态同步到 OBS 界面。

    设计要点：
    - 用注册表替代原先的大 if/elif 链：每个控件分类对应一个 handler，
      通过 @UIUpdater.register(WidgetCategory.XXX) 装饰器注册。
    - 可见性和启用状态的更新逻辑独立成 _apply_visibility / _apply_enabled，
      统一处理可折叠分组框的特殊行为。
    - 对 float 变体的数字框，int 输入自动视为合法，不再产生 WARNING 噪音。
    """

    # 直接引用模块级注册表，方便外部按 UIUpdater._handlers 访问
    _handlers = _UI_HANDLERS

    @classmethod
    def registered_categories(cls) -> List[WidgetCategory]:
        """返回已注册 handler 的所有分类，便于调试和测试。"""
        return list(_UI_HANDLERS.keys())

    # ------------------------------------------------------------------
    # 构造
    # ------------------------------------------------------------------
    def __init__(self, script_settings: Any, control_manager: Any, Log_manager: Any) -> None:
        self.script_settings = script_settings
        self.control_manager = control_manager
        self.Log_manager = Log_manager

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def update(self, update_widget_for_props_dict: Dict[str, List[str]]) -> bool:
        """
        更新 UI 界面数据，使控件状态与内部数据模型同步。

        :param update_widget_for_props_dict: 字典，键为控件所属属性集名称（props_name），
                                             值为该属性集下需要动态更新的控件名称列表（control_name）。
        :return: 始终返回 True。
        """
        for w in self.control_manager.get_widgets_by_load_order():
            # 过滤：只处理在更新映射里显式指定的控件
            if w.props_name not in update_widget_for_props_dict:
                continue
            if w.control_name not in update_widget_for_props_dict[w.props_name]:
                continue

            # 1. 可见性 / 启用状态（所有控件统一处理）
            self._apply_visibility(w)
            self._apply_enabled(w)

            # 2. 分类分发
            handler = self._handlers.get(w.widget_category)
            if handler is None:
                self.Log_manager.log_debug(
                    f"[UIUpdater] 控件 '{w.control_name}' 的分类 "
                    f"{w.widget_category.value} 尚未注册处理器，跳过数值同步。"
                )
                continue
            handler(self, w)

        return True

    # ------------------------------------------------------------------
    # 可见性 / 启用状态
    # ------------------------------------------------------------------
    def _apply_visibility(self, w: Any) -> None:
        """把控件数据模型的 visible / folding_visible 同步到 OBS 界面。"""
        if (
            w.widget_category == WidgetCategory.GROUP
            and w.widget_variant == GroupVariant.CHECKABLE
        ):
            # 可折叠分组框：本体 + 折叠控制对象 两个 obs_property
            current_main = obs.obs_property_visible(w.obj)
            current_folding = obs.obs_property_visible(w.folding_control_obj)

            if w.visible:
                target_main = w.folding_visible
                target_folding = not w.folding_visible
            else:
                target_main = w.visible
                target_folding = w.visible

            self.Log_manager.log_debug(
                f"{w.control_name}可见状态{current_main}⏩{target_main}"
            )
            if current_main != target_main:
                obs.obs_property_set_visible(w.obj, target_main)
            if current_folding != target_folding:
                obs.obs_property_set_visible(w.folding_control_obj, target_folding)
        else:
            current = obs.obs_property_visible(w.obj)
            self.Log_manager.log_debug(f"{w.control_name}可见状态{current}⏩{w.visible}")
            if current != w.visible:
                obs.obs_property_set_visible(w.obj, w.visible)

    def _apply_enabled(self, w: Any) -> None:
        """把控件数据模型的 enabled / folding_enabled 同步到 OBS 界面。"""
        if (
            w.widget_category == WidgetCategory.GROUP
            and w.widget_variant == GroupVariant.CHECKABLE
        ):
            current_main = obs.obs_property_enabled(w.obj)
            current_folding = obs.obs_property_enabled(w.folding_control_obj)

            if w.enabled:
                target_main = w.folding_enabled
                target_folding = not w.folding_enabled
            else:
                target_main = w.enabled
                target_folding = w.enabled

            self.Log_manager.log_debug(
                f"{w.control_name}启用状态{current_main}⏩{target_main}"
            )
            if current_main != target_main:
                obs.obs_property_set_enabled(w.obj, target_main)
            if current_folding != target_folding:
                obs.obs_property_set_enabled(w.folding_control_obj, target_folding)
        else:
            current = obs.obs_property_enabled(w.obj)
            self.Log_manager.log_debug(f"{w.control_name}启用状态{current}⏩{w.enabled}")
            if current != w.enabled:
                obs.obs_property_set_enabled(w.obj, w.enabled)

    # ------------------------------------------------------------------
    # 类型辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_float(value: Any) -> Any:
        """
        把 int（非 bool）安全转换为 float，其他类型原样返回。
        用于在 float 变体下宽容处理 CSV 中的 int 输入。
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return float(value)
        return value

    # ------------------------------------------------------------------
    # 各类型控件的 handler
    # ------------------------------------------------------------------

    @register_ui_handler(WidgetCategory.CHECKBOX)
    def _update_checkbox(self, w: CheckBoxData) -> None:
        """同步复选框控件的值。"""
        current_bool = obs.obs_data_get_bool(self.script_settings, w.control_name)

        if not isinstance(w.checked, bool):
            self.Log_manager.log_warning(
                f"复选框 {w.control_name} 期望 bool，实际为 {type(w.checked)}"
            )

        self.Log_manager.log_debug(f"{w.control_name}的勾选状态{current_bool}⏩{w.checked}")
        if current_bool != w.checked:
            obs.obs_data_set_bool(self.script_settings, w.control_name, w.checked)

    @register_ui_handler(WidgetCategory.DIGITALBOX)
    def _update_digitalbox(self, w: DigitalBoxData) -> None:
        """同步数字框控件的范围与值。"""
        variant = w.widget_variant
        is_int_variant = variant in (DigitalBoxVariant.INT, DigitalBoxVariant.INT_SLIDER)
        is_float_variant = variant in (DigitalBoxVariant.FLOAT, DigitalBoxVariant.FLOAT_SLIDER)

        if is_int_variant:
            current_min = obs.obs_property_int_min(w.obj)
            current_max = obs.obs_property_int_max(w.obj)
            current_step = obs.obs_property_int_step(w.obj)
            current_value = obs.obs_data_get_int(self.script_settings, w.control_name)
        elif is_float_variant:
            current_min = obs.obs_property_float_min(w.obj)
            current_max = obs.obs_property_float_max(w.obj)
            current_step = obs.obs_property_float_step(w.obj)
            current_value = obs.obs_data_get_double(self.script_settings, w.control_name)
        else:
            self.Log_manager.log_warning(
                f"数字框 {w.control_name} 的 widget_variant 未知：{variant}"
            )
            return

        # 类型审查（宽松）：float 变体接受 int 输入，自动视为合法
        if is_int_variant:
            if isinstance(w.digital, bool) or not isinstance(w.digital, int):
                self.Log_manager.log_warning(
                    f"数字框 {w.control_name} 期望 int，实际为 {type(w.digital)}"
                )
        else:  # float variant
            if isinstance(w.digital, bool) or not isinstance(w.digital, (int, float)):
                self.Log_manager.log_warning(
                    f"数字框 {w.control_name} 期望 float，实际为 {type(w.digital)}"
                )
            elif isinstance(w.digital, int):
                self.Log_manager.log_debug(
                    f"数字框 {w.control_name} 的数值为 int {w.digital}，"
                    f"在 float 变体下自动视为合法。"
                )

        # 记录更新
        self.Log_manager.log_debug(f"{w.control_name}最小值{current_min}⏩{w.min_val}")
        self.Log_manager.log_debug(f"{w.control_name}最大值{current_max}⏩{w.max_val}")
        self.Log_manager.log_debug(f"{w.control_name}步数{current_step}⏩{w.step}")
        self.Log_manager.log_debug(f"{w.control_name}数值{current_value}⏩{w.digital}")

        # 执行更新
        if is_int_variant:
            if w.min_val != current_min or w.max_val != current_max or w.step != current_step:
                obs.obs_property_int_set_limits(
                    w.obj, int(w.min_val), int(w.max_val), int(w.step)
                )
            if current_value != w.digital:
                obs.obs_data_set_int(self.script_settings, w.control_name, int(w.digital))
        else:  # float variant
            if w.min_val != current_min or w.max_val != current_max or w.step != current_step:
                obs.obs_property_float_set_limits(
                    w.obj,
                    float(self._coerce_float(w.min_val)),
                    float(self._coerce_float(w.max_val)),
                    float(self._coerce_float(w.step)),
                )
            if current_value != w.digital:
                obs.obs_data_set_double(
                    self.script_settings,
                    w.control_name,
                    float(self._coerce_float(w.digital)),
                )

    @register_ui_handler(WidgetCategory.TEXTBOX)
    def _update_textbox(self, w: TextBoxData) -> None:
        """同步文本框控件的类型与内容。"""
        variant = w.widget_variant

        if variant is TextBoxVariant.INFO:
            current_info_type = obs.obs_property_text_info_type(w.obj)
        current_string = obs.obs_data_get_string(self.script_settings, w.control_name)

        if variant is TextBoxVariant.INFO:
            if not isinstance(w.info_type, TextBoxInfoVariant):
                self.Log_manager.log_warning(
                    f"文本框 {w.control_name} 期望 TextBoxInfoVariant，"
                    f"实际为 {type(w.info_type)}"
                )
        if not isinstance(w.text, str):
            self.Log_manager.log_warning(
                f"文本框 {w.control_name} 期望 str，实际为 {type(w.text)}"
            )

        if variant is TextBoxVariant.INFO:
            self.Log_manager.log_debug(
                f"{w.control_name}文本提示类型{current_info_type}⏩{w.info_type}"
            )
        self.Log_manager.log_debug(f"{w.control_name}文本{current_string}⏩{w.text}")

        if variant is TextBoxVariant.INFO:
            if current_info_type != w.info_type.value:
                obs.obs_property_text_set_info_type(w.obj, w.info_type.value)
        if current_string != w.text:
            obs.obs_data_set_string(self.script_settings, w.control_name, w.text)

    @register_ui_handler(WidgetCategory.BUTTON)
    def _update_button(self, w: ButtonData) -> None:
        """按钮无需数值同步，保留占位以显式声明 handler。"""
        # 按钮的 URL / 点击行为在 script_properties 创建时已固化，
        # 运行时不通过 UIUpdater 同步。
        pass

    @register_ui_handler(WidgetCategory.COMBOBOX)
    def _update_combobox(self, w: ComboBoxData) -> None:
        """同步组合框控件的选项与当前值。"""
        current_options = []
        item_count = obs.obs_property_list_item_count(w.obj)
        for idx in range(item_count):
            label = obs.obs_property_list_item_name(w.obj, idx)
            value = obs.obs_property_list_item_string(w.obj, idx)
            current_options.append({"label": label, "value": value})
        current_string = obs.obs_data_get_string(self.script_settings, w.control_name)

        if not isinstance(w.items, list):
            self.Log_manager.log_warning(
                f"组合框 {w.control_name} 期望 list，实际为 {type(w.items)}"
            )
            label_exists = False
            value_exists = False
        else:
            label_exists = any(item.get("label") == w.label for item in w.items)
            value_exists = any(item.get("value") == w.value for item in w.items)
        if not isinstance(w.label, str):
            self.Log_manager.log_warning(
                f"组合框 {w.control_name} 期望 str，实际为 {type(w.label)}"
            )
        if not isinstance(w.value, str):
            self.Log_manager.log_warning(
                f"组合框 {w.control_name} 期望 str，实际为 {type(w.value)}"
            )
        if not label_exists:
            self.Log_manager.log_warning(
                f"组合框 {w.control_name} 期望 in {w.items}，实际为 {w.label}"
            )
        if not value_exists:
            self.Log_manager.log_warning(
                f"组合框 {w.control_name} 期望 in {w.items}，实际为 {w.value}"
            )

        if w.items != current_options:
            self.Log_manager.log_debug(
                f"{w.control_name}组合框列表{current_options}⏩{w.items}"
            )
        self.Log_manager.log_debug(
            f"{w.control_name}组合框显示文本{current_string}⏩{w.label}"
        )

        if w.items != current_options:
            obs.obs_property_list_clear(w.obj)
            for item in w.items:
                if item["label"] == w.label:
                    obs.obs_property_list_insert_string(
                        w.obj, 0, item["label"], item["value"]
                    )
                    break
            for item in w.items:
                if item["label"] != w.label:
                    obs.obs_property_list_add_string(w.obj, item["label"], item["value"])

        if w.widget_variant is ComboBoxVariant.EDITABLE:
            if current_string != w.label:
                if label_exists:
                    obs.obs_data_set_string(
                        self.script_settings, w.control_name, w.label
                    )
                else:
                    first_item_name = obs.obs_property_list_item_name(w.obj, 0)
                    obs.obs_data_set_string(
                        self.script_settings, w.control_name, first_item_name
                    )
        elif w.widget_variant is ComboBoxVariant.LIST:
            if current_string != w.value:
                if value_exists:
                    obs.obs_data_set_string(
                        self.script_settings, w.control_name, w.value
                    )
                else:
                    first_item_value = obs.obs_property_list_item_string(w.obj, 0)
                    obs.obs_data_set_string(
                        self.script_settings, w.control_name, first_item_value
                    )

    @register_ui_handler(WidgetCategory.PATHBOX)
    def _update_pathbox(self, w: PathBoxData) -> None:
        """同步路径框控件的路径文本。"""
        current_path = obs.obs_data_get_string(self.script_settings, w.control_name)

        if not isinstance(w.path_text, str):
            self.Log_manager.log_warning(
                f"路径框 {w.control_name} 期望 str，实际为 {type(w.path_text)}"
            )
        if w.path_text and not os.path.exists(w.path_text):
            self.Log_manager.log_warning(
                f"路径框 {w.control_name} 路径不存在: {w.path_text}"
            )

        self.Log_manager.log_debug(f"{w.control_name}路径框{current_path}⏩{w.path_text}")

        if current_path != w.path_text:
            obs.obs_data_set_string(self.script_settings, w.control_name, w.path_text)

    @register_ui_handler(WidgetCategory.GROUP)
    def _update_group(self, w: GroupData) -> None:
        """同步分组框控件的勾选状态（仅可勾选分组框有 checked 语义）。"""
        variant = w.widget_variant

        if variant is GroupVariant.CHECKABLE:
            current_bool = obs.obs_data_get_bool(self.script_settings, w.control_name)

            if not isinstance(w.checked, bool):
                self.Log_manager.log_warning(
                    f"分组框 {w.control_name} 期望 bool，实际为 {type(w.checked)}"
                )

            self.Log_manager.log_debug(
                f"{w.control_name}分组框{current_bool}⏩{w.checked}"
            )

            if current_bool != w.checked:
                obs.obs_data_set_bool(self.script_settings, w.control_name, w.checked)
            obs.obs_data_set_bool(
                self.script_settings, w.control_name.encode().hex(), w.checked
            )

    @register_ui_handler(WidgetCategory.COLORBOX)
    def _update_colorbox(self, w: ColorBoxData) -> None:
        """同步颜色选择框的颜色值。"""
        current = obs.obs_data_get_int(self.script_settings, w.control_name)

        if not isinstance(w.color_value, int):
            self.Log_manager.log_warning(
                f"颜色框 {w.control_name} 期望 int，实际为 {type(w.color_value)}"
            )

        self.Log_manager.log_debug(
            f"{w.control_name}的颜色{int_to_color_str(current)}"
            f"⏩{int_to_color_str(w.color_value)}"
        )

        if current != w.color_value:
            obs.obs_data_set_int(self.script_settings, w.control_name, w.color_value)

    @register_ui_handler(WidgetCategory.FONTBOX)
    def _update_fontbox(self, w: FontBoxData) -> None:
        """同步字体选择框的字体数据。"""
        current_font_data = obs.obs_data_get_obj(self.script_settings, w.control_name)
        if current_font_data:
            current_face = obs.obs_data_get_string(current_font_data, "face")
            current_size = obs.obs_data_get_int(current_font_data, "size")
            current_style = obs.obs_data_get_string(current_font_data, "style")
            current_flags = obs.obs_data_get_int(current_font_data, "flags")
            obs.obs_data_release(current_font_data)
        else:
            current_face = current_size = current_style = current_flags = None

        if not isinstance(w.font_face, str):
            self.Log_manager.log_warning(
                f"字体框 {w.control_name} 期望 str，实际为 {type(w.font_face)}"
            )
        if not isinstance(w.font_size, int):
            self.Log_manager.log_warning(
                f"字体框 {w.control_name} 期望 int，实际为 {type(w.font_size)}"
            )
        if not isinstance(w.font_style, str):
            self.Log_manager.log_warning(
                f"字体框 {w.control_name} 期望 str，实际为 {type(w.font_style)}"
            )
        if not isinstance(w.font_flags, int):
            self.Log_manager.log_warning(
                f"字体框 {w.control_name} 期望 int，实际为 {type(w.font_flags)}"
            )

        self.Log_manager.log_debug(
            f"{w.control_name}的字体系列名称{current_face}⏩{w.font_face}"
        )
        self.Log_manager.log_debug(
            f"{w.control_name}的字体大小{current_size}px⏩{w.font_size}px"
        )
        self.Log_manager.log_debug(
            f"{w.control_name}的字体样式{current_style}⏩{w.font_style}"
        )
        self.Log_manager.log_debug(
            f"{w.control_name}的字体标志位{current_flags}⏩{w.font_flags}"
        )

        if current_flags is not None:
            self.Log_manager.log_debug(
                f"{w.control_name}的标志粗体{bool(current_flags & 1)}⏩{w.font_bold}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志斜体{bool(current_flags & 2)}⏩{w.font_italic}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志下划线{bool(current_flags & 4)}⏩{w.font_underline}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志删除线{bool(current_flags & 8)}⏩{w.font_strikeout}"
            )
        else:
            self.Log_manager.log_debug(
                f"{w.control_name}的标志粗体(无数据)⏩{w.font_bold}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志斜体(无数据)⏩{w.font_italic}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志下划线(无数据)⏩{w.font_underline}"
            )
            self.Log_manager.log_debug(
                f"{w.control_name}的标志删除线(无数据)⏩{w.font_strikeout}"
            )

        if (
            current_face != w.font_face
            or current_size != w.font_size
            or current_style != w.font_style
            or current_flags != w.font_flags
        ):
            font_data = obs.obs_data_create()
            obs.obs_data_set_string(font_data, "face", w.font_face)
            obs.obs_data_set_int(font_data, "size", w.font_size)
            obs.obs_data_set_string(font_data, "style", w.font_style)
            obs.obs_data_set_int(font_data, "flags", w.font_flags)
            obs.obs_data_set_obj(self.script_settings, w.control_name, font_data)
            obs.obs_data_release(font_data)

    @register_ui_handler(WidgetCategory.LISTBOX)
    def _update_listbox(self, w: ListBoxData) -> None:
        """同步列表框控件的项目列表。"""
        current_array = obs.obs_data_get_array(self.script_settings, w.control_name)
        current_items = []
        if current_array is not None:
            count = obs.obs_data_array_count(current_array)
            for i in range(count):
                item_obj = obs.obs_data_array_item(current_array, i)
                val = obs.obs_data_get_string(item_obj, "value")
                sel = obs.obs_data_get_bool(item_obj, "selected")
                hid = obs.obs_data_get_bool(item_obj, "hidden")
                current_items.append({"value": val, "selected": sel, "hidden": hid})
                obs.obs_data_release(item_obj)
            obs.obs_data_array_release(current_array)

        if not isinstance(w.items, list):
            self.Log_manager.log_warning(
                f'列表框 {w.control_name} 期望 list，实际为 {type(w.items)}'
            )

        if current_items != w.items:
            self.Log_manager.log_debug(
                f"{w.control_name}列表框内容{current_items}⏩{w.items}"
            )

        if current_items != w.items:
            new_array = obs.obs_data_array_create()
            for item in w.items:
                obj = obs.obs_data_create()
                obs.obs_data_set_string(obj, "value", item.get("value", "?"))
                obs.obs_data_set_bool(obj, "selected", item.get("selected", False))
                obs.obs_data_set_bool(obj, "hidden", item.get("hidden", False))
                obs.obs_data_array_push_back(new_array, obj)
                obs.obs_data_release(obj)
            obs.obs_data_set_array(self.script_settings, w.control_name, new_array)
            obs.obs_data_array_release(new_array)