"""
编辑器用户设置：主题、字体、颜色。持久化到 JSON。
"""
import json
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Any, Dict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SETTINGS_FILE = _PROJECT_ROOT / "editor_settings.json"


# ----------------------------------------------------------------------
# 数据模型
# ----------------------------------------------------------------------
@dataclass
class EditorSettings:
    theme: str = "light"           # "light" / "dark" / "custom"

    font_family: str = ""          # 空串 = 系统默认
    font_size: int = 0             # 0 = 系统默认

    # 全局
    foreground: str = "#1e1e1e"
    background: str = "#f0f0f0"
    accent: str = "#3a7ebf"

    # 输入控件（QLineEdit / QComboBox / QSpinBox）
    input_background: str = "#ffffff"
    input_foreground: str = "#1e1e1e"

    # 树
    tree_background: str = "#ffffff"
    tree_foreground: str = "#1e1e1e"

    # 属性面板
    property_background: str = "#fafafa"
    property_foreground: str = "#1e1e1e"

    # 标签文字（属性面板左侧列）
    label_foreground: str = "#555555"

    # 预览面板中控件标签（description）的文字颜色
    preview_label_color: str = "#888888"


LIGHT_PRESET: Dict[str, Any] = {
    "theme": "light",
    "font_family": "",
    "font_size": 0,
    "foreground": "#1e1e1e",
    "background": "#f0f0f0",
    "accent": "#3a7ebf",
    "input_background": "#ffffff",
    "input_foreground": "#1e1e1e",
    "tree_background": "#ffffff",
    "tree_foreground": "#1e1e1e",
    "property_background": "#fafafa",
    "property_foreground": "#1e1e1e",
    "label_foreground": "#555555",
    "preview_label_color": "#888888",
}

DARK_PRESET: Dict[str, Any] = {
    "theme": "dark",
    "font_family": "",
    "font_size": 0,
    "foreground": "#e0e0e0",
    "background": "#2b2b2b",
    "accent": "#5a9bd4",
    "input_background": "#3c3f41",
    "input_foreground": "#e0e0e0",
    "tree_background": "#2b2b2b",
    "tree_foreground": "#e0e0e0",
    "property_background": "#2b2b2b",
    "property_foreground": "#e0e0e0",
    "label_foreground": "#a0a0a0",
    "preview_label_color": "#a0a0a0",
}


def preset(name: str) -> EditorSettings:
    """按名称返回预设。未知名称回退到 light。"""
    if name == "dark":
        return EditorSettings(**DARK_PRESET)
    return EditorSettings(**LIGHT_PRESET)


# ----------------------------------------------------------------------
# 读写
# ----------------------------------------------------------------------
def load_settings() -> EditorSettings:
    if not _SETTINGS_FILE.exists():
        return preset("light")
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return preset("light")

    # 过滤未知字段，保证向前兼容
    valid_keys = {f.name for f in fields(EditorSettings)}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    try:
        return EditorSettings(**filtered)
    except TypeError:
        return preset("light")


def save_settings(settings: EditorSettings) -> None:
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_settings_file_path() -> Path:
    return _SETTINGS_FILE