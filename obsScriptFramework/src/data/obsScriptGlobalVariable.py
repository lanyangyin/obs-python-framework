"""定义了一些脚本的全局变量"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class classproperty:
    """类属性装饰器，允许像实例属性一样访问类方法"""

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, owner):
        return self.fget(owner)

class ObsScriptGlobalVariable:
    """脚本的全局变量"""
    version: str = "1.0.0"
    """脚本版本号"""
    settings: Any = None
    """脚本设置体"""
    causeOfTheFrontDeskIncident = None
    """前台事件引起的原因"""
    props_dict = {}
    """控件属性集的字典"""

    __data_dir_path = Path(__file__).parent
    """数据文件存放文件夹路径"""
    description_filename: str = "obsScriptDescription.html"
    """脚本介绍文件名称"""
    @classproperty
    def description(self) -> str:
        """脚本介绍"""
        try:
            with open(self.__data_dir_path / self.description_filename, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            return str(e)

    control_data_csv_filename: str = "widgetData.csv"
    """控件数据csv文件名"""
    @classproperty
    def control_data_csv_filepath(self) -> str:
        return str(self.__data_dir_path / self.control_data_csv_filename)

    Log_manager: Any = None
    """日志管理器"""
    log_folder_name:str = "LOG"
    """保存日志文件的文件夹名称"""
    control_manager: Any = None
    """控件管理器"""
    control_parser: Any = None
    """控件属性文档转换器"""
    t_f_event = None
    """前端事件触发管理器"""
    btn_f = None
    """按钮回调函数管理器"""

if __name__ == "__main__":
    print(ObsScriptGlobalVariable.description_filename)
    print(ObsScriptGlobalVariable.description)
