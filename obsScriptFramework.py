import os
import sys
import time
from pathlib import Path

file_path = Path(__file__)
"""脚本文件路径"""
file_dir = file_path.parent
"""脚本所在文件夹路径"""
file_name = file_path.stem
"""脚本无后缀名称"""
config_folder = file_dir.joinpath(file_name)
"""脚本配置文件夹路径"""
os.makedirs(config_folder, exist_ok=True)  # 新建脚本配置文件夹
sys.path.insert(0, f'{config_folder}')


def script_defaults(settings):  # 设置其默认值
    """
    调用以设置与脚本关联的默认设置(如果有的话)。为了设置其默认值，您通常会调用默认值函数。
    :param settings:与脚本关联的设置。
    """
    pass


def script_description():
    """
    调用以检索要在“脚本”窗口中显示给用户的描述字符串。
    """
    pass
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin:0; padding:12px; background-color:#2b2b2b; color:#e0e0e0; font-family:'Microsoft YaHei', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
<div style="display:flex; align-items:center; background-color:rgba(255,193,7,0.1); border:1px solid rgba(255,193,7,0.3); padding:12px 20px; max-width:300px;">
    <div style="font-size:20px; color:#ffc107; margin-right:12px;">🚀</div>
    <div style="color:#ffc107; font-weight:600; font-size:16px;">script_properties</div>
</div>
</body>
</html>
"""


def script_load(settings):
    """
    在脚本启动时调用与脚本相关的特定设置。所提供的设置参数通常不用于由用户设置的设置;
    相反，该参数用于脚本中可能使用的任何额外的内部设置数据。
    :param settings:与脚本关联的设置。
    """
    pass


def script_update(settings):
    """
    当用户更改了脚本的设置(如果有的话)时调用。
    这里更改控件属性不会实时显示，
    不要在这里控制控件的【可见】、【可用】、【值】和【名称】
    :param settings:与脚本关联的设置。
    """
    pass


def script_properties():
    """主属性创建函数"""
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
    pass


def script_unload():
    """
    在脚本被卸载时调用。
    """
    pass




