"""
载入脚本：
    [__init__.py] script_defaults 被调用
    [__init__.py] script_defaults 被调用
    [__init__.py] script_load 被调用
    [__init__.py] script_update 被调用
    [__init__.py] script_properties 被调用
    [__init__.py] script_properties 被调用
    【[__init__.py] script_tick 被调用】
焦点重新聚焦到脚本
    [__init__.py] script_properties 被调用
    【[__init__.py] script_tick 被调用】
移除脚本
    [__init__.py] script_unload 被调用
重新载入脚本
    [__init__.py] script_unload 被调用
    [__init__.py] script_defaults 被调用
    [__init__.py] script_defaults 被调用
    [__init__.py] script_load 被调用
    [__init__.py] script_update 被调用
    [__init__.py] script_properties 被调用
    [__init__.py] script_properties 被调用
    【[__init__.py] script_tick 被调用】
"""
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache, wraps
from pathlib import Path
from typing import Literal, Any, Union, Dict, List, Optional, Iterator, Callable, Set, TypeVar, Generic, Type

import obspython as obs
try:
    from obspython import script_path
except ImportError:
    pass

# import 结束 ====================================================================================================
class CommonDataManager:
    """
    管理用户多种类型常用数据的JSON文件

    功能:
    - 管理 {user_id: {data_type1: [item1, item2, ...], data_type2: [...]}} 格式的JSON文件
    - 每种数据类型最多包含5个元素
    - 支持增删改查操作
    - 自动创建不存在的目录和文件
    - 自动转换旧格式数据到新格式

    参数:
        directory: 文件存放目录
        default_data_type: 默认数据类型（用于向后兼容）
    """

    def __init__(self, filepath: Union[str, Path], default_data_type: str = "title"):
        """
        初始化CommonDataManager

        Args:
            filepath: 文件路径
            default_data_type: 默认数据类型（用于处理旧格式数据）
            maximum_quantity_of_elements: 保留的最大元素数
        """
        self.filepath = Path(filepath)
        self.default_data_type = default_data_type
        self.data: Dict[str, Dict[str, List[str]]] = {}

        # 确保目录存在
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件不存在则创建
        if not self.filepath.exists():
            self._save_data()
        else:
            self._load_data()
            self._convert_old_format()

    def _load_data(self) -> None:
        """从文件加载数据"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # 文件为空或格式错误时创建新文件
            self.data = {}
            self._save_data()

    def _save_data(self) -> None:
        """保存数据到文件"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _convert_old_format(self) -> None:
        """将旧格式数据转换为新格式"""
        needs_save = False

        for user_id, user_data in list(self.data.items()):
            # 如果用户数据是列表格式（旧格式），则转换为新格式
            if isinstance(user_data, list):
                self.data[user_id] = {self.default_data_type: user_data}
                needs_save = True

        if needs_save:
            self._save_data()

    def get_data(self, user_id: str, data_type: str) -> List[str]:
        """
        获取指定用户的指定类型数据列表

        Args:
            user_id: 用户ID
            data_type: 数据类型

        Returns:
            该用户的指定类型数据列表（如果没有则为空列表）
        """
        if user_id not in self.data:
            return []

        return self.data[user_id].get(data_type, [])

    def add_data(self, user_id: str, data_type: str, item: str, maximum: int = 5) -> None:
        """
        为用户添加新数据项

        特点:
        - 如果数据项已存在，则移动到列表最前面
        - 确保列表长度不超过5个
        - 如果用户不存在，则创建新条目
        - 如果数据类型不存在，则创建新类型

        Args:
            maximum: 保留的最大元素数
            user_id: 用户ID
            data_type: 数据类型
            item: 要添加的数据项
        """
        # 确保用户数据存在
        if user_id not in self.data:
            self.data[user_id] = {}

        # 确保数据类型存在
        if data_type not in self.data[user_id]:
            self.data[user_id][data_type] = []

        items = self.data[user_id][data_type]

        # 移除重复项（如果存在）
        if item in items:
            items.remove(item)

        # 添加到列表开头
        items.insert(0, item)

        # 确保不超过5个元素
        if len(items) > maximum:
            items = items[:maximum]

        # 更新数据并保存
        self.data[user_id][data_type] = items
        self._save_data()

    def remove_data(self, user_id: str, data_type: str, item: str) -> bool:
        """
        移除用户的指定数据项

        Args:
            user_id: 用户ID
            data_type: 数据类型
            item: 要移除的数据项

        Returns:
            True: 成功移除
            False: 数据项不存在
        """
        if user_id not in self.data or data_type not in self.data[user_id]:
            return False

        items = self.data[user_id][data_type]

        if item in items:
            items.remove(item)
            # 如果列表为空，则删除数据类型条目
            if not items:
                del self.data[user_id][data_type]
                # 如果用户数据为空，则删除用户条目
                if not self.data[user_id]:
                    del self.data[user_id]
            self._save_data()
            return True
        return False

    def update_data(self, user_id: str, data_type: str, old_item: str, new_item: str) -> bool:
        """
        更新用户的数据项

        Args:
            user_id: 用户ID
            data_type: 数据类型
            old_item: 要替换的旧数据项
            new_item: 新数据项

        Returns:
            True: 更新成功
            False: 旧数据项不存在
        """
        if user_id not in self.data or data_type not in self.data[user_id]:
            return False

        items = self.data[user_id][data_type]

        if old_item in items:
            # 替换数据项并移动到列表前面
            index = items.index(old_item)
            items.pop(index)
            items.insert(0, new_item)
            self._save_data()
            return True
        return False

    def clear_user_data(self, user_id: str, data_type: Optional[str] = None) -> None:
        """
        清除指定用户的指定类型数据或所有数据

        Args:
            user_id: 用户ID
            data_type: 数据类型（如果为None，则清除所有数据）
        """
        if user_id not in self.data:
            return

        if data_type is None:
            # 清除所有数据
            del self.data[user_id]
        elif data_type in self.data[user_id]:
            # 清除指定类型数据
            del self.data[user_id][data_type]
            # 如果用户数据为空，则删除用户条目
            if not self.data[user_id]:
                del self.data[user_id]

        self._save_data()

    def get_all_users(self) -> List[str]:
        """
        获取所有有数据的用户ID列表

        Returns:
            用户ID列表
        """
        return list(self.data.keys())

    def get_user_data_types(self, user_id: str) -> List[str]:
        """
        获取指定用户的所有数据类型

        Args:
            user_id: 用户ID

        Returns:
            数据类型列表
        """
        if user_id not in self.data:
            return []

        return list(self.data[user_id].keys())

    def get_all_data(self) -> Dict[str, Dict[str, List[str]]]:
        """
        获取所有数据

        Returns:
            完整的{user_id: {data_type: items}}字典
        """
        return self.data.copy()

    def __str__(self) -> str:
        """返回数据的字符串表示"""
        return json.dumps(self.data, ensure_ascii=False, indent=2)


# ====================================================================================================================


# -----------------------------------------------------------
# OBS Script Functions                                      -
# -----------------------------------------------------------

script_version = bytes.fromhex('302e302e30').decode('utf-8')
"""脚本版本.encode().hex()"""


class FunctionCache:
    @staticmethod
    @lru_cache(maxsize=None)
    def get_c_d_m():
        # 创建用户常用数据实例
        c_d_m = CommonDataManager(Path(GlobalVariableOfData.scriptsDataDirpath) / "commonData.json")
        return c_d_m

    @staticmethod
    @lru_cache(maxsize=None)
    def get_common_widget_groups_visibility() -> set[str]:
        """
        可折叠分组框中处于折叠状态的分组框名称的集合
        Returns:
            折叠状态的分组框名称的集合
        """
        widget_groups_visibility_data_precursor_list: list[str] = FunctionCache.get_c_d_m().get_data("setting", "widgetVisibility")
        if not widget_groups_visibility_data_precursor_list:  # 如果没有 widgetVisibility 记录 就创建默认的数据
            widget_groups_visibility_data_precursor_item: str = json.dumps([], ensure_ascii=False)
            """可折叠分组框控件可见性数据前体 记录 元素"""
            FunctionCache.get_c_d_m().add_data("setting", "widgetVisibility", widget_groups_visibility_data_precursor_item, 1)
        else:
            widget_groups_visibility_data_precursor_item = widget_groups_visibility_data_precursor_list[0]
        widget_groups_visibility_data_precursor_set = set(json.loads(widget_groups_visibility_data_precursor_item))
        return widget_groups_visibility_data_precursor_set

    @staticmethod
    @lru_cache(maxsize=None)
    def get_combobox_test_load_data():
        return {
            "Text": "测试选项3",
            "Value": "option-test3",
            "DictionaryList": [
                {"label": "测试选项0", "value": "option-test0"},
                {"label": "测试选项1", "value": "option-test1"},
                {"label": "测试选项2", "value": "option-test2"},
                {"label": "测试选项3", "value": "option-test3"},
                {"label": "测试选项4", "value": "option-test4"},
            ]
        }

    @staticmethod
    def cache_clear():
        FunctionCache.get_c_d_m.cache_clear()
        FunctionCache.get_combobox_test_load_data.cache_clear()
        FunctionCache.get_common_widget_groups_visibility.cache_clear()


class GlobalVariableOfData:
    """定义了一些全局变量"""
    props_dict: Dict[str, Any] = {}
    """属性集字典"""
    causeOfTheFrontDeskIncident = ""
    """前台事件引起的原因"""
    update_widget_attribute_dict: dict[str, set[str]] = {}
    """需要更新的控件 控件属性集名称为键 控件名称组成的集合为值 的字典"""
    group_folding_names: set[str] = set()
    """可折叠分组框中处于折叠状态的分组框名称的集合"""
    script_loading_is: bool = False
    """是否正式加载脚本"""
    isScript_propertiesIs: bool = False  # Script_properties()被调用
    """是否允许Script_properties()被调用"""
    script_settings: bool = None  # #脚本的所有设定属性集
    """脚本的所有设定属性集"""

    logRecording: str = ""  # #日志记录的文本
    """日志记录的文本"""

    # 网络配置类-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    networkConnectionStatus: bool = False  # #网络连接状态
    """网络连接状态"""
    sslVerification: bool = False
    """SSL验证"""

    # 文件配置类-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    scriptsDataDirpath: Optional[Path] = None  # #脚本所在目录
    """脚本所在目录"""
    scriptsUsersConfigFilepath: Optional[Path] = None  # #用户配置文件路径
    """用户配置文件路径"""
    scriptsTempDir: Optional[Path] = None  # #临时文件文件夹
    """临时文件文件夹"""
    scriptsLogDir: Optional[Path] = None  # #日志文件文件夹
    """日志文件文件夹"""
    scriptsCacheDir: Optional[Path] = None  # #缓存文件文件夹
    """缓存文件文件夹"""

    # 用户类-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


class ExplanatoryDictionary:
    """定义了一些数据的说明字典"""
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
    log_text: str = f"{script_version} 【{formatted}】【{ExplanatoryDictionary.log_type[log_level]}】 \t{log_str}"
    obs.script_log(log_level, log_str)
    GlobalVariableOfData.logRecording += log_text + "\n"

# 使用枚举定义控件类型，避免魔法字符串
class ControlType(Enum):
    BASE = "Base"
    CHECKBOX = "CheckBox"
    DIGITALBOX = "DigitalBox"
    TEXTBOX = "TextBox"
    BUTTON = "Button"
    COMBOBOX = "ComboBox"
    PATHBOX = "PathBox"
    GROUP = "Group"
    COLORBOX = "ColorBox"
    FONTBOX = "FontBox"
    LISTBOX = "ListBox"


@dataclass
class ControlBase:
    """控件基类"""
    WidgetType: ControlType = ControlType.BASE
    """📵控件的基本类型"""
    PropsName: str = "props"
    """📵控件所属属性集的名称"""
    Props: Any = None
    """📵控控件所属属性集"""
    Name: str = ""
    """📵控件的唯一名"""
    Description: str = ""
    """📵控件显示给用户的信息"""
    LongDescription: str = "长介绍测试"
    """📵长描述"""
    Type: Any = None
    """📵控件的功能类型"""
    Obj: Any = None
    """📵控件的obs对象"""
    LoadOrder: int = 0
    """📵控件的加载顺序数"""
    ModifiedIs: bool = False
    """📵控件变动是否触发钩子函数"""
    Visible: bool = True
    """控件的可见状态"""
    Enabled: bool = True
    """控件的可用状态"""

    def __repr__(self) -> str:
        """提供清晰的数据类表示，便于调试。"""
        return (f"<{self.__class__.__name__} name='{self.Name}' "
                f"type={self.Type.value} order={self.LoadOrder}>")


class Widget:
    """表单管理器，管理所有控件"""

    class CheckBoxPs:
        """复选框控件管理器"""

        @dataclass
        class CheckBoxP(ControlBase):
            """复选框控件实例"""
            WidgetType: ControlType = ControlType.CHECKBOX
            """📵复选框的控件类型为 CheckBox"""
            Bool: bool = False
            """复选框的选中状态"""

            def __repr__(self) -> str:
                type_name = "复选框"
                return f"<CheckBoxP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Bool={self.Bool}>"

        def __init__(self):
            self._controls: Dict[str, Widget.CheckBoxPs.CheckBoxP] = {}
            self._loading_order: List[Widget.CheckBoxPs.CheckBoxP] = []

        def add(self, name: str, **kwargs) -> CheckBoxP:
            """添加复选框控件"""
            if name in self._controls:
                raise ValueError(f"复选框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.CheckBoxPs.CheckBoxP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[CheckBoxP]:
            """获取复选框控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除复选框控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[CheckBoxP]:
            """迭代所有复选框控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """复选框控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查复选框控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[CheckBoxP]:
            """获取按载入次序排序的复选框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class DigitalBoxPs:
        """数字框控件管理器"""

        @dataclass
        class DigitalBoxP(ControlBase):
            """数字框控件实例"""
            WidgetType: ControlType = ControlType.DIGITALBOX
            """📵数字框的控件类型为 PathBox"""
            Type: Literal[
                "Int",
                "Float",
                "IntSlider",
                "FloatSlider"
            ] = "Int"
            """
            📵数字框的类型
            Int 表示整数数字框，
            Float 表示浮点数数字框，
            IntSlider 表示整数数字框带滑块，
            FloatSlider 表示浮点数数字框带滑块，
            """
            Value: int = 0
            """数字框显示的数值"""
            Suffix: str = ""
            """数字框显示的数值的单位"""
            Min: int = 0
            """数字框显示的数值的最小值"""
            Max: int = 0
            """数字框显示的数值的最大值"""
            Step: int = 0
            """数字框显示的步长"""

            def __repr__(self) -> str:
                type_name = "数字框"
                if self.Type == "Int":
                    type_name = "整数"
                elif self.Type == "Float":
                    type_name = "浮点数"
                elif self.Type == "IntSlider":
                    type_name = "整数滑块"
                elif self.Type == "FloatSlider":
                    type_name = "浮点滑块"
                return f"<DigitalBoxP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Min={self.Min} Max={self.Max}>"

        def __init__(self):
            self._controls: Dict[str, Widget.DigitalBoxPs.DigitalBoxP] = {}
            self._loading_order: List[Widget.DigitalBoxPs.DigitalBoxP] = []

        def add(self, name: str, **kwargs) -> DigitalBoxP:
            """添加数字框控件"""
            if name in self._controls:
                raise ValueError(f"数字框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.DigitalBoxPs.DigitalBoxP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[DigitalBoxP]:
            """获取数字框控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除数字框控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[DigitalBoxP]:
            """迭代所有数字框控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """数字框控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查数字框控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[DigitalBoxP]:
            """获取按载入次序排序的数字框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class TextBoxPs:
        """文本框控件管理器"""

        @dataclass
        class TextBoxP(ControlBase):
            """文本框控件实例"""
            WidgetType: ControlType = ControlType.TEXTBOX
            """📵文本框的控件类型为 TextBox"""
            Type: Optional[int] = obs.OBS_TEXT_DEFAULT  # 文本框类型
            """📵文本框的类型
            OBS_TEXT_DEFAULT 表示单行文本框，
            OBS_TEXT_PASSWORD 表示单行密码文本框，
            OBS_TEXT_MULTILINE 表示多行文本框，
            OBS_TEXT_INFO 表示不可编辑的只读文本框，效果类似于标签。
            """
            Text: str = ""
            """文本框显示的文字"""
            InfoType: Any = obs.OBS_TEXT_INFO_NORMAL  # 信息类型
            """
            只读文本框控件的信息类型
            OBS_TEXT_INFO_NORMAL 表示正常信息，
            OBS_TEXT_INFO_WARNING 表示警告信息，
            OBS_TEXT_INFO_ERROR 表示错误信息
            """

            def __repr__(self) -> str:
                type_name = "文本框"
                if self.Type == obs.OBS_TEXT_DEFAULT:
                    type_name = "单行文本"
                elif self.Type == obs.OBS_TEXT_PASSWORD:
                    type_name = "单行文本（带密码）"
                elif self.Type == obs.OBS_TEXT_MULTILINE:
                    type_name = "多行文本"
                elif self.Type == obs.OBS_TEXT_INFO:
                    type_name = "只读信息文本"
                return f"<TextBoxP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Text='{self.Text}'>"

        def __init__(self):
            self._controls: Dict[str, Widget.TextBoxPs.TextBoxP] = {}
            self._loading_order: List[Widget.TextBoxPs.TextBoxP] = []

        def add(self, name: str, **kwargs) -> TextBoxP:
            """添加文本框控件"""
            if name in self._controls:
                raise ValueError(f"文本框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.TextBoxPs.TextBoxP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[TextBoxP]:
            """获取文本框控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除文本框控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[TextBoxP]:
            """迭代所有文本框控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """文本框控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查文本框控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[TextBoxP]:
            """获取按载入次序排序的文本框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class ButtonPs:
        """按钮控件管理器"""

        @dataclass
        class ButtonP(ControlBase):
            """按钮控件实例"""
            WidgetType: ControlType = ControlType.BUTTON
            """📵按钮的控件类型为 Button"""
            Type: Optional[int] = obs.OBS_BUTTON_DEFAULT  # 按钮类型
            """
            📵按钮的类型 
            OBS_BUTTON_DEFAULT 表示标准普通按钮，
            OBS_BUTTON_URL 表示可打开指定 URL 的链接按钮。
            """
            Callback: Optional[Callable[[Any, Any], Literal[True, False]]] = None  # 回调函数
            """📵按钮被按下后触发的回调函数"""
            Url: str = ""  # 需要打开的 URL
            """📵URL类型的按钮被按下后跳转的URL"""

            def __repr__(self) -> str:
                type_name = "按钮"
                if self.Type == obs.OBS_BUTTON_DEFAULT:
                    type_name = "标准按钮"
                elif self.Type == obs.OBS_BUTTON_URL:
                    type_name = "打开 URL 的按钮"
                return f"<ButtonP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Callback={self.Callback is not None}>"

        def __init__(self):
            self._controls: Dict[str, Widget.ButtonPs.ButtonP] = {}
            self._loading_order: List[Widget.ButtonPs.ButtonP] = []

        def add(self, name: str, **kwargs) -> ButtonP:
            """添加按钮控件"""
            if name in self._controls:
                raise ValueError(f"按钮 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.ButtonPs.ButtonP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[ButtonP]:
            """获取按钮控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除按钮控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[ButtonP]:
            """迭代所有按钮控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """按钮控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查按钮控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[ButtonP]:
            """获取按载入次序排序的按钮控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class ComboBoxPs:
        """组合框控件管理器"""

        @dataclass
        class ComboBoxP(ControlBase):
            """组合框控件实例"""
            WidgetType: ControlType = ControlType.COMBOBOX
            """📵组合框的控件类型为 ComboBox"""
            Type: Optional[int] = obs.OBS_COMBO_TYPE_LIST  # 组合框类型
            """
            📵组合框类型
            OBS_COMBO_TYPE_EDITABLE 表示可编辑组合框，仅适用于字符串格式，用户可以输入自己的内容，
            OBS_COMBO_TYPE_LIST 表示不可编辑组合框
            """
            Text: str = ""
            """组合框显示的文字"""
            Value: str = ""
            """组合框显示的文字对应的值"""
            DictionaryList: List[Dict[str, str]] = field(default_factory=list)  # 数据字典
            """组合框选项数据列表 显示文字为键label 选项值为键value"""

            def __repr__(self) -> str:
                type_name = "组合框"
                if self.Type == obs.OBS_COMBO_TYPE_EDITABLE:
                    type_name = "可以编辑。 仅与字符串列表一起使用"
                elif self.Type == obs.OBS_COMBO_TYPE_LIST:
                    type_name = "不可编辑。显示为组合框"
                elif self.Type == obs.OBS_COMBO_TYPE_RADIO:
                    type_name = "不可编辑。显示为单选按钮"
                return f"<ComboBoxP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Text='{self.Text}'>"

        def __init__(self):
            self._controls: Dict[str, Widget.ComboBoxPs.ComboBoxP] = {}
            self._loading_order: List[Widget.ComboBoxPs.ComboBoxP] = []

        def add(self, name: str, **kwargs) -> ComboBoxP:
            """添加组合框控件"""
            if name in self._controls:
                raise ValueError(f"组合框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.ComboBoxPs.ComboBoxP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[ComboBoxP]:
            """获取组合框控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除组合框控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[ComboBoxP]:
            """迭代所有组合框控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """组合框控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查组合框控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[ComboBoxP]:
            """获取按载入次序排序的组合框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class PathBoxPs:
        """路径对话框控件管理器"""

        @dataclass
        class PathBoxP(ControlBase):
            """路径对话框控件实例"""
            WidgetType: ControlType = ControlType.PATHBOX
            """📵路径对话框的控件类型为 PathBox"""
            Type: Optional[int] = obs.OBS_PATH_FILE  # 路径对话框类型
            """
            📵路径对话框的类型
            OBS_PATH_FILE 表示读取文件的对话框，
            OBS_PATH_FILE_SAVE 表示写入文件的对话框，
            OBS_PATH_DIRECTORY 表示选择文件夹的对话框。
            """
            Text: str = ""
            """路径对话框显示的路径"""
            Filter: Optional[str] = ""  # 文件种类（筛选条件）
            """路径对话框筛选的文件种类（筛选条件）"""
            StartPath: str = ""  # 对话框起始路径
            """路径对话框选择文件的起始路径"""

            def __repr__(self) -> str:
                type_name = "路径对话框"
                if self.Type == obs.OBS_PATH_FILE:
                    type_name = "文件对话框"
                elif self.Type == obs.OBS_PATH_FILE_SAVE:
                    type_name = "保存文件对话框"
                elif self.Type == obs.OBS_PATH_DIRECTORY:
                    type_name = "文件夹对话框"
                return f"<PathBoxP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}' Text='{self.Text}'>"

        def __init__(self):
            self._controls: Dict[str, Widget.PathBoxPs.PathBoxP] = {}
            self._loading_order: List[Widget.PathBoxPs.PathBoxP] = []

        def add(self, name: str, **kwargs) -> PathBoxP:
            """添加路径对话框控件"""
            if name in self._controls:
                raise ValueError(f"路径对话框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            control = Widget.PathBoxPs.PathBoxP(**kwargs)
            self._controls[name] = control
            self._loading_order.append(control)
            setattr(self, name, control)
            return control

        def get(self, name: str) -> Optional[PathBoxP]:
            """获取路径对话框控件"""
            return self._controls.get(name)

        def remove(self, name: str) -> bool:
            """移除路径对话框控件"""
            if name in self._controls:
                control = self._controls.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if control in self._loading_order:
                    self._loading_order.remove(control)
                return True
            return False

        def __iter__(self) -> Iterator[PathBoxP]:
            """迭代所有路径对话框控件"""
            return iter(self._controls.values())

        def __len__(self) -> int:
            """路径对话框控件数量"""
            return len(self._controls)

        def __contains__(self, name: str) -> bool:
            """检查路径对话框控件是否存在"""
            return name in self._controls

        def get_loading_order(self) -> List[PathBoxP]:
            """获取按载入次序排序的路径对话框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    class GroupPs:
        """分组框控件管理器"""

        @dataclass
        class GroupP(ControlBase):
            """分组框控件实例（独立控件）"""
            WidgetType: ControlType = ControlType.GROUP
            """📵分组框的控件类型为 Group"""
            Type: Any = obs.OBS_GROUP_NORMAL  # 分组框类型
            """
            📵分组框的类型
            OBS_GROUP_NORMAL 表示标准普通分组框，
            OBS_GROUP_CHECKABLE 表示拥有复选框的分组框。
            """
            GroupPropsName: str = "GroupProps"
            """📵分组框的自身控件属性集的名称"""
            GroupProps: Any = None  # 统辖属性集
            """📵分组框的自身控件属性集"""
            Bool: bool = True
            """带复选框的分组框的选中状态"""
            ObjFolding: Any = None  # 折叠后的对象
            """带复选框的分组框折叠后的对象"""

            def __repr__(self) -> str:
                type_name = "分组框"
                if self.Type == obs.OBS_GROUP_NORMAL:
                    type_name = "只有名称和内容的普通组"
                elif self.Type == obs.OBS_GROUP_CHECKABLE:
                    type_name = "具有复选框、名称和内容的可选组"
                return f"<GroupP Name='{self.Name}' LoadOrder={self.LoadOrder} Type='{type_name}'>"

        def __init__(self):
            self._groups: Dict[str, Widget.GroupPs.GroupP] = {}
            self._loading_order: List[Widget.GroupPs.GroupP] = []

        def add(self, name: str, **kwargs) -> GroupP:
            """添加分组框控件"""
            if name in self._groups:
                raise ValueError(f"分组框 '{name}' 已存在")
            # 确保Name属性设置正确
            if "Name" not in kwargs:
                kwargs["Name"] = name
            group = Widget.GroupPs.GroupP(**kwargs)
            self._groups[name] = group
            self._loading_order.append(group)
            setattr(self, name, group)
            return group

        def get(self, name: str) -> Optional[GroupP]:
            """获取分组框控件"""
            return self._groups.get(name)

        def remove(self, name: str) -> bool:
            """移除分组框控件"""
            if name in self._groups:
                group = self._groups.pop(name)
                if hasattr(self, name):
                    delattr(self, name)
                if group in self._loading_order:
                    self._loading_order.remove(group)
                return True
            return False

        def __iter__(self) -> Iterator[GroupP]:
            """迭代所有分组框控件"""
            return iter(self._groups.values())

        def __len__(self) -> int:
            """分组框控件数量"""
            return len(self._groups)

        def __contains__(self, name: str) -> bool:
            """检查分组框控件是否存在"""
            return name in self._groups

        def get_loading_order(self) -> List[GroupP]:
            """获取按载入次序排序的分组框控件列表"""
            return sorted(self._loading_order, key=lambda c: c.LoadOrder)

    def __init__(self):
        """初始化表单管理器"""
        self.CheckBox = Widget.CheckBoxPs()
        """复选框"""
        self.DigitalBox = Widget.DigitalBoxPs()
        """数字框"""
        self.TextBox = Widget.TextBoxPs()
        """文本框"""
        self.Button = Widget.ButtonPs()
        """按钮"""
        self.ComboBox = Widget.ComboBoxPs()
        """组合框"""
        self.PathBox = Widget.PathBoxPs()
        """路径对话框"""
        self.Group = Widget.GroupPs()
        """分组框"""
        self.widget_Button_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        按钮控件不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                按钮控件的不变属性字典[
                    "Name"|"Description"|“Type”|“Callback”｜“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜按钮类型｜按钮回调｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_Group_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        分组框控件不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                分组框控件的不变属性字典[
                    "Name"|"Description"|“Type”|“GroupProps”｜“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜分组框类型｜分组框携带属性集名称｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_TextBox_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        文本框控件不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                文本框控件的不变属性字典[
                    "Name"|"Description"|“Type”|“LongDescription”｜“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜文本框类型｜控件用户层长介绍｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_ComboBox_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        组合框控件不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                组合框控件的不变属性字典[
                    "Name"|"Description"|“Type”|“LongDescription”｜“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜组合框类型｜控件用户层长介绍｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_PathBox_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        路径对话框不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                路径对话框的不变属性字典[
                    "Name"|"Description"|“Type”|“Filter”|“StartPath”｜“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜路径对话框类型｜文件格式筛选｜起步路径｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_DigitalBox_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        数字框不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                数字框的不变属性字典[
                    "Name"|"Description"|“Type”|“Suffix”|“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜数字框类型｜单位后缀｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_CheckBox_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        """
        复选框不变属性的整体数据字典[
            控件所属属性集名称,
            控件不变属性字典[
                控件在类中的对象名, 
                复选框的不变属性字典[
                    "Name"|"Description"|“ModifiedIs”, 
                    控件唯一名|控件用户层介绍｜控件改动是否触发控件变动事件
                ]
            ]
        ]
        """
        self.widget_list: List[str] = []
        """一个用于规定控件加载顺序的列表，内容是控件名称"""
        self.props_Collection: dict[str, set[str]] = {}
        """控件属性集名称为键 控件名称组成的集合为值 的字典"""
        self._all_controls: List[Any] = []
        self._loading_dict: Dict[int, Any] = {}

    @property
    def widget_dict_all(self) -> dict[ControlType, dict[str, dict[str, dict[str, Union[Callable[[Any, Any], bool], str]]]]]:
        """
        记录10大控件类型的所有控件的不变属性
        控件类型为键 注册控件时设置的控件不变属性字典为值 的字典
        """
        return {
            ControlType.GROUP: self.widget_Group_dict,
            ControlType.BUTTON: self.widget_Button_dict,
            ControlType.TEXTBOX: self.widget_TextBox_dict,
            ControlType.COMBOBOX: self.widget_ComboBox_dict,
            ControlType.PATHBOX: self.widget_PathBox_dict,
            ControlType.DIGITALBOX: self.widget_DigitalBox_dict,
            ControlType.CHECKBOX: self.widget_CheckBox_dict,
        }

    @property
    def verification_number_controls(self):
        """和排序列表进行控件数量验证"""
        return len(self.widget_list) == len(self.get_sorted_controls())

    def _update_all_controls(self):
        """更新所有控件列表"""
        self._all_controls = []
        # 收集所有类型的控件
        self._all_controls.extend(self.CheckBox)
        self._all_controls.extend(self.DigitalBox)
        self._all_controls.extend(self.TextBox)
        self._all_controls.extend(self.Button)
        self._all_controls.extend(self.ComboBox)
        self._all_controls.extend(self.PathBox)
        self._all_controls.extend(self.Group)

    def loading(self):
        """按载入次序排序所有控件"""
        self._update_all_controls()
        # 按LoadOrder属性排序
        sorted_controls = sorted(self._all_controls, key=lambda c: c.LoadOrder)
        name_dict = {}  # 用于检测名称冲突

        # 创建载入次序字典
        self._loading_dict = {}
        for control in sorted_controls:
            # 检查名称冲突
            if control.Name in name_dict:
                existing_control = name_dict[control.Name]
                raise ValueError(
                    f"控件名称冲突: 控件 '{control.Name}' "
                    f"(类型: {type(control).__name__}, 载入次序: {control.LoadOrder}) 与 "
                    f"'{existing_control.Name}' "
                    f"(类型: {type(existing_control).__name__}, 载入次序: {existing_control.LoadOrder}) 重名"
                )
            else:
                name_dict[control.Name] = control
            if control.LoadOrder in self._loading_dict:
                existing_control = self._loading_dict[control.LoadOrder]
                raise ValueError(
                    f"载入次序冲突: 控件 '{control.Name}' (类型: {type(control).__name__}) 和 "
                    f"'{existing_control.Name}' (类型: {type(existing_control).__name__}) "
                    f"使用相同的LoadOrder值 {control.LoadOrder}"
                )
            self._loading_dict[control.LoadOrder] = control

    def get_control_by_number(self, number: int) -> Optional[Any]:
        """通过载入次序获取控件"""
        self.loading()  # 确保已排序
        return self._loading_dict.get(number)

    def get_control_by_name(self, name: str) -> Optional[Any]:
        """通过名称获取控件"""
        # 在顶级控件中查找
        for manager in [
            self.CheckBox,
            self.DigitalBox,
            self.TextBox,
            self.Button,
            self.ComboBox,
            self.PathBox,
            self.Group
        ]:
            if name in manager:
                return manager.get(name)
        return None

    def get_sorted_controls(self) -> List[Any]:
        """获取按载入次序排序的所有控件列表"""
        self.loading()
        return list(self._loading_dict.values())

    def clean(self):
        """清除所有控件并重置表单"""
        # 重置所有控件管理器
        self.CheckBox = Widget.CheckBoxPs()
        self.DigitalBox = Widget.DigitalBoxPs()
        self.TextBox = Widget.TextBoxPs()
        self.Button = Widget.ButtonPs()
        self.ComboBox = Widget.ComboBoxPs()
        self.PathBox = Widget.PathBoxPs()
        self.Group = Widget.GroupPs()

        # 清空内部存储
        self._all_controls = []
        self._loading_dict = {}

        return self  # 支持链式调用

    def preliminary_configuration_control(self):
        """创建初始控件数据"""
        for basic_types_controls in self.widget_dict_all:
            log_save(obs.LOG_INFO, f"{basic_types_controls}")
            if basic_types_controls == ControlType.GROUP:
                for prop_attribute in self.widget_dict_all[basic_types_controls].values():
                    for attribute in prop_attribute.values():
                        if attribute["GroupPropsName"] not in self.props_Collection:
                            self.props_Collection[attribute["GroupPropsName"]] = set()
            for PropsName in self.widget_dict_all[basic_types_controls]:
                log_save(obs.LOG_INFO, f"\t{PropsName}")
                if PropsName not in self.props_Collection:
                    self.props_Collection[PropsName] = set()  # 添加键 属性集名称
                for objName in self.widget_dict_all[basic_types_controls][PropsName]:
                    log_save(obs.LOG_INFO, f"\t\t添加 {objName}")
                    widget_types_controls = getattr(self, str(basic_types_controls.value))
                    widget_types_controls.add(objName)
                    obj = getattr(widget_types_controls, objName)
                    obj.PropsName = PropsName
                    obj.Name = self.widget_dict_all[basic_types_controls][PropsName][objName]["Name"]
                    obj.Description = self.widget_dict_all[basic_types_controls][PropsName][objName]["Description"]
                    obj.LongDescription = self.widget_dict_all[basic_types_controls][PropsName][objName].get("LongDescription", obj.LongDescription)
                    obj.Type = self.widget_dict_all[basic_types_controls][PropsName][objName].get("Type", obj.Type)
                    obj.LoadOrder = self.widget_list.index(obj.Name)
                    obj.ModifiedIs = self.widget_dict_all[basic_types_controls][PropsName][objName].get("ModifiedIs", obj.ModifiedIs)
                    if obj.WidgetType in [ControlType.BUTTON]:
                        obj.Callback = self.widget_dict_all[basic_types_controls][PropsName][objName].get("Callback", obj.Callback)
                        obj.Url = self.widget_dict_all[basic_types_controls][PropsName][objName].get("Url", obj.Url)
                    if obj.WidgetType in [ControlType.GROUP]:
                        obj.GroupPropsName = self.widget_dict_all[basic_types_controls][PropsName][objName].get("GroupPropsName", obj.GroupPropsName)
                    if obj.WidgetType in [ControlType.DIGITALBOX]:
                        obj.Suffix = self.widget_dict_all[basic_types_controls][PropsName][objName].get("Suffix", obj.Suffix)
                    if obj.WidgetType in [ControlType.PATHBOX]:
                        obj.Filter = self.widget_dict_all[basic_types_controls][PropsName][objName].get("Filter", obj.Filter)
                        obj.StartPath = self.widget_dict_all[basic_types_controls][PropsName][objName]["StartPath"]
                    self.props_Collection[PropsName].add(obj.Name)  # 添加值 控件名称

    def __repr__(self) -> str:
        """返回表单的可读表示形式"""
        self._update_all_controls()
        return f"<Widget controls={len(self._all_controls)}>"


def trigger_frontend_event(event):
    """
    处理推流事件
    Args:
        event: obs前端事件

    Returns:

    """
    log_save(obs.LOG_INFO, f"监测到obs前端事件: {ExplanatoryDictionary.information4frontend_event[event]}")

    if GlobalVariableOfData.causeOfTheFrontDeskIncident:
        log_save(obs.LOG_INFO, f"此次 事件 由【{GlobalVariableOfData.causeOfTheFrontDeskIncident}】引起")

    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        if not GlobalVariableOfData.causeOfTheFrontDeskIncident:
            log_save(obs.LOG_INFO, f"此次 OBS 完成加载 事件 由前台事件引起")

        pass
    elif event == obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN:
        if not GlobalVariableOfData.causeOfTheFrontDeskIncident:
            log_save(obs.LOG_INFO,f"此次 脚本关闭中 事件 由前台事件引起")

        pass
    return True


def property_modified(widget_name: str) -> bool:
    """
    控件变动拉钩
    Args:
        widget_name: 控件全局唯一名

    Returns:

    """
    log_save(obs.LOG_INFO, f"检测到控件【{widget_name}】变动事件")
    if widget_name == "bottom_button":  # 这个按钮用来标记脚本开始构造控件
        log_save(obs.LOG_INFO, f"检测到脚本构造控件体开始，断开控件事件钩子")
        GlobalVariableOfData.isScript_propertiesIs = True
    if widget_name == "top_button":
        log_save(obs.LOG_INFO, f"检测到脚本构造控件体结束，启动控件事件钩子")
        GlobalVariableOfData.isScript_propertiesIs = False
    if not GlobalVariableOfData.isScript_propertiesIs:  #  执行触发事件动作
        group_widget_attribute: List[str] = []
        """所有分组框名称的列表"""
        for prop_attribute in widget.widget_Group_dict.values():
            for attribute in prop_attribute.values():
                group_widget_attribute.append(attribute["Name"])
                if attribute["Type"] == obs.OBS_GROUP_CHECKABLE:
                    group_widget_attribute.append(f'{attribute["Name"]}_folding')
        if widget_name in group_widget_attribute:
            return ButtonFunction.button_function_fold_group()
        else:
            log_save(obs.LOG_INFO, widget_name)
        pass
    else:
        log_save(obs.LOG_INFO, f"控件事件钩子已断开")
        return False
    return False


# --- 设置默认值
def script_defaults(settings):  # 设置其默认值
    """
    调用以设置与脚本关联的默认设置(如果有的话)。为了设置其默认值，您通常会调用默认值函数。
    :param settings:与脚本关联的设置。
    """
    log_save(obs.LOG_INFO, "script_defaults 被调用")
    # =================================================================================================================
    # 设置脚本属性=======================================================================================================
    GlobalVariableOfData.script_settings = settings

    # 设置控件属性参数
    GlobalVariableOfData.scriptsDataDirpath = Path(f"{script_path()}ObsScriptsFrameworkTesting")
    log_save(obs.LOG_INFO, f"║║脚本用户数据文件夹路径：{GlobalVariableOfData.scriptsDataDirpath}")
    GlobalVariableOfData.scriptsTempDir = Path(GlobalVariableOfData.scriptsDataDirpath) / "temp"
    os.makedirs(GlobalVariableOfData.scriptsTempDir, exist_ok=True)
    log_save(obs.LOG_INFO, f"║║脚本临时文件夹路径：{GlobalVariableOfData.scriptsTempDir}")
    GlobalVariableOfData.scriptsLogDir = Path(GlobalVariableOfData.scriptsDataDirpath) / "log"
    os.makedirs(GlobalVariableOfData.scriptsLogDir, exist_ok=True)
    log_save(obs.LOG_INFO, f"║║脚本日志文件夹路径：{GlobalVariableOfData.scriptsLogDir}")
    GlobalVariableOfData.scriptsCacheDir = Path(GlobalVariableOfData.scriptsDataDirpath) / "cache"
    os.makedirs(GlobalVariableOfData.scriptsCacheDir, exist_ok=True)
    log_save(obs.LOG_INFO, f"║║脚本缓存文件夹路径：{GlobalVariableOfData.scriptsCacheDir}")

    # =================================================================================================================
    # 设置属性集合=======================================================================================================
    update_widget_name = set()
    """需要更新的控件的名称的集合"""
    if not GlobalVariableOfData.update_widget_attribute_dict:
        GlobalVariableOfData.update_widget_attribute_dict = widget.props_Collection
    for props_name in GlobalVariableOfData.update_widget_attribute_dict:
        update_widget_name |= GlobalVariableOfData.update_widget_attribute_dict[props_name]
    log_save(obs.LOG_INFO, f"║║💫更新以下控件：{update_widget_name}")
    update_widget_name |= GlobalVariableOfData.group_folding_names | FunctionCache.get_common_widget_groups_visibility()

    GlobalVariableOfData.group_folding_names = FunctionCache.get_common_widget_groups_visibility()

    log_save(obs.LOG_INFO, f"折叠以下分组框：{GlobalVariableOfData.group_folding_names}")

    widget_specific_object = widget.Group.test
    if widget_specific_object.Name in update_widget_name:
        widget_specific_object.Visible = widget_specific_object.Name not in GlobalVariableOfData.group_folding_names
        widget_specific_object.Enabled = widget_specific_object.Name not in GlobalVariableOfData.group_folding_names
        widget_specific_object.Bool = widget_specific_object.Name not in GlobalVariableOfData.group_folding_names

    # =================================================================================================================
    # 设置控件属性=======================================================================================================
    widget_specific_object = widget.Button.top
    if widget_specific_object.Name in update_widget_name:
        widget_specific_object.Visible = False
        widget_specific_object.Enabled = False

    widget_specific_object = widget.ComboBox.test
    if widget_specific_object.Name in update_widget_name:
        widget_specific_object.Visible = True
        widget_specific_object.Enabled = True
        widget_specific_object.Text = FunctionCache.get_combobox_test_load_data()["Text"]
        widget_specific_object.Value = FunctionCache.get_combobox_test_load_data()["Value"]
        widget_specific_object.DictionaryList = FunctionCache.get_combobox_test_load_data()["DictionaryList"]

    widget_specific_object = widget.Button.test
    if widget_specific_object.Name in update_widget_name:
        widget_specific_object.Visible = True
        widget_specific_object.Enabled = True

    widget_specific_object = widget.Button.bottom
    if widget_specific_object.Name in update_widget_name:
        widget_specific_object.Visible = False
        widget_specific_object.Enabled = False

    FunctionCache.cache_clear()
    return True


# --- 一个名为script_description的函数返回显示给的描述
def script_description():
    """
    调用以检索要在“脚本”窗口中显示给用户的描述字符串。
    """
    log_save(obs.LOG_INFO, "script_defaults 被调用")
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


# --- 一个名为script_load的函数将在启动时调用
def script_load(settings):
    """
    在脚本启动时调用与脚本相关的特定设置。所提供的设置参数通常不用于由用户设置的设置;
    相反，该参数用于脚本中可能使用的任何额外的内部设置数据。
    :param settings:与脚本关联的设置。
    """
    log_save(obs.LOG_INFO, "script_load 被调用")
    obs.obs_frontend_add_event_callback(trigger_frontend_event)
    pass


# 控件状态更新时调用
def script_update(settings):
    """
    当用户更改了脚本的设置(如果有的话)时调用。
    这里更改控件属性不会实时显示，
    不要在这里控制控件的【可见】、【可用】、【值】和【名称】
    :param settings:与脚本关联的设置。
    """
    log_save(obs.LOG_INFO, "script_update 被调用")
    pass



# --- 2. 注册装饰器和注册表 ---
_control_creator_registry: Dict[ControlType, Callable] = {}

def creates(control_type: ControlType):
    """装饰器：自动注册控件创建函数到全局注册表"""

    def decorator(creator_func: Callable) -> Callable:
        if control_type in _control_creator_registry:
            raise ValueError(f"控件类型 {control_type} 已注册")
        _control_creator_registry[control_type] = creator_func
        return creator_func

    return decorator

# --- 3. 各控件的具体创建函数 ---

@creates(ControlType.TEXTBOX)
def _create_textbox(w) -> None:
    """
    创建文本框控件
    支持类型: OBS_TEXT_DEFAULT(默认), OBS_TEXT_PASSWORD(密码),
             OBS_TEXT_MULTILINE(多行), OBS_TEXT_INFO(信息文本)
    """
    log_save(obs.LOG_INFO, f"文本框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量（假设w.Type已经是OBS常量或可转换的字符串）
    obs_text_type = getattr(obs, f"OBS_TEXT_{w.Type}", obs.OBS_TEXT_DEFAULT) if isinstance(w.Type, str) else w.Type
    w.Obj = obs.obs_properties_add_text(w.Props, w.Name, w.Description, obs_text_type)

    # 如果是信息文本类型，设置信息类型
    if hasattr(w, 'InfoType') and obs_text_type == obs.OBS_TEXT_INFO:
        obs.obs_property_text_set_info_type(w.Obj, w.InfoType)

@creates(ControlType.BUTTON)
def _create_button(w) -> None:
    """
    创建按钮控件
    支持类型: OBS_BUTTON_DEFAULT(默认), OBS_BUTTON_URL(URL链接)
    """
    log_save(obs.LOG_INFO, f"按钮控件: {w.Name} 【{w.Description}】")

    # 创建按钮（回调函数w.Callback需提前定义）
    w.Obj = obs.obs_properties_add_button(w.Props, w.Name, w.Description, w.Callback)

    # 设置按钮类型
    obs_button_type = getattr(obs, f"OBS_BUTTON_{w.Type}", obs.OBS_BUTTON_DEFAULT) if isinstance(w.Type,
                                                                                                 str) else w.Type
    obs.obs_property_button_set_type(w.Obj, obs_button_type)

    # 如果是URL按钮，设置URL地址
    if obs_button_type == obs.OBS_BUTTON_URL and hasattr(w, 'Url'):
        obs.obs_property_button_set_url(w.Obj, w.Url)

@creates(ControlType.COMBOBOX)
def _create_combobox(w) -> None:
    """
    创建组合框（下拉列表）控件
    支持类型: OBS_COMBO_TYPE_LIST(列表), OBS_COMBO_TYPE_EDITABLE(可编辑)
    """
    log_save(obs.LOG_INFO, f"组合框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_combo_type = getattr(obs, f"OBS_COMBO_TYPE_{w.Type}", obs.OBS_COMBO_TYPE_LIST) if isinstance(w.Type,
                                                                                                     str) else w.Type

    # 创建组合框，格式固定为字符串
    w.Obj = obs.obs_properties_add_list(
        w.Props,
        w.Name,
        w.Description,
        obs_combo_type,
        obs.OBS_COMBO_FORMAT_STRING
    )

    # 如果有预定义选项列表，则添加选项
    if hasattr(w, 'DictionaryList') and w.DictionaryList:
        # 首先添加默认选项（如果有）
        if hasattr(w, 'Text') and hasattr(w, 'Value'):
            obs.obs_property_list_insert_string(w.Obj, 0, w.Text, w.Value)

        # 添加其他选项（排除默认选项避免重复）
        for item in w.DictionaryList:
            item_label = item.get("label", "")
            item_value = item.get("value", "")
            if item_label != getattr(w, 'Text', ""):
                obs.obs_property_list_add_string(w.Obj, item_label, item_value)

@creates(ControlType.PATHBOX)
def _create_pathbox(w) -> None:
    """
    创建路径选择框控件
    支持类型: OBS_PATH_FILE(文件), OBS_PATH_DIRECTORY(目录)
    """
    log_save(obs.LOG_INFO, f"路径对话框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_path_type = getattr(obs, f"OBS_PATH_{w.Type}", obs.OBS_PATH_FILE) if isinstance(w.Type, str) else w.Type

    # 获取过滤器、起始路径等可选参数
    filter_str = getattr(w, 'Filter', "*.*")
    default_path = getattr(w, 'StartPath', "")

    w.Obj = obs.obs_properties_add_path(
        w.Props,
        w.Name,
        w.Description,
        obs_path_type,
        filter_str,
        default_path
    )

@creates(ControlType.GROUP)
def _create_group(w) -> None:
    """
    创建分组框控件
    支持类型: OBS_GROUP_NORMAL(普通), OBS_GROUP_CHECKABLE(可勾选)
    """
    log_save(obs.LOG_INFO, f"分组框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_group_type = getattr(obs, f"OBS_GROUP_{w.Type}", obs.OBS_GROUP_NORMAL) if isinstance(w.Type, str) else w.Type

    # 确保分组有对应的属性集对象
    if not hasattr(w, 'GroupProps'):
        log_save(obs.LOG_WARNING, f"分组 {w.Name} 缺少GroupProps属性")
        return

    w.Obj = obs.obs_properties_add_group(
        w.Props,
        w.Name,
        w.Description,
        obs_group_type,
        w.GroupProps
    )

    # 如果是可勾选分组，创建额外的折叠控制复选框
    if obs_group_type == obs.OBS_GROUP_CHECKABLE:
        folding_name = f"{w.Name}_folding"
        folding_desc = f"{w.Description}[折叠]"
        w.FoldingObj = obs.obs_properties_add_bool(w.Props, folding_name, folding_desc)
        log_save(obs.LOG_INFO, f"创建可勾选分组折叠控制: {folding_name}")

@creates(ControlType.CHECKBOX)
def _create_checkbox(w):
    """创建复选框控件"""
    log_save(obs.LOG_INFO, f"复选框控件: {w.Name} 【{w.Description}】")
    w.Obj = obs.obs_properties_add_bool(w.Props, w.Name, w.Description)

@creates(ControlType.DIGITALBOX)
def _create_digitalbox(w):
    """创建数字输入或滑块控件"""
    log_save(obs.LOG_INFO, f"数字框控件: {w.Name} 【{w.Description}】")
    type_map = {
        "IntSlider": obs.obs_properties_add_int_slider,
        "Int": obs.obs_properties_add_int,
        "FloatSlider": obs.obs_properties_add_float_slider,
        "Float": obs.obs_properties_add_float,
    }
    creator_func = type_map.get(w.Type, obs.obs_properties_add_float_slider)
    w.Obj = creator_func(w.Props, w.Name, w.Description, w.Min, w.Max, w.Step)
    if w.Suffix:
        obs.obs_property_int_set_suffix(w.Obj, w.Suffix)

# --- 4. 辅助函数：获取创建器 ---
def get_control_creator(control_type: ControlType):
    """根据控件类型字符串获取对应的创建函数"""
    try:
        return _control_creator_registry.get(control_type)
    except ValueError:
        log_save(obs.LOG_WARNING, f"未知的控件类型: {control_type}")
        return None

def _init_property_sets(widgets):
    """职责1：初始化所有需要的属性集"""
    props_dict = {"props": obs.obs_properties_create()}
    for props_name in widget.props_Collection:
        props_dict[props_name] = obs.obs_properties_create()
    for w in widgets:
        w.Props = props_dict[w.PropsName]
        if w.WidgetType == ControlType.GROUP:
            w.GroupProps = props_dict[w.GroupPropsName]
    return props_dict

def _create_control_for_widget(w):
    """为单个控件对象执行创建和通用设置"""
    # 1. 获取对应的创建函数
    creator = get_control_creator(w.WidgetType)
    if not creator:
        log_save(obs.LOG_WARNING, f"未找到 {w.WidgetType} 的创建器，跳过")
        return

    # 2. 执行创建
    creator(w)

    # 3. 设置长描述（所有控件通用）
    if hasattr(w, 'LongDescription') and w.LongDescription:
        obs.obs_property_set_long_description(w.Obj, w.LongDescription)

    # 4. 设置修改回调（根据条件）
    callback_conditions = [
        getattr(w, 'ModifiedIs', False),
        (w.WidgetType == ControlType.GROUP and
         getattr(w, 'Type', None) == obs.OBS_GROUP_CHECKABLE)
    ]

    if any(callback_conditions):
        log_save(obs.LOG_INFO, f"为{w.WidgetType}: 【{w.Description}】添加触发回调")
        obs.obs_property_set_modified_callback(
            w.Obj,
            lambda ps, p, st, name=w.Name: property_modified(name)
        )

        # 分组框的特殊折叠控件回调
        if w.WidgetType == ControlType.GROUP and hasattr(w, 'FoldingObj'):
            obs.obs_property_set_modified_callback(
                w.FoldingObj,
                lambda ps, p, st, name=f"{w.Name}_folding": property_modified(name)
            )

def script_properties():
    """主属性创建函数"""
    log_save(obs.LOG_INFO, "script_properties 被调用")

    # 1. 初始化属性集
    all_widgets = widget.get_sorted_controls().copy()
    props_dict = _init_property_sets(all_widgets)

    # 2. 创建所有控件
    for w in all_widgets:
        _create_control_for_widget(w)

    # 3. 更新界面并返回
    update_ui_interface_data()
    return props_dict["props"]

# 2. 全局处理器注册表（核心）
_control_handler_registry: Dict[ControlType, Callable] = {}

# 3. 自动注册装饰器
def handles(control_type: ControlType):
    """
    装饰器：自动将控件处理函数注册到全局注册表中。
    使用示例：
        @handles(ControlType.CHECKBOX)
        def update_checkbox(widget, settings):
            ...
    """

    def decorator(handler_func: Callable) -> Callable:
        # 检查是否已存在相同类型的处理器
        if control_type in _control_handler_registry:
            existing_handler = _control_handler_registry[control_type].__name__
            raise ValueError(f"控件类型 {control_type} 已由函数 '{existing_handler}' 处理")

        # 注册处理器
        _control_handler_registry[control_type] = handler_func

        # 添加类型验证的包装器
        @wraps(handler_func)
        def wrapper(widget, settings):
            # 可选：在此处添加通用前置/后置处理逻辑
            # 例如：日志记录、性能监控、异常处理等
            return handler_func(widget, settings)

        return wrapper

    return decorator

# 4. 获取处理器的公共接口
def get_handler_for_control(control_type: ControlType) -> Optional[Callable]:
    """
    根据控件类型字符串获取对应的处理函数。
    返回: 处理函数或None（如果未找到对应类型或类型无效）。
    """
    try:
        return _control_handler_registry.get(control_type)
    except ValueError:
        # 控件类型字符串无法映射到已知枚举值
        return None

# ============== 各个控件的处理函数（使用装饰器注册） ==============

def _update_basic_properties(w) -> None:
    """更新控件的基础属性"""
    if obs.obs_property_visible(w.Obj) != w.Visible:
        obs.obs_property_set_visible(w.Obj, w.Visible)
    if obs.obs_property_enabled(w.Obj) != w.Enabled:
        obs.obs_property_set_enabled(w.Obj, w.Enabled)

@handles(ControlType.CHECKBOX)
def _update_checkbox(w, settings) -> None:
    """更新复选框的值"""
    if obs.obs_data_get_bool(settings, w.Name) != w.Bool:
        obs.obs_data_set_bool(settings, w.Name, w.Bool)

@handles(ControlType.DIGITALBOX)
def _update_digitalbox(w, settings) -> None:
    """更新数字框的限值和值"""
    # 检查并更新限值
    if (w.Min != obs.obs_property_int_min(w.Obj)
            or w.Max != obs.obs_property_int_max(w.Obj)
            or w.Step != obs.obs_property_int_step(w.Obj)):
        obs.obs_property_int_set_limits(w.Obj, w.Min, w.Max, w.Step)
    # 检查并更新当前值
    if obs.obs_data_get_int(settings, w.Name) != w.Value:
        obs.obs_data_set_int(settings, w.Name, w.Value)

@handles(ControlType.TEXTBOX)
def _update_textbox(w, settings) -> None:
    """更新文本框的值和属性。"""
    # 1. 如果是信息文本类型(OBS_TEXT_INFO)，则更新其信息类型
    if w.Type == obs.OBS_TEXT_INFO:
        current_info_type = obs.obs_property_text_info_type(w.Obj)
        if current_info_type != w.InfoType:
            obs.obs_property_text_set_info_type(w.Obj, w.InfoType)

    # 2. 更新文本框的字符串内容
    current_text = obs.obs_data_get_string(settings, w.Name)
    if current_text != w.Text:
        obs.obs_data_set_string(settings, w.Name, w.Text)

@handles(ControlType.COMBOBOX)
def _update_combobox(w, settings) -> None:
    """更新组合框的列表项和当前选中的值。"""
    # 1. 获取当前OBS控件中的所有列表项
    current_items = []
    item_count = obs.obs_property_list_item_count(w.Obj)
    for idx in range(item_count):
        current_items.append({
            "label": obs.obs_property_list_item_name(w.Obj, idx),
            "value": obs.obs_property_list_item_string(w.Obj, idx)
        })

    # 2. 如果目标列表与当前列表不同，则重建列表
    if w.DictionaryList != current_items:
        obs.obs_property_list_clear(w.Obj)
        # 首先插入默认选项到第0位
        obs.obs_property_list_insert_string(w.Obj, 0, w.Text, w.Value)
        # 然后添加其他非默认选项
        for item in w.DictionaryList:
            if item["label"] != w.Text:  # 避免默认选项重复
                obs.obs_property_list_add_string(w.Obj, item["label"], item["value"])

    # 3. 根据组合框类型设置当前值
    if w.Type == obs.OBS_COMBO_TYPE_EDITABLE:
        current_value = obs.obs_data_get_string(settings, w.Name)
        # 对于可编辑类型，对比并设置的是显示的文本 (Label)
        target_value = obs.obs_property_list_item_name(w.Obj, 0)  # 默认选项的标签
        if current_value != target_value:
            obs.obs_data_set_string(settings, w.Name, target_value)
    elif w.Type == obs.OBS_COMBO_TYPE_LIST:
        current_value = obs.obs_data_get_string(settings, w.Name)
        # 对于列表类型，对比并设置的是内部值 (Value)
        target_value = obs.obs_property_list_item_string(w.Obj, 0)  # 默认选项的内部值
        if current_value != target_value:
            obs.obs_data_set_string(settings, w.Name, target_value)

@handles(ControlType.PATHBOX)
def _update_pathbox(w, settings) -> None:
    """更新路径选择框的文本值。"""
    current_path = obs.obs_data_get_string(settings, w.Name)
    if current_path != w.Text:
        obs.obs_data_set_string(settings, w.Name, w.Text)

@handles(ControlType.GROUP)
def _update_group(w, settings) -> None:
    """更新分组控件的状态。"""
    # 处理可勾选的分组 (OBS_GROUP_CHECKABLE)
    if w.Type == obs.OBS_GROUP_CHECKABLE:
        current_bool = obs.obs_data_get_bool(settings, w.Name)
        if current_bool != w.Bool:
            obs.obs_data_set_bool(settings, w.Name, w.Bool)

        # 设置控制分组折叠状态的参数（通常用于控制子控件的显隐）
        obs.obs_data_set_bool(settings, f"{w.Name}_folding", w.Bool)
        # 根据分组的可见性，设置其“折叠控制对象”的可见性（通常取反）
        if w.FoldingObj:
            obs.obs_property_set_visible(w.FoldingObj, not w.Visible)

@handles(ControlType.BUTTON)
def _update_button(w, settings) -> None:
    """按钮控件通常没有需要动态更新的状态，此为占位函数。"""
    pass

def update_ui_interface_data() -> bool:
    """
    主更新函数：遍历所有控件并更新其属性和值。
    返回: 始终返回 True。
    """
    # 1. 获取全局数据（假设已定义）
    settings = GlobalVariableOfData.script_settings
    update_dict = GlobalVariableOfData.update_widget_attribute_dict

    # 2. 遍历所有控件
    for w in widget.get_sorted_controls():
        # 2.1 检查控件是否需要更新
        if w.PropsName not in update_dict:
            continue
        if w.Name not in update_dict[w.PropsName]:
            continue

        # 2.2 更新基础属性（可见性、启用状态）
        _update_basic_properties(w)

        # 2.3 获取并调用类型特定的处理器
        handler = get_handler_for_control(w.WidgetType)
        if handler:
            handler(w, settings)  # 解耦调用
        else:
            log_save(obs.LOG_WARNING, f"警告：未找到控件类型 '{w.WidgetType}' 的处理器")

    return True


def script_tick(seconds):
    """
    每帧调用
    这里更改控件属性不会实时显示，
    不要在这里控制控件的【可见】、【可用】、【值】和【名称】
    Args:
        seconds:

    Returns:

    """
    # log_save(obs.LOG_INFO, "script_tick 被调用")
    pass


def script_unload():
    """
    在脚本被卸载时调用。
    """
    log_save(obs.LOG_INFO, "script_unload 被调用")
    obs.obs_frontend_remove_event_callback(trigger_frontend_event)
    log_save(obs.LOG_INFO, GlobalVariableOfData.logRecording)
    pass


class ButtonFunction:
    """按钮回调函数"""

    @staticmethod
    def button_function_top(*args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        log_save(obs.LOG_INFO, f"【{'顶部'}】按钮被触发")
        return True

    @staticmethod
    def button_function_test(*args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        log_save(obs.LOG_INFO, f"【{'测试按钮'}】按钮被触发")
        return True

    @staticmethod
    def button_function_fold_group(*args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        log_save(obs.LOG_INFO, f"【{'折叠分组框'}】按钮被触发")
        folded_group_name: List = []
        """折叠的分组框的名称"""
        for prop_attribute in widget.widget_Group_dict.values():
            for attribute in prop_attribute.values():
                if attribute["Type"] == obs.OBS_GROUP_CHECKABLE:
                    group_bool = obs.obs_data_get_bool(GlobalVariableOfData.script_settings, attribute["Name"])
                    group_folded_bool = obs.obs_data_get_bool(GlobalVariableOfData.script_settings, f'{attribute["Name"]}_folding')
                    if group_bool != group_folded_bool:
                        if attribute["Name"] not in FunctionCache.get_common_widget_groups_visibility():
                            folded_group_name.append(attribute["Name"])

        FunctionCache.get_c_d_m().add_data("setting", "widgetVisibility", json.dumps(folded_group_name, ensure_ascii=False),1)

        FunctionCache.cache_clear()

        # 更新脚本控制台中的控件
        GlobalVariableOfData.update_widget_for_props_dict = {}
        log_save(obs.LOG_INFO, f"更新控件配置信息")
        script_defaults(GlobalVariableOfData.script_settings)
        # 更新脚本用户小部件
        log_save(obs.LOG_INFO, f"更新控件UI")
        update_ui_interface_data()
        GlobalVariableOfData.update_widget_for_props_dict = widget.props_Collection
        return True

    @staticmethod
    def button_function_bottom(*args):
        if len(args) == 2:
            props = args[0]
            prop = args[1]
        if len(args) == 3:
            settings = args[2]
        log_save(obs.LOG_INFO, f"【{'底部'}】按钮被触发")
        return True


# 创建控件表单
widget = Widget()

widget.widget_Button_dict = {
    "props": {
        "top": {
            "Name": "top_button",
            "Description": "Top",
            "Type": obs.OBS_BUTTON_DEFAULT,
            "Callback": ButtonFunction.button_function_top,
            "ModifiedIs": True
        },
        "bottom": {
            "Name": "bottom_button",
            "Description": "Bottom",
            "Type": obs.OBS_BUTTON_DEFAULT,
            "Callback": ButtonFunction.button_function_bottom,
            "ModifiedIs": True
        },
    },
    "test_props": {
        "test": {
            "Name": "test_button",
            "Description": "测试按钮",
            "LongDescription": "长介绍测试",
            "Type": obs.OBS_BUTTON_DEFAULT,
            "Callback": ButtonFunction.button_function_test,
            "ModifiedIs": False
        },
    },
}

widget.widget_Group_dict = {
    "props": {
        "test": {
            "Name": "test_group",
            "Description": "测试",
            "Type": obs.OBS_GROUP_CHECKABLE,
            "GroupPropsName": "test_props",
            "ModifiedIs": True
        },
    },
}

widget.widget_TextBox_dict = {
    "props": {
        "test": {
            "Name": "test_textBox",
            "Description": "测试",
            "Type": obs.OBS_TEXT_INFO,
            "ModifiedIs": True
        },
    },
}

widget.widget_ComboBox_dict = {
    "props": {
        "textTest": {
            "Name": "text_test_comboBox",
            "Description": "文本组合框测试",
            "Type": obs.OBS_COMBO_TYPE_EDITABLE,
            "ModifiedIs": True
        },
    },
    "test_props": {
        "test": {
            "Name": "test_comboBox",
            "Description": "测试",
            "Type": obs.OBS_COMBO_TYPE_LIST,
            "ModifiedIs": True
        },
    },
}

widget.widget_PathBox_dict = {
    "props": {
        "test": {
            "Name": "test_fileDialogBox",
            "Description": "测试",
            "Type": obs.OBS_PATH_FILE,
            "Filter": "图片(*.jpg *.jpeg *.png)",
            "StartPath": "",
            "ModifiedIs": True
        },
    },
}

widget.widget_DigitalBox_dict = {
    "props": {
        "test": {
            "Name": "test_digitalSlider",
            "Description": "测试",
            "Type": "Int",
            "Suffix": "天",
            "ModifiedIs": True
        },
    },
}

widget.widget_CheckBox_dict = {
    "props": {
        "test": {
            "Name": "test_checkBox",
            "Description": "测试",
            "LongDescription": "长介绍测试",
            "ModifiedIs": True
        },
    },
}

widget.widget_list = [
    "top_button",
    "test_group",
    "test_comboBox",
    "text_test_comboBox",
    "test_button",
    "test_checkBox",
    "test_digitalSlider",
    "test_textBox",
    "test_fileDialogBox",
    "bottom_button",
]

widget.preliminary_configuration_control()


if __name__ == "__main__":
    import threading

    setting = {}
    script_defaults(setting)
    script_defaults(setting)
    script_load(setting)
    script_update(setting)
    script_properties()
    script_properties()
    stop_event = threading.Event()
    stop_frontend_event = threading.Event()


    def start_script_tick(seconds):
        while not stop_event.is_set():
            script_tick(seconds)
            time.sleep(1)


    thread_script_tick = threading.Thread(target=start_script_tick, args=[1])
    thread_script_tick.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()  # 设置事件，通知线程停止
        thread_script_tick.join()
        script_unload()
        print(GlobalVariableOfData.logRecording)
    pass
