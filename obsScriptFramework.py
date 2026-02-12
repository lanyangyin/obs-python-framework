import os
import sys
from pathlib import Path
import obspython as obs

script_file_path = Path(__file__)
"""脚本文件路径"""
script_file_dir = script_file_path.parent
"""脚本所在文件夹路径"""
script_file_name = script_file_path.stem
"""脚本无后缀名称"""
script_config_folder = script_file_dir.joinpath(script_file_name + "_")
"""脚本配置文件夹路径"""
os.makedirs(script_config_folder, exist_ok=True)  # 新建脚本配置文件夹
sys.path.insert(0, f'{script_config_folder}')  # 将脚本配置文件夹也加入环境用来导入包
try:  # 导入脚本配置文件夹中的包
    from src.tool.LogManager import LogManager
    from src.tool.scriptCsv2Json import ControlTemplateParser
    from src.data.obsScriptGlobalVariable import ObsScriptGlobalVariable
    from src.data.obsScriptControlData import *
    from src.framework.obsScriptControlDataFramework import get_control_manager
    from src.framework.obsScriptModifiedFramework import ModifiedFunction
    from src.framework.obsTriggerFrontendEventFramework import TriggerFrontendEvent
    from plugins.ButtonFunction import BtnFunction
    from plugins.ControlFunction import ControlDataSetFunction
    ImportSuccess = (True, None)
except ImportError as e:
    ImportSuccess = (False, str(e.msg))
    obs.script_log(obs.LOG_ERROR, str(e.msg))

try:  # 开发测试用
    from obsScriptFramework_.src.tool.LogManager import LogManager
    from obsScriptFramework_.src.tool.scriptCsv2Json import ControlTemplateParser
    from obsScriptFramework_.src.data.obsScriptGlobalVariable import ObsScriptGlobalVariable
    from obsScriptFramework_.src.data.obsScriptControlData import *
    from obsScriptFramework_.src.framework.obsScriptControlDataFramework import get_control_manager
    from obsScriptFramework_.src.framework.obsSciptButtonFunctionFramework import ObsScriptButtonFunctionFramework
    from obsScriptFramework_.src.framework.obsScriptModifiedFramework import ModifiedFunction
    from obsScriptFramework_.src.framework.obsTriggerFrontendEventFramework import TriggerFrontendEvent
    from obsScriptFramework_.plugins.ButtonFunction import BtnFunction
    from obsScriptFramework_.plugins.ControlFunction import ControlDataSetFunction
except ImportError:
    pass


def script_defaults(settings):  # 设置其默认值
    """
    调用以设置与脚本关联的默认设置(如果有的话)。为了设置其默认值，您通常会调用默认值函数。
    :param settings:与脚本关联的设置。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    # 脚本设置体
    ObsScriptGlobalVariable.settings = settings
    # 日志管理器
    ObsScriptGlobalVariable.Log_manager = LogManager(script_config_folder / ObsScriptGlobalVariable.log_folder_name)
    # 控件管理器
    ObsScriptGlobalVariable.control_manager = get_control_manager()
    # 控件属性文档转换
    ObsScriptGlobalVariable.control_parser = ControlTemplateParser()
    # 按钮回调函数管理器
    ObsScriptGlobalVariable.btn = BtnFunction(a_s_g_v=ObsScriptGlobalVariable)
    # 前端事件触发管理器
    ObsScriptGlobalVariable.t_f_event = TriggerFrontendEvent(ObsScriptGlobalVariable.btn, a_s_g_v=ObsScriptGlobalVariable)
    # 按钮回调函数管理器
    ObsScriptGlobalVariable.btn_f = ObsScriptButtonFunctionFramework(ObsScriptGlobalVariable.btn, ObsScriptGlobalVariable.Log_manager)
    # 控件变动回调函数管理器
    ObsScriptGlobalVariable.mdf_f = ModifiedFunction(ObsScriptGlobalVariable.btn, a_s_g_v=ObsScriptGlobalVariable)

    result = ObsScriptGlobalVariable.control_parser.parse_csv(
        ObsScriptGlobalVariable.control_data_csv_filepath,
        initial_props_name=ObsScriptGlobalVariable.control_manager.get_basic_group().group_props_name
    )

    if not hasattr(
            ObsScriptGlobalVariable.control_manager.button,
            "e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"
    ):
        ObsScriptGlobalVariable.control_manager.button.add(
            control_name="e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
            object_name="e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
            description="允许执行控件修改回调",
            long_description="允许执行控件修改回调",
            widget_variant=ButtonVariant.DEFAULT,
            modified_callback_enabled=True,
            modified_callback=ObsScriptGlobalVariable.mdf_f.property_modified(
                "e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"
            ),
            url="",
            callback=lambda pr, ps: None
        )
    for controls_data in result["all_controls"]:  # 添加控件原始属性
        controls = getattr(ObsScriptGlobalVariable.control_manager, controls_data["widget_category"].lower())
        if hasattr(controls, controls_data["object_name"]):
            continue
        kwargs = controls_data["group_properties"]["group_1"] | controls_data["group_properties"].get("group_2", {})
        kwargs |= {"props_name": controls_data["props_name"]}
        ObsScriptGlobalVariable.Log_manager.log_info(controls_data["group_properties"]["group_1"]["control_name"])
        del kwargs['control_name']
        if kwargs['modified_callback_enabled']:
            kwargs['modified_callback'] = ObsScriptGlobalVariable.mdf_f.property_modified(
                controls_data["group_properties"]["group_1"]["control_name"]
            )
        if kwargs.get("callback", False):
            kwargs["callback"] = ObsScriptGlobalVariable.btn_f.select(kwargs["callback"])
        kwargs["widget_category"] = getattr(WidgetCategory, controls_data["widget_category"])
        if kwargs['widget_variant']:
            if kwargs["widget_category"] == WidgetCategory.CHECKBOX:
                kwargs['widget_variant'] = getattr(CheckBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.DIGITALBOX:
                kwargs['widget_variant'] = getattr(DigitalBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.TEXTBOX:
                kwargs['widget_variant'] = getattr(TextBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.BUTTON:
                kwargs['widget_variant'] = getattr(ButtonVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.COMBOBOX:
                kwargs['widget_variant'] = getattr(ComboBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.PATHBOX:
                kwargs['widget_variant'] = getattr(PathBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.COLORBOX:
                kwargs['widget_variant'] = getattr(ColorBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.FONTBOX:
                kwargs['widget_variant'] = getattr(FontBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.LISTBOX:
                kwargs['widget_variant'] = getattr(ListBoxVariant, kwargs['widget_variant'])
            elif kwargs["widget_category"] == WidgetCategory.GROUP:
                kwargs['widget_variant'] = getattr(GroupVariant, kwargs['widget_variant'])
        controls.add(
            control_name=controls_data["group_properties"]["group_1"]["control_name"],
            object_name=controls_data["object_name"],
            **kwargs
        )
    if not hasattr(
            ObsScriptGlobalVariable.control_manager.button,
            "e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"
    ):
        ObsScriptGlobalVariable.control_manager.button.add(
            control_name="e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
            object_name="e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083",
            description="禁止执行控件修改回调",
            long_description="禁止执行控件修改回调",
            widget_variant=ButtonVariant.DEFAULT,
            modified_callback_enabled=True,
            modified_callback=ObsScriptGlobalVariable.mdf_f.property_modified(
                "e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"
            ),
            url="",
            callback=lambda pr, ps: None
        )


def script_description():
    """
    调用以检索要在“脚本”窗口中显示给用户的描述字符串。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return ImportSuccess[1]
    return ObsScriptGlobalVariable.description


def script_load(settings):
    """
    在脚本启动时调用与脚本相关的特定设置。所提供的设置参数通常不用于由用户设置的设置;
    相反，该参数用于脚本中可能使用的任何额外的内部设置数据。
    :param settings:与脚本关联的设置。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    ObsScriptGlobalVariable.Log_manager.log_info(f"{script_file_name} 加载成功")
    obs.obs_frontend_add_event_callback(ObsScriptGlobalVariable.t_f_event.event_callback())
    pass


def script_update(settings):
    """
    当用户更改了脚本的设置(如果有的话)时调用。
    这里更改控件属性不会实时显示，
    不要在这里控制控件的【可见】、【可用】、【值】和【名称】
    :param settings:与脚本关联的设置。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    pass


def script_properties():
    """主属性创建函数"""
    # 包载入判断
    if not ImportSuccess[0]:
        return None
    ObsScriptGlobalVariable.Log_manager.log_info(f"生成控件")

    for props_name in ObsScriptGlobalVariable.control_manager.available_group_props_names:
        ObsScriptGlobalVariable.Log_manager.log_info(f"构建属性集: {props_name}")
        ObsScriptGlobalVariable.props_dict[props_name] = obs.obs_properties_create()

    sorted_widgets = ObsScriptGlobalVariable.control_manager.get_widgets_by_load_order()
    for w in sorted_widgets:
        w.props = ObsScriptGlobalVariable.props_dict[w.props_name]
        if hasattr(w, "group_props_name"):
            w.group_props = ObsScriptGlobalVariable.props_dict[w.group_props_name]

        # 获取按载入次序排序的所有控件列表
        if w.widget_category == WidgetCategory.CHECKBOX:
            # 添加复选框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"复选框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_bool(w.props, w.control_name, w.description)
        elif w.widget_category == WidgetCategory.DIGITALBOX:
            # 添加数字控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"数字框控件: {w.control_name} 【{w.description}】")
            if w.widget_variant == DigitalBoxVariant.INT_SLIDER:
                w.obj = obs.obs_properties_add_int_slider(
                    w.props, w.control_name, w.description, w.min_val, w.max_val, w.step
                )
            elif w.widget_variant == DigitalBoxVariant.INT:
                w.obj = obs.obs_properties_add_int(
                    w.props, w.control_name, w.description, w.min_val, w.max_val, w.step
                )
            elif w.widget_variant == DigitalBoxVariant.FLOAT_SLIDER:
                w.obj = obs.obs_properties_add_float_slider(
                    w.props, w.control_name, w.description, w.min_val, w.max_val, w.step
                )
            elif w.widget_variant == DigitalBoxVariant.FLOAT:
                w.obj = obs.obs_properties_add_float(
                    w.props, w.control_name, w.description, w.min_val, w.max_val, w.step
                )
            obs.obs_property_int_set_suffix(w.obj, w.suffix)
        elif w.widget_category == WidgetCategory.TEXTBOX:
            # 添加文本框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"文本框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_text(w.props, w.control_name, w.description, w.widget_variant.value)
        elif w.widget_category == WidgetCategory.BUTTON:
            # 添加按钮控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"按钮控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_button(
                w.props, w.control_name, w.description, w.callback
            )
            obs.obs_property_button_set_type(w.obj, w.widget_variant.value)
            if w.widget_variant == ButtonVariant.URL:  # 是否为链接跳转按钮
                obs.obs_property_button_set_url(w.obj, w.url)
        elif w.widget_category == WidgetCategory.COMBOBOX:
            # 添加组合框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"组合框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_list(
                w.props, w.control_name, w.description, w.widget_variant.value, obs.OBS_COMBO_FORMAT_STRING
            )
        elif w.widget_category == WidgetCategory.PATHBOX:
            # 添加路径对话框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"路径对话框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_path(
                w.props, w.control_name, w.description, w.widget_variant.value, w.filter_str, w.default_path
            )
        elif w.widget_category == WidgetCategory.COLORBOX:
            # 添加颜色对话框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"颜色对话框控件: {w.control_name} 【{w.description}】")
            if w.widget_variant == ColorBoxVariant.COLOR:
                w.obj = obs.obs_properties_add_color(w.props, w.control_name, w.description)
            elif w.widget_variant == ColorBoxVariant.ALPHA:
                w.obj = obs.obs_properties_add_color_alpha(w.props, w.control_name, w.description)
        elif w.widget_category == WidgetCategory.FONTBOX:
            # 添加字体对话框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"字体对话框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_font(w.props, w.control_name, w.description)
        elif w.widget_category == WidgetCategory.LISTBOX:
            # 添加列表对话框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"列表对话框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_editable_list(
                w.props, w.control_name, w.description, w.widget_variant.value, w.filter_str, w.default_path
            )
        elif w.widget_category == WidgetCategory.GROUP:
            # 分组框控件
            ObsScriptGlobalVariable.Log_manager.log_info(f"分组框控件: {w.control_name} 【{w.description}】")
            w.obj = obs.obs_properties_add_group(
                w.props, w.control_name, w.description, w.widget_variant.value, w.group_props
            )

        if w.long_description:
            obs.obs_property_set_long_description(w.obj, w.long_description)

        if w.modified_callback_enabled:
            ObsScriptGlobalVariable.Log_manager.log_info(f"为{w.widget_category}: 【{w.description}】添加钩子函数")
            obs.obs_property_set_modified_callback(w.obj, w.modified_callback)
    # GlobalVariableOfData.props_dict = props_dict
    # 更新UI界面数据#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*
    # update_ui_interface_data()
    return ObsScriptGlobalVariable.props_dict[ObsScriptGlobalVariable.control_manager.get_basic_group().group_props_name]

    pass


def script_tick(seconds):
    """
    每帧调用
    这里更改控件属性不会实时显示，
    不要在这里控制控件的【可见】、【可用】、【值】和【名称】
    Args:
        seconds:

    Returns:

    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    pass


def script_unload():
    """
    在脚本被卸载时调用。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    ObsScriptGlobalVariable.Log_manager.flush()
    pass




