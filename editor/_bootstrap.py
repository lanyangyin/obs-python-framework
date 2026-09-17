# editor/_bootstrap.py
"""
编辑器启动引导：路径设置 + mock obspython。

main.py（GUI 入口）和 conftest.py（pytest）都调用 bootstrap()。
"""
import sys
import types
from pathlib import Path

EDITOR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EDITOR_DIR.parent
FRAMEWORK_DIR = PROJECT_ROOT / "obsScriptFramework_"


def setup_paths() -> None:
    """把项目根目录和框架目录加入 sys.path。"""
    for p in (PROJECT_ROOT, FRAMEWORK_DIR):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def install_mock_obspython() -> None:
    """在没有 OBS 运行时时，注入 mock obspython。"""
    if "obspython" in sys.modules:
        return
    mod = types.ModuleType("obspython")

    mod.OBS_TEXT_DEFAULT = 0
    mod.OBS_TEXT_PASSWORD = 1
    mod.OBS_TEXT_MULTILINE = 2
    mod.OBS_TEXT_INFO = 3
    mod.OBS_TEXT_INFO_NORMAL = 0
    mod.OBS_TEXT_INFO_WARNING = 1
    mod.OBS_TEXT_INFO_ERROR = 2

    mod.OBS_BUTTON_DEFAULT = 0
    mod.OBS_BUTTON_URL = 1

    mod.OBS_COMBO_TYPE_EDITABLE = 0
    mod.OBS_COMBO_TYPE_LIST = 1
    mod.OBS_COMBO_TYPE_RADIO = 2

    mod.OBS_EDITABLE_LIST_TYPE_STRINGS = 0
    mod.OBS_EDITABLE_LIST_TYPE_FILES = 1
    mod.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS = 2

    mod.OBS_PATH_DIRECTORY = 0
    mod.OBS_PATH_FILE_SAVE = 1
    mod.OBS_PATH_FILE = 2

    mod.OBS_GROUP_NORMAL = 0
    mod.OBS_GROUP_CHECKABLE = 1

    mod.LOG_ERROR = 0
    mod.LOG_WARNING = 1
    mod.LOG_INFO = 2
    mod.LOG_DEBUG = 3

    mod.script_log = lambda *a, **kw: None
    sys.modules["obspython"] = mod


def bootstrap() -> None:
    setup_paths()
    install_mock_obspython()