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

    __file_path = Path(__file__)
    description_filename: str = "obsScriptDescription.html"
    """脚本介绍文件名称"""
    @classproperty
    def description(self) -> str:
        """脚本介绍"""
        try:
            with open(self.__file_path.parent / self.description_filename, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            return str(e)

    Log_manager: Any = None
    """日志管理器"""
    log_folder_name:str = "LOG"
    """保存日志文件的文件夹名称"""


if __name__ == "__main__":
    print(ObsScriptGlobalVariable.description_filename)
    print(ObsScriptGlobalVariable.description)
