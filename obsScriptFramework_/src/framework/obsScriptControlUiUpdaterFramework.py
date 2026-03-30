import obspython as obs
from typing import Any, Dict, List, Optional

# 根据您的实际文件路径调整导入
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
)


class UIUpdater:
    """
    OBS 脚本 UI 更新器，负责将控件数据模型的状态同步到 OBS 界面。

    该类封装了原有的 update_ui_interface_data 函数，将脚本设置存储作为依赖项，
    通过构造函数传入，避免直接引用全局变量，提高可测试性和模块化。

    Attributes:
        script_settings: OBS 数据对象 (obs_data_t)，用于读写控件值。
    """

    def __init__(self, script_settings: Any) -> None:
        """
        初始化 UIUpdater 实例。

        Args:
            script_settings: OBS 数据对象，通常为 GlobalVariableOfData.script_settings。
        """
        self.script_settings = script_settings

    def update(self, widget, update_widget_for_props_dict: Dict[str, List[str]]) -> bool:
        """
        更新 UI 界面数据，使控件状态与内部数据模型同步。

        遍历所有需要关注的控件（通过 widget.get_sorted_controls() 获取），
        根据预定义的配置（update_widget_for_props_dict）更新控件的可见性、
        启用状态以及当前值。同时将用户界面的改动写回到 script_settings 中。

        Args:
            widget: 包含控件列表和相关方法的对象，必须提供 get_sorted_controls() 方法，
                    返回一个由控件数据对象（如 CheckBoxData、DigitalBoxData 等）组成的列表。
            update_widget_for_props_dict: 字典，键为控件所属属性集名称（props_name），
                                           值为该属性集下需要动态更新的控件名称列表（control_name）。

        Returns:
            bool: 始终返回 True，表示更新完成。

        Notes:
            - 控件数据对象应继承自 ControlBaseData，并包含对应类型的专用属性。
            - 本方法仅处理原有逻辑中涉及的控件类型（复选框、数字框、文本框、按钮、组合框、路径框、分组框），
              颜色框、字体框、列表框暂不处理（可后续扩展）。
        """
        for w in widget.get_sorted_controls():
            # 检查当前控件是否需要动态更新
            if w.props_name not in update_widget_for_props_dict:
                continue
            if w.control_name not in update_widget_for_props_dict[w.props_name]:
                continue

            # 更新可见性
            if obs.obs_property_visible(w.obj) != w.visible:
                obs.obs_property_set_visible(w.obj, w.visible)

            # 更新启用状态
            if obs.obs_property_enabled(w.obj) != w.enabled:
                obs.obs_property_set_enabled(w.obj, w.enabled)

            # 根据控件分类进行数据同步
            category = w.widget_category

            # 复选框
            if category is WidgetCategory.CHECKBOX:
                if isinstance(w, CheckBoxData):
                    self._update_checkbox(w)

            # 数字框
            elif category is WidgetCategory.DIGITALBOX:
                if isinstance(w, DigitalBoxData):
                    self._update_digitalbox(w)

            # 文本框
            elif category is WidgetCategory.TEXTBOX:
                if isinstance(w, TextBoxData):
                    self._update_textbox(w)

            # 按钮（无需数据同步）
            elif category is WidgetCategory.BUTTON:
                pass

            # 组合框
            elif category is WidgetCategory.COMBOBOX:
                if isinstance(w, ComboBoxData):
                    self._update_combobox(w)

            # 路径框
            elif category is WidgetCategory.PATHBOX:
                if isinstance(w, PathBoxData):
                    self._update_pathbox(w)

            # 分组框
            elif category is WidgetCategory.GROUP:
                if isinstance(w, GroupData):
                    self._update_group(w)

            # 其他控件类型（颜色框、字体框、列表框）暂不处理，可后续扩展
            else:
                # 可在此添加日志或忽略
                pass

        return True

    # ----------------------------------------------------------------------
    # 私有更新方法，按控件类型拆分以提高可读性
    # ----------------------------------------------------------------------

    def _update_checkbox(self, w: CheckBoxData) -> None:
        """同步复选框控件的值。"""
        if obs.obs_data_get_bool(self.script_settings, w.control_name) != w.checked:
            obs.obs_data_set_bool(self.script_settings, w.control_name, w.checked)

    def _update_digitalbox(self, w: DigitalBoxData) -> None:
        """同步数字框控件的范围与值。"""
        variant = w.widget_variant
        if variant in (DigitalBoxVariant.INT, DigitalBoxVariant.INT_SLIDER):
            # 整数范围
            if (w.min_val != obs.obs_property_int_min(w.obj) or
                    w.max_val != obs.obs_property_int_max(w.obj) or
                    w.step != obs.obs_property_int_step(w.obj)):
                obs.obs_property_int_set_limits(w.obj, w.min_val, w.max_val, w.step)
            # 同步值
            if obs.obs_data_get_int(self.script_settings, w.control_name) != w.value:
                obs.obs_data_set_int(self.script_settings, w.control_name, w.value)
        elif variant in (DigitalBoxVariant.FLOAT, DigitalBoxVariant.FLOAT_SLIDER):
            # 浮点数范围
            if (w.min_val != obs.obs_property_float_min(w.obj) or
                    w.max_val != obs.obs_property_float_max(w.obj) or
                    w.step != obs.obs_property_float_step(w.obj)):
                obs.obs_property_float_set_limits(w.obj, w.min_val, w.max_val, w.step)
            # 同步值
            if obs.obs_data_get_double(self.script_settings, w.control_name) != w.value:
                obs.obs_data_set_double(self.script_settings, w.control_name, w.value)

    def _update_textbox(self, w: TextBoxData) -> None:
        """同步文本框控件的类型与内容。"""
        if w.widget_variant is TextBoxVariant.INFO:
            # 更新信息类型
            if obs.obs_property_text_info_type(w.obj) != w.info_type.value:
                obs.obs_property_text_set_info_type(w.obj, w.info_type.value)
        # 同步文本内容
        if obs.obs_data_get_string(self.script_settings, w.control_name) != w.text:
            obs.obs_data_set_string(self.script_settings, w.control_name, w.text)

    def _update_combobox(self, w: ComboBoxData) -> None:
        """同步组合框控件的选项与当前值。"""
        # 构建当前选项列表以比较
        current_options = []
        item_count = obs.obs_property_list_item_count(w.obj)
        for idx in range(item_count):
            label = obs.obs_property_list_item_name(w.obj, idx)
            value = obs.obs_property_list_item_string(w.obj, idx)
            current_options.append({"label": label, "value": value})

        # 如果选项列表发生变化，则重建
        if w.items != current_options:
            obs.obs_property_list_clear(w.obj)
            # 先将当前显示文本对应的项插入到索引 0
            found = False
            for item in w.items:
                if item["label"] == w.display_text:
                    obs.obs_property_list_insert_string(w.obj, 0, item["label"], item["value"])
                    found = True
                else:
                    obs.obs_property_list_add_string(w.obj, item["label"], item["value"])
            # 如果当前显示文本不在选项中，则所有项按顺序添加（无需额外操作）

        # 根据组合框类型设置当前选中值
        if w.widget_variant is ComboBoxVariant.EDITABLE:
            first_item_name = obs.obs_property_list_item_name(w.obj, 0)
            if obs.obs_data_get_string(self.script_settings, w.control_name) != first_item_name:
                obs.obs_data_set_string(self.script_settings, w.control_name, first_item_name)
        elif w.widget_variant is ComboBoxVariant.LIST:
            first_item_value = obs.obs_property_list_item_string(w.obj, 0)
            if obs.obs_data_get_string(self.script_settings, w.control_name) != first_item_value:
                obs.obs_data_set_string(self.script_settings, w.control_name, first_item_value)

    def _update_pathbox(self, w: PathBoxData) -> None:
        """同步路径框控件的路径文本。"""
        if obs.obs_data_get_string(self.script_settings, w.control_name) != w.path_text:
            obs.obs_data_set_string(self.script_settings, w.control_name, w.path_text)

    def _update_group(self, w: GroupData) -> None:
        """同步分组框控件的勾选状态（如果可勾选）。"""
        if w.widget_variant is GroupVariant.CHECKABLE:
            if obs.obs_data_get_bool(self.script_settings, w.control_name) != w.checked:
                obs.obs_data_set_bool(self.script_settings, w.control_name, w.checked)