"""定义了一些脚本的全局变量"""
from typing import Any

version: str = "1.0.0"
"""脚本版本号"""
settings: Any = None
"""脚本设置体"""

description_filename: str = "obsScriptDescription.html"
"""脚本介绍文件名称"""
description: str = ""
"""脚本介绍"""

Log_manager: Any = None
"""日志管理器"""
log_folder_name:str = "LOG"
"""保存日志文件的文件夹名称"""
