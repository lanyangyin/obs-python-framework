"""
每种控件分类可用的 widget_variant 选项。
优先从 obsScriptFramework_ 的枚举里动态提取，导入失败时回退到硬编码。
"""
from typing import Dict, List


# 硬编码兜底（与 obsScriptControlData.py 保持同步）
_FALLBACK: Dict[str, List[str]] = {
    "CHECKBOX": [],
    "DIGITALBOX": ["INT", "FLOAT", "INT_SLIDER", "FLOAT_SLIDER"],
    "TEXTBOX": ["DEFAULT", "PASSWORD", "MULTILINE", "INFO"],
    "BUTTON": ["DEFAULT", "URL"],
    "COMBOBOX": ["EDITABLE", "LIST"],
    "PATHBOX": ["FILE", "FILE_SAVE", "DIRECTORY"],
    "GROUP": ["NORMAL", "CHECKABLE"],
    "COLORBOX": ["COLOR", "ALPHA"],
    "FONTBOX": [],
    "LISTBOX": ["STRINGS", "FILES", "FILES_AND_URLS"],
}


# category -> 变体枚举类
_VARIANT_CLASS_MAP = {
    "CHECKBOX": "CheckBoxVariant",
    "DIGITALBOX": "DigitalBoxVariant",
    "TEXTBOX": "TextBoxVariant",
    "BUTTON": "ButtonVariant",
    "COMBOBOX": "ComboBoxVariant",
    "PATHBOX": "PathBoxVariant",
    "GROUP": "GroupVariant",
    "COLORBOX": "ColorBoxVariant",
    "FONTBOX": "FontBoxVariant",
    "LISTBOX": "ListBoxVariant",
}


def list_variants_for(category: str) -> List[str]:
    """返回指定 category 可用的 variant 名称列表（不含 None）。"""
    try:
        import src.data.obsScriptControlData as m
    except Exception:
        return list(_FALLBACK.get(category, []))

    cls_name = _VARIANT_CLASS_MAP.get(category)
    if not cls_name:
        return list(_FALLBACK.get(category, []))

    cls = getattr(m, cls_name, None)
    if cls is None:
        return list(_FALLBACK.get(category, []))

    try:
        return [member.name for member in cls]
    except TypeError:
        return []


def default_variant_for(category: str) -> str:
    """返回该分类的默认 variant（第一个），若无则返回空串。"""
    variants = list_variants_for(category)
    return variants[0] if variants else ""