"""
pytest 全局配置：设置路径 + 调用 _bootstrap 注入 mock obspython。
"""
import sys
from pathlib import Path

# ---------------------------------------------------------------
# 1. 先把项目根目录加入 sys.path，否则下一行 import editor 会失败
# ---------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()
_EDITOR_DIR = _THIS_FILE.parent
_PROJECT_ROOT = _EDITOR_DIR.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------
# 2. 现在可以安全地 import editor 包
# ---------------------------------------------------------------
import pytest

from editor._bootstrap import bootstrap, FRAMEWORK_DIR

bootstrap()


@pytest.fixture
def template_path() -> Path:
    """真实的 widgetAttributeDefinitionData.csv 路径。"""
    return FRAMEWORK_DIR / "src" / "data" / "widgetAttributeDefinitionData.csv"


@pytest.fixture
def sample_data_path() -> Path:
    """真实的 widgetData.csv 路径。"""
    return FRAMEWORK_DIR / "plugins" / "widgetData.csv"