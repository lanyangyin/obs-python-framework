from pathlib import Path

# class ButtonType:
OBS_BUTTON_DEFAULT = 0
OBS_BUTTON_URL = 1


# class ComboBoxType:
OBS_COMBO_TYPE_RADIO = 2
OBS_COMBO_TYPE_LIST = 1
OBS_COMBO_TYPE_EDITABLE = 0


# class TextType:
OBS_TEXT_INFO = 3
OBS_TEXT_MULTILINE = 2
OBS_TEXT_PASSWORD = 1
OBS_TEXT_DEFAULT = 0


# class PathBoxType:
OBS_PATH_DIRECTORY = 0
OBS_PATH_FILE_SAVE = 1
OBS_PATH_FILE = 2


# class GroupType:
OBS_GROUP_CHECKABLE = 1
OBS_GROUP_NORMAL = 0


# class ObsTextInfo:
OBS_TEXT_INFO_NORMAL = 0
OBS_TEXT_INFO_WARNING = 1
OBS_TEXT_INFO_ERROR = 2


# class ObsFrontendEvent:
OBS_FRONTEND_EVENT_THEME_CHANGED = 39
OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN = 40
OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED = 41
OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED = 42
OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED = 43
OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN = 44
OBS_FRONTEND_EVENT_FINISHED_LOADING = 0
OBS_FRONTEND_EVENT_EXIT = 1
OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED = 2
OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED = 3
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP = 4
OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED = 5
OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED = 6
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED = 7
OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING = 8
OBS_FRONTEND_EVENT_PROFILE_RENAMED = 36
OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED = 7
OBS_FRONTEND_EVENT_PROFILE_CHANGED = 8
OBS_FRONTEND_EVENT_PROFILE_CHANGING = 31
OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED = 9
OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED = 10
OBS_FRONTEND_EVENT_TRANSITION_STOPPED = 11
OBS_FRONTEND_EVENT_TRANSITION_CHANGED = 12
OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED = 13
OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED = 27
OBS_FRONTEND_EVENT_SCENE_CHANGED = 14
OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED = 15
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED = 16
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING = 17
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED = 18
OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING = 19
OBS_FRONTEND_EVENT_RECORDING_UNPAUSED = 20
OBS_FRONTEND_EVENT_RECORDING_PAUSED = 21
OBS_FRONTEND_EVENT_RECORDING_STOPPED = 22
OBS_FRONTEND_EVENT_RECORDING_STOPPING = 23
OBS_FRONTEND_EVENT_RECORDING_STARTED = 24
OBS_FRONTEND_EVENT_RECORDING_STARTING = 25
OBS_FRONTEND_EVENT_STREAMING_STOPPED = 26
OBS_FRONTEND_EVENT_STREAMING_STOPPING = 27
OBS_FRONTEND_EVENT_STREAMING_STARTED = 28
OBS_FRONTEND_EVENT_STREAMING_STARTING = 29


# class ObsLog:
LOG_ERROR = f"{Path(__file__)}".split("\\")[-1]
LOG_WARNING = f"{Path(__file__)}".split("\\")[-1]
LOG_DEBUG = f"{Path(__file__)}".split("\\")[-1]
LOG_INFO = f"{Path(__file__)}".split("\\")[-1]


# class AddControl:
# @staticmethod
def obs_properties_add_button(props, name, text, callback):
    pass


# class WidgetCategory:
# @staticmethod
def obs_property_button_set_type(p, type) -> None:
    r"""
    obs_property_button_set_type(p, type)

    Parameters
    ----------
    p: obs_property_t *
    type: enum enum obs_button_type

    """
    pass


OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS = None
OBS_EDITABLE_LIST_TYPE_FILES = None
OBS_EDITABLE_LIST_TYPE_STRINGS = None
setting = {}

@staticmethod
def script_log(LOG_INFO, param):
    print(LOG_INFO, param)
    return None

@staticmethod
def obs_frontend_add_event_callback(callback, *private_data):
    """
    添加一个回调函数，该回调函数将在发生前端事件时调用。请参阅obs_frontend_event，了解可以触发哪些类型的事件。

    以下是 OBS 前端事件的主要类型（完整列表见 obs-frontend-api.h）：
        - 事件常量	值	说明
        - OBS_FRONTEND_EVENT_EXIT	1	OBS即将退出（最后一个可调用API的事件）
        - OBS_FRONTEND_EVENT_FINISHED_LOADING	0	OBS完成初始化加载
        - OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED	27	工作室模式下预览场景改变
        - OBS_FRONTEND_EVENT_PROFILE_CHANGED	8	当前配置文件已切换
        - OBS_FRONTEND_EVENT_PROFILE_CHANGING	31	当前配置文件即将切换
        - OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED	7	配置文件列表改变（增删）
        - OBS_FRONTEND_EVENT_PROFILE_RENAMED	36	配置文件被重命名
        - OBS_FRONTEND_EVENT_RECORDING_PAUSED	18	录制已暂停
        - OBS_FRONTEND_EVENT_RECORDING_STARTED	15	录制已成功开始
        - OBS_FRONTEND_EVENT_RECORDING_STARTING	14	录制正在启动
        - OBS_FRONTEND_EVENT_RECORDING_STOPPED	17	录制已完全停止
        - OBS_FRONTEND_EVENT_RECORDING_STOPPING	16	录制正在停止
        - OBS_FRONTEND_EVENT_RECORDING_UNPAUSED	19	录制已取消暂停
        - OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED	24	回放缓存已保存
        - OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED	21	回放缓存已成功开始
        - OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING	20	回放缓存正在启动
        - OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED	23	回放缓存已完全停止
        - OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING	22	回放缓存正在停止
        - OBS_FRONTEND_EVENT_SCENE_CHANGED	2	当前场景已改变
        - OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED	8	当前场景集合已切换
        - OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING	32	当前场景集合即将切换
        - OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP	28	场景集合已完全卸载
        - OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED	9	场景集合列表改变（增删）
        - OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED	35	场景集合被重命名
        - OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED	3	场景列表改变（增删/重排序）
        - OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN	30	脚本需要处理OBS关闭（在EXIT事件前触发）
        - OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN	40	截图已保存（v29.0.0+）
        - OBS_FRONTEND_EVENT_STREAMING_STARTED	11	推流已成功开始
        - OBS_FRONTEND_EVENT_STREAMING_STARTING	10	推流正在启动
        - OBS_FRONTEND_EVENT_STREAMING_STOPPED	13	推流已完全停止
        - OBS_FRONTEND_EVENT_STREAMING_STOPPING	12	推流正在停止
        - OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED	26	工作室模式已禁用
        - OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED	25	工作室模式已启用
        - OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED	29	转场控制条数值改变
        - OBS_FRONTEND_EVENT_THEME_CHANGED	39	主题已更改（v29.0.0+）
        - OBS_FRONTEND_EVENT_TRANSITION_CHANGED	4	当前转场效果已改变
        - OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED	34	转场持续时间已更改
        - OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED	33	转场列表改变（增删）
        - OBS_FRONTEND_EVENT_TRANSITION_STOPPED	5	转场动画已完成
        - OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED	37	虚拟摄像头已启动
        - OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED	38	虚拟摄像头已停止
    Args:
        callback:当前端事件发生时使用的回调
        *private_data:与回调关联的私有数据

    Returns:

    """
    return None

@staticmethod
def obs_frontend_remove_event_callback(callback, *private_data):
    """
    以下是 OBS 前端事件的主要类型（完整列表见 obs-frontend-api.h）：
    事件常量	值	说明
    OBS_FRONTEND_EVENT_STREAMING_STARTING	4	推流正在启动
    OBS_FRONTEND_EVENT_STREAMING_STARTED	5	推流已开始
    OBS_FRONTEND_EVENT_STREAMING_STOPPING	3	推流正在停止
    OBS_FRONTEND_EVENT_STREAMING_STOPPED	6	推流已停止
    OBS_FRONTEND_EVENT_RECORDING_STARTED	7	录制已开始
    OBS_FRONTEND_EVENT_RECORDING_STOPPED	8	录制已停止
    OBS_FRONTEND_EVENT_SCENE_CHANGED	2	当前场景改变
    OBS_FRONTEND_EVENT_TRANSITION_CHANGED	9	转场效果改变
    OBS_FRONTEND_EVENT_PROFILE_CHANGED	10	配置文件切换
    OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED	11	配置文件列表改变
    OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED	12	场景列表改变
    OBS_FRONTEND_EVENT_EXIT	0	OBS 即将退出
    OBS_FRONTEND_EVENT_FINISHED_LOADING	1	OBS 完成加载
    Args:
        callback:当前端事件发生时使用的回调
        *private_data:与回调关联的私有数据

    Returns:

    """
    return None

@staticmethod
def obs_properties_create():
    return False

@staticmethod
def obs_property_set_modified_callback(p, modified) -> None:
    return None

@staticmethod
def obs_property_enabled(p) -> bool:
    r"""
    obs_property_enabled(p) -> bool

    Parameters
    ----------
    p: obs_property_t *

    """
    return True

@staticmethod
def obs_property_visible(p) -> bool:
    r"""
    obs_property_visible(p) -> bool

    Parameters
    ----------
    p: obs_property_t *

    """
    return True

@staticmethod
def obs_property_set_visible(p, visible: bool) -> None:
    r"""
    obs_property_set_visible(p, visible)

    Parameters
    ----------
    p: obs_property_t *
    visible: bool

    """
    return None

@staticmethod
def obs_property_set_enabled(p, enabled: bool) -> None:
    r"""
    obs_property_set_enabled(p, enabled)

    Parameters
    ----------
    p: obs_property_t *
    enabled: bool

    """
    return None

def script_path():
    """
    用于获取脚本所在文件夹的路径，这其实是一个obs插件内置函数，
    只在obs插件指定的函数内部使用有效,
    这里构建这个函数是没必要的，写在这里只是为了避免IDE出现error提示
    Example:
        假如脚本路径在 "/Applications/OBS.app/Contents/PlugIns/frontend-tools.plugin/Contents/Resources/scripts/bilibili_live.py"
        >>> print(script_path())
        /Applications/OBS.app/Contents/PlugIns/frontend-tools.plugin/Contents/Resources/scripts/
        >>> print(Path(f'{script_path()}bilibili-live') / "config.json")
        /Applications/OBS.app/Contents/PlugIns/frontend-tools.plugin/Contents/Resources/scripts/bilibili-live/config.json
    """
    return f"{Path(__file__).parent}\\"
