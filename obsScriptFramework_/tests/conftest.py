"""
pytest 全局配置：
1. 把项目根目录加入 sys.path
2. 注入 mock 的 obspython 模块，让 src/plugins 下的模块可以正常 import
3. 提供公共 fixture
"""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------- 1. 路径设置 ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------- 2. mock obspython ----------
def _build_mock_obspython() -> types.ModuleType:
    """构造一个足以让框架模块成功 import 的 obspython mock。"""
    mod = types.ModuleType("obspython")

    # --- 文本类型 ---
    mod.OBS_TEXT_DEFAULT = 0
    mod.OBS_TEXT_PASSWORD = 1
    mod.OBS_TEXT_MULTILINE = 2
    mod.OBS_TEXT_INFO = 3

    mod.OBS_TEXT_INFO_NORMAL = 0
    mod.OBS_TEXT_INFO_WARNING = 1
    mod.OBS_TEXT_INFO_ERROR = 2

    # --- 按钮类型 ---
    mod.OBS_BUTTON_DEFAULT = 0
    mod.OBS_BUTTON_URL = 1

    # --- 组合框类型 ---
    mod.OBS_COMBO_TYPE_EDITABLE = 0
    mod.OBS_COMBO_TYPE_LIST = 1
    mod.OBS_COMBO_TYPE_RADIO = 2

    # --- 列表框类型 ---
    mod.OBS_EDITABLE_LIST_TYPE_STRINGS = 0
    mod.OBS_EDITABLE_LIST_TYPE_FILES = 1
    mod.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS = 2

    # --- 路径框类型 ---
    mod.OBS_PATH_DIRECTORY = 0
    mod.OBS_PATH_FILE_SAVE = 1
    mod.OBS_PATH_FILE = 2

    # --- 分组框类型 ---
    mod.OBS_GROUP_NORMAL = 0
    mod.OBS_GROUP_CHECKABLE = 1

    # --- 日志级别 ---
    mod.LOG_ERROR = 0
    mod.LOG_WARNING = 1
    mod.LOG_INFO = 2
    mod.LOG_DEBUG = 3

    # --- 常用函数：统一返回 None 或 MagicMock ---
    def _noop(*args, **kwargs):
        return None

    mod.script_log = _noop

    # 属性创建函数
    mod.obs_properties_create = lambda: MagicMock(name="obs_properties_t")
    mod.obs_properties_add_bool = lambda *a, **kw: MagicMock(name="prop.bool")
    mod.obs_properties_add_int = lambda *a, **kw: MagicMock(name="prop.int")
    mod.obs_properties_add_int_slider = lambda *a, **kw: MagicMock(name="prop.int_slider")
    mod.obs_properties_add_float = lambda *a, **kw: MagicMock(name="prop.float")
    mod.obs_properties_add_float_slider = lambda *a, **kw: MagicMock(name="prop.float_slider")
    mod.obs_properties_add_text = lambda *a, **kw: MagicMock(name="prop.text")
    mod.obs_properties_add_button = lambda *a, **kw: MagicMock(name="prop.button")
    mod.obs_properties_add_list = lambda *a, **kw: MagicMock(name="prop.list")
    mod.obs_properties_add_path = lambda *a, **kw: MagicMock(name="prop.path")
    mod.obs_properties_add_color = lambda *a, **kw: MagicMock(name="prop.color")
    mod.obs_properties_add_color_alpha = lambda *a, **kw: MagicMock(name="prop.color_alpha")
    mod.obs_properties_add_font = lambda *a, **kw: MagicMock(name="prop.font")
    mod.obs_properties_add_editable_list = lambda *a, **kw: MagicMock(name="prop.editable_list")
    mod.obs_properties_add_group = lambda *a, **kw: MagicMock(name="prop.group")

    # 属性设置函数
    mod.obs_property_set_modified_callback = _noop
    mod.obs_property_set_long_description = _noop
    mod.obs_property_set_visible = _noop
    mod.obs_property_set_enabled = _noop
    mod.obs_property_button_set_type = _noop
    mod.obs_property_button_set_url = _noop
    mod.obs_property_int_set_suffix = _noop
    mod.obs_property_float_set_suffix = _noop
    mod.obs_property_text_set_info_type = _noop
    mod.obs_property_visible = lambda *a, **kw: True
    mod.obs_property_enabled = lambda *a, **kw: True

    # 前端事件
    mod.obs_frontend_add_event_callback = _noop
    mod.obs_frontend_remove_event_callback = _noop

    # 数据读写
    mod.obs_data_get_bool = lambda *a, **kw: False
    mod.obs_data_get_int = lambda *a, **kw: 0
    mod.obs_data_get_double = lambda *a, **kw: 0.0
    mod.obs_data_get_string = lambda *a, **kw: ""
    mod.obs_data_set_bool = _noop
    mod.obs_data_set_int = _noop
    mod.obs_data_set_double = _noop
    mod.obs_data_set_string = _noop
    mod.obs_data_get_obj = lambda *a, **kw: None
    mod.obs_data_set_obj = _noop
    mod.obs_data_release = _noop
    mod.obs_data_get_array = lambda *a, **kw: None
    mod.obs_data_set_array = _noop
    mod.obs_data_array_release = _noop

    # 一些枚举常量（避免某些模块访问时报 AttributeError）
    mod.OBS_FRONTEND_EVENT_SCENE_CHANGED = 2
    mod.OBS_FRONTEND_EVENT_STREAMING_STARTED = 5
    mod.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN = 30

    # --- 属性读取/设置（UIUpdater 用到）---
    mod.obs_property_visible = lambda *a, **kw: True
    mod.obs_property_enabled = lambda *a, **kw: True
    mod.obs_property_set_visible = _noop
    mod.obs_property_set_enabled = _noop

    mod.obs_property_int_min = lambda *a, **kw: 0
    mod.obs_property_int_max = lambda *a, **kw: 100
    mod.obs_property_int_step = lambda *a, **kw: 1
    mod.obs_property_int_set_limits = _noop

    mod.obs_property_float_min = lambda *a, **kw: 0.0
    mod.obs_property_float_max = lambda *a, **kw: 100.0
    mod.obs_property_float_step = lambda *a, **kw: 1.0
    mod.obs_property_float_set_limits = _noop

    mod.obs_property_text_info_type = lambda *a, **kw: 0
    mod.obs_property_text_set_info_type = _noop

    mod.obs_property_list_item_count = lambda *a, **kw: 0
    mod.obs_property_list_item_name = lambda *a, **kw: ""
    mod.obs_property_list_item_string = lambda *a, **kw: ""
    mod.obs_property_list_clear = _noop
    mod.obs_property_list_add_string = _noop
    mod.obs_property_list_insert_string = _noop

    mod.obs_data_array_count = lambda *a, **kw: 0
    mod.obs_data_array_item = lambda *a, **kw: None
    mod.obs_data_array_create = lambda *a, **kw: MagicMock(name="array")
    mod.obs_data_array_push_back = _noop
    mod.obs_data_array_release = _noop

    mod.obs_data_create = lambda *a, **kw: MagicMock(name="data")
    mod.obs_data_get_obj = lambda *a, **kw: None
    mod.obs_data_set_obj = _noop
    mod.obs_data_release = _noop

    return mod


# 必须在任何 src/plugins 模块被导入之前注入
if "obspython" not in sys.modules:
    sys.modules["obspython"] = _build_mock_obspython()


# ---------- 3. 公共 fixture ----------
@pytest.fixture(autouse=True)
def _reset_control_cache():
    yield
    try:
        from plugins.ControlFunction import ControlDataSetFunction
        clear = getattr(ControlDataSetFunction, "clear", None)
        if callable(clear):
            clear()
    except ImportError:
        pass