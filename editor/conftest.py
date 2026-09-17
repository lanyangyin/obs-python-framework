"""
pytest 全局配置：
1. 把 obsScriptFramework_ 加入 sys.path，让 editor 能 import ControlTemplateParser
2. 注入 mock 的 obspython，防止间接 import 失败
3. 提供通用的 fixture
"""
import sys
import types
from pathlib import Path

import pytest


# ---------- 1. 路径设置 ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # obs-python-framework/
FRAMEWORK_DIR = PROJECT_ROOT / "obsScriptFramework_"
EDITOR_DIR = Path(__file__).resolve().parent

if str(FRAMEWORK_DIR) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_DIR))
if str(EDITOR_DIR.parent) not in sys.path:
    sys.path.insert(0, str(EDITOR_DIR.parent))


# ---------- 2. mock obspython ----------
def _build_mock_obspython() -> types.ModuleType:
    """obspython 最小 mock，仅在间接 import 时需要。"""
    mod = types.ModuleType("obspython")

    # 文本类型
    mod.OBS_TEXT_DEFAULT = 0
    mod.OBS_TEXT_PASSWORD = 1
    mod.OBS_TEXT_MULTILINE = 2
    mod.OBS_TEXT_INFO = 3
    mod.OBS_TEXT_INFO_NORMAL = 0
    mod.OBS_TEXT_INFO_WARNING = 1
    mod.OBS_TEXT_INFO_ERROR = 2

    # 按钮类型
    mod.OBS_BUTTON_DEFAULT = 0
    mod.OBS_BUTTON_URL = 1

    # 组合框类型
    mod.OBS_COMBO_TYPE_EDITABLE = 0
    mod.OBS_COMBO_TYPE_LIST = 1
    mod.OBS_COMBO_TYPE_RADIO = 2

    # 列表框类型
    mod.OBS_EDITABLE_LIST_TYPE_STRINGS = 0
    mod.OBS_EDITABLE_LIST_TYPE_FILES = 1
    mod.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS = 2

    # 路径框类型
    mod.OBS_PATH_DIRECTORY = 0
    mod.OBS_PATH_FILE_SAVE = 1
    mod.OBS_PATH_FILE = 2

    # 分组框类型
    mod.OBS_GROUP_NORMAL = 0
    mod.OBS_GROUP_CHECKABLE = 1

    # 日志级别
    mod.LOG_ERROR = 0
    mod.LOG_WARNING = 1
    mod.LOG_INFO = 2
    mod.LOG_DEBUG = 3

    mod.script_log = lambda *a, **kw: None
    return mod


if "obspython" not in sys.modules:
    sys.modules["obspython"] = _build_mock_obspython()


# ---------- 3. fixture ----------
@pytest.fixture
def template_path() -> Path:
    """真实的 widgetAttributeDefinitionData.csv 路径。"""
    return FRAMEWORK_DIR / "src" / "data" / "widgetAttributeDefinitionData.csv"


@pytest.fixture
def sample_data_path() -> Path:
    """真实的 widgetData.csv 路径。"""
    return FRAMEWORK_DIR / "plugins" / "widgetData.csv"