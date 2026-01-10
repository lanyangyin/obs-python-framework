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
    from src.data import obsScriptGlobalVariable
    from src.tool.LogManager import LogManager
    ImportSuccess = (True, None)
except ImportError as e:
    ImportSuccess = (False, str(e.msg))
    obs.script_log(obs.LOG_ERROR, str(e.msg))

try:  # 开发测试用
    from obsScriptFramework import obsScriptGlobalVariable
    from obsScriptFramework.src.tool.LogManager import LogManager
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
    obsScriptGlobalVariable.settings = settings
    # 日志管理器
    obsScriptGlobalVariable.Log_manager = LogManager(script_config_folder / obsScriptGlobalVariable.log_folder_name)
    # 脚本介绍
    try:
        with open(script_config_folder.joinpath(obsScriptGlobalVariable.description_filename), encoding="utf-8") as f:
            obsScriptGlobalVariable.description = f.read()
    except FileNotFoundError as e:
        obsScriptGlobalVariable.description = str(e)


def script_description():
    """
    调用以检索要在“脚本”窗口中显示给用户的描述字符串。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return ImportSuccess[1]
    return obsScriptGlobalVariable.description


def script_load(settings):
    """
    在脚本启动时调用与脚本相关的特定设置。所提供的设置参数通常不用于由用户设置的设置;
    相反，该参数用于脚本中可能使用的任何额外的内部设置数据。
    :param settings:与脚本关联的设置。
    """
    # 包载入判断
    if not ImportSuccess[0]:
        return
    obsScriptGlobalVariable.Log_manager.log_info(f"{script_file_name} 加载成功")
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
    obsScriptGlobalVariable.Log_manager.log_info(f"生成控件")
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
    obsScriptGlobalVariable.Log_manager.flush()
    pass




