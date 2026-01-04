from datetime import datetime

from obsScriptControlData import *
import config

class GlobalVariableOfData:
    logRecording = ""

def log_save(log_level, log_str: str) -> None:
    """
    输出并保存日志
    Args:
        log_level: 日志等级

            - obs.LOG_INFO
            - obs.LOG_DEBUG
            - obs.LOG_WARNING
            - obs.LOG_ERROR
        log_str: 日志内容
    Returns: None
    """
    now: datetime = datetime.now()
    formatted: str = now.strftime("%Y/%m/%d %H:%M:%S")
    log_text: str = f"【{formatted}】 \t{log_str}"
    # log_text: str = f"{config.version} 【{formatted}】【{ExplanatoryDictionary.log_type[log_level]}】 \t{log_str}"
    # obs.script_log(log_level, log_str)
    GlobalVariableOfData.logRecording += log_text + "\n"
