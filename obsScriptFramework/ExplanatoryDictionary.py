"""定义了一些数据的说明字典"""
from typing import Dict
import obspython as obs

textBox_type_name4textBox_type: Dict[int, str] = {
    obs.OBS_TEXT_INFO_NORMAL: '正常信息',
    obs.OBS_TEXT_INFO_WARNING: '警告信息',
    obs.OBS_TEXT_INFO_ERROR: '错误信息'
}
"""只读文本框的消息类型 说明字典"""

information4frontend_event: Dict[int, str] = {
    # 推流相关事件
    obs.OBS_FRONTEND_EVENT_STREAMING_STARTING: "推流正在启动",
    obs.OBS_FRONTEND_EVENT_STREAMING_STARTED: "推流已开始",
    obs.OBS_FRONTEND_EVENT_STREAMING_STOPPING: "推流正在停止",
    obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED: "推流已停止",

    # 录制相关事件
    obs.OBS_FRONTEND_EVENT_RECORDING_STARTING: "录制正在启动",
    obs.OBS_FRONTEND_EVENT_RECORDING_STARTED: "录制已开始",
    obs.OBS_FRONTEND_EVENT_RECORDING_STOPPING: "录制正在停止",
    obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED: "录制已停止",
    obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED: "录制已暂停",
    obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED: "录制已恢复",

    # 回放缓存相关事件
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING: "回放缓存正在启动",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED: "回放缓存已开始",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING: "回放缓存正在停止",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED: "回放缓存已停止",
    obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED: "回放已保存",

    # 场景相关事件
    obs.OBS_FRONTEND_EVENT_SCENE_CHANGED: "当前场景已改变",
    obs.OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED: "预览场景已改变",
    obs.OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED: "场景列表已改变",

    # 转场相关事件
    obs.OBS_FRONTEND_EVENT_TRANSITION_CHANGED: "转场效果已改变",
    obs.OBS_FRONTEND_EVENT_TRANSITION_STOPPED: "转场效果已停止",
    obs.OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED: "转场列表已改变",
    obs.OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED: "转场持续时间已更改",

    # 配置文件相关事件
    obs.OBS_FRONTEND_EVENT_PROFILE_CHANGING: "配置文件即将切换",
    obs.OBS_FRONTEND_EVENT_PROFILE_CHANGED: "配置文件已切换",
    obs.OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED: "配置文件列表已改变",
    obs.OBS_FRONTEND_EVENT_PROFILE_RENAMED: "配置文件已重命名",

    # 场景集合相关事件
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING: "场景集合即将切换",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED: "场景集合已切换",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED: "场景集合列表已改变",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED: "场景集合已重命名",
    obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP: "场景集合清理完成",

    # 工作室模式事件
    obs.OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED: "工作室模式已启用",
    obs.OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED: "工作室模式已禁用",

    # 系统级事件
    obs.OBS_FRONTEND_EVENT_EXIT: "OBS 即将退出",
    obs.OBS_FRONTEND_EVENT_FINISHED_LOADING: "OBS 完成加载",
    obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN: "脚本关闭中",

    # 虚拟摄像头事件
    obs.OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED: "虚拟摄像头已启动",
    obs.OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED: "虚拟摄像头已停止",

    # 控制条事件
    obs.OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED: "转场控制条(T-Bar)值已改变",

    # OBS 28+ 新增事件
    obs.OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN: "截图已完成",
    obs.OBS_FRONTEND_EVENT_THEME_CHANGED: "主题已更改"
}
"""obs前台事件 说明字典"""

log_type: Dict[int, str] = {
    obs.LOG_INFO: "INFO",
    obs.LOG_DEBUG: "DEBUG",
    obs.LOG_WARNING: "WARNING",
    obs.LOG_ERROR: "ERROR"
}
"""obs日志警告等级 说明字典"""