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
script_config_folder = script_file_dir.joinpath(script_file_name)
"""脚本配置文件夹路径"""
os.makedirs(script_config_folder, exist_ok=True)  # 新建脚本配置文件夹
sys.path.insert(0, f'{script_config_folder}')  # 将脚本配置文件夹也加入环境用来导入包
try:  # 导入脚本配置文件夹中的包
    from src.data.obsScriptGlobalVariable import ObsScriptGlobalVariable
    from src.data.obsScriptControlData import *
    from src.tool.LogManager import LogManager
    from src.tool.scriptCsv2Json import ControlTemplateParser
    from src.framework.obsScriptControlDataFramework import get_control_manager
    from src.framework.obsScriptModifiedFramework import ModifiedFunction
    from src.framework.TriggerFrontendEventFramework import TriggerFrontendEvent
    from plugins.ButtonFunction import BtnFunction
    ImportSuccess = (True, None)
except ImportError as e:
    ImportSuccess = (False, str(e.msg))
    obs.script_log(obs.LOG_ERROR, str(e.msg))

try:  # 开发测试用
    from obsScriptFramework.src.data.obsScriptGlobalVariable import ObsScriptGlobalVariable
    from obsScriptFramework.src.data.obsScriptControlData import *
    from obsScriptFramework.src.tool.LogManager import LogManager
    from obsScriptFramework.src.tool.scriptCsv2Json import ControlTemplateParser
    from obsScriptFramework.src.framework.obsScriptControlDataFramework import get_control_manager
    from obsScriptFramework.src.framework.obsScriptModifiedFramework import ModifiedFunction
    from obsScriptFramework.src.framework.TriggerFrontendEventFramework import TriggerFrontendEvent
    from obsScriptFramework.plugins.ButtonFunction import BtnFunction
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
    # 前端事件触发管理器
    ObsScriptGlobalVariable.t_f_event = TriggerFrontendEvent(a_s_g_v=ObsScriptGlobalVariable)
    # 按钮回调函数管理器
    ObsScriptGlobalVariable.btn_f = BtnFunction(a_s_g_v=ObsScriptGlobalVariable)
    # 控件变动回调函数管理器
    ObsScriptGlobalVariable.mdf_f = ModifiedFunction("top", "bottom", a_s_g_v=ObsScriptGlobalVariable)

    result = ObsScriptGlobalVariable.control_parser.parse_csv(
        ObsScriptGlobalVariable.control_data_csv_filepath,
        initial_props_name=ObsScriptGlobalVariable.control_manager.get_basic_group().group_props_name
    )
    for controls_data in result["all_controls"]:
        controls = getattr(ObsScriptGlobalVariable.control_manager, controls_data["widget_category"].lower())
        if hasattr(controls, controls_data["object_name"]):
            continue
        args = controls_data["group_properties"]["group_1"] | controls_data["group_properties"].get("group_2", {})
        args |= {"props_name": controls_data["props_name"]}
        ObsScriptGlobalVariable.Log_manager.log_info(controls_data["group_properties"]["group_1"]["control_name"])
        del args['control_name']
        if args['modified_callback_enabled']:
            args['modified_callback'] = lambda name=controls_data["group_properties"]["group_1"]["control_name"]: ObsScriptGlobalVariable.mdf_f.property_modified(name)
        if args.get("callback", False):
            args["callback"] = getattr(ObsScriptGlobalVariable.btn_f, args["callback"])
        args["widget_category"] = getattr(WidgetCategory, controls_data["widget_category"])
        if args['widget_variant']:
            if args["widget_category"] == WidgetCategory.CHECKBOX:
                args['widget_variant'] = getattr(CheckBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.DIGITALBOX:
                args['widget_variant'] = getattr(DigitalBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.TEXTBOX:
                args['widget_variant'] = getattr(TextBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.BUTTON:
                args['widget_variant'] = getattr(ButtonVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.COMBOBOX:
                args['widget_variant'] = getattr(ComboBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.PATHBOX:
                args['widget_variant'] = getattr(PathBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.COLORBOX:
                args['widget_variant'] = getattr(ColorBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.FONTBOX:
                args['widget_variant'] = getattr(FontBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.LISTBOX:
                args['widget_variant'] = getattr(ListBoxVariant, args['widget_variant'])
            elif args["widget_category"] == WidgetCategory.GROUP:
                args['widget_variant'] = getattr(GroupVariant, args['widget_variant'])
        controls.add(
            control_name=controls_data["group_properties"]["group_1"]["control_name"],
            object_name=controls_data["object_name"],
            **args
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
    obs.obs_frontend_add_event_callback(lambda event: ObsScriptGlobalVariable.t_f_event.trigger_frontend_event(event))
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
        return
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
                w.props, w.control_name, w.description, lambda ps, p, lw=w: lw.callback()
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
            obs.obs_property_set_modified_callback(w.obj, lambda ps, p, st, lw=w: lw.modified_callback())

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




