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
    from src.framework.obsScriptControlDataFramework import get_control_manager
    from src.tool.scriptCsv2Json import ControlTemplateParser
    from src.framework.TriggerFrontendEventFramework import TriggerFrontendEvent
    ImportSuccess = (True, None)
except ImportError as e:
    ImportSuccess = (False, str(e.msg))
    obs.script_log(obs.LOG_ERROR, str(e.msg))

try:  # 开发测试用
    from obsScriptFramework.src.data.obsScriptGlobalVariable import ObsScriptGlobalVariable
    from obsScriptFramework.src.data.obsScriptControlData import *
    from obsScriptFramework.src.tool.LogManager import LogManager
    from obsScriptFramework.src.framework.obsScriptControlDataFramework import get_control_manager
    from obsScriptFramework.src.tool.scriptCsv2Json import ControlTemplateParser
    from obsScriptFramework.src.framework.TriggerFrontendEventFramework import TriggerFrontendEvent
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

    result = ObsScriptGlobalVariable.control_parser.parse_csv(
        ObsScriptGlobalVariable.control_data_csv_filepath,
        initial_props_name=ObsScriptGlobalVariable.control_manager.get_basic_group().group_props_name
    )
    for controls_data in result["all_controls"]:
        controls = getattr(ObsScriptGlobalVariable.control_manager, controls_data["widget_category"].lower())
        try:
            getattr(controls, controls_data["object_name"])
            continue
        except AttributeError:
            pass
        args = controls_data["group_properties"]["group_1"] | controls_data["group_properties"].get("group_2", {})
        args |= {"props_name": controls_data["props_name"]}
        ObsScriptGlobalVariable.Log_manager.log_info(controls_data["group_properties"]["group_1"]["control_name"])
        del args['control_name']
        if args['widget_variant']:
            if controls_data["widget_category"] == "CHECKBOX":
                args['widget_variant'] = getattr(CheckBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "DIGITALBOX":
                args['widget_variant'] = getattr(DigitalBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "TEXTBOX":
                args['widget_variant'] = getattr(TextBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "BUTTON":
                args['widget_variant'] = getattr(ButtonVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "COMBOBOX":
                args['widget_variant'] = getattr(ComboBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "PATHBOX":
                args['widget_variant'] = getattr(PathBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "COLORBOX":
                args['widget_variant'] = getattr(ColorBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "FONTBOX":
                args['widget_variant'] = getattr(FontBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "LISTBOX":
                args['widget_variant'] = getattr(ListBoxVariant, args['widget_variant'])
            elif controls_data["widget_category"] == "GROUP":
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




