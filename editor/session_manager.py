"""
会话状态管理：最近文件、上次目录、上次打开的路径。
用 QSettings 存储，系统会放到合适的位置（注册表 / plist / ini）。

和 editor_settings.json 的分工：
- editor_settings.json：用户偏好（主题、字体）
- QSettings：会话状态（最近文件、上次路径）
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QSettings


_ORG = "obsScriptFramework"
_APP = "Editor"
_MAX_RECENT = 10

_KEY_RECENT = "recent/data_files"
_KEY_LAST_DATA = "session/last_data_path"
_KEY_LAST_DIR = "session/last_directory"
_KEY_SECTION_EXPANDED = "session/section_expanded"


class SessionManager:
    def __init__(self, settings_path: Optional[str] = None):
        """
        :param settings_path: 可选，指定一个 ini 文件路径。
                              用于测试或需要在指定位置存储场景。
                              不传则用系统默认位置（注册表 / plist / ini）。
        """
        if settings_path:
            self._s = QSettings(settings_path, QSettings.IniFormat)
        else:
            self._s = QSettings(_ORG, _APP)

    # ------------------------------------------------------------------
    # 最近文件
    # ------------------------------------------------------------------
    def recent_files(self) -> List[str]:
        """返回最近打开的文件列表（最新在前），过滤掉已不存在的路径。"""
        raw = self._s.value(_KEY_RECENT, [])
        if raw is None:
            return []
        if isinstance(raw, str):
            items = [raw]
        else:
            items = list(raw)

        # 过滤已删除的文件
        existing = [p for p in items if p and Path(p).exists()]

        # 如果过滤掉了，写回
        if len(existing) != len(items):
            self._s.setValue(_KEY_RECENT, existing)

        return existing

    def add_recent_file(self, path: str) -> None:
        """把文件推到最近列表头部，去重，限制长度。"""
        path = str(Path(path).resolve())
        items = self.recent_files()
        if path in items:
            items.remove(path)
        items.insert(0, path)
        if len(items) > _MAX_RECENT:
            items = items[:_MAX_RECENT]
        self._s.setValue(_KEY_RECENT, items)

    def clear_recent_files(self) -> None:
        self._s.remove(_KEY_RECENT)

    # ------------------------------------------------------------------
    # 上次打开的路径
    # ------------------------------------------------------------------
    def last_data_path(self) -> Optional[str]:
        v = self._s.value(_KEY_LAST_DATA, "")
        return v if v and Path(v).exists() else None

    def set_last_data_path(self, path: str) -> None:
        self._s.setValue(_KEY_LAST_DATA, str(Path(path).resolve()))

    # ------------------------------------------------------------------
    # 上次操作的目录（用于文件对话框的默认位置）
    # ------------------------------------------------------------------
    def last_directory(self) -> str:
        v = self._s.value(_KEY_LAST_DIR, "")
        if v and Path(v).is_dir():
            return v
        from ._bootstrap import get_project_root
        return str(get_project_root())

    def set_last_directory(self, path: str) -> None:
        p = Path(path)
        if p.is_file():
            p = p.parent
        if p.is_dir():
            self._s.setValue(_KEY_LAST_DIR, str(p))

    # ------------------------------------------------------------------
    # 属性面板分组折叠状态
    # ------------------------------------------------------------------
    def get_section_expanded(self, key: str, default: bool = True) -> bool:
        data = self._s.value(_KEY_SECTION_EXPANDED, {}) or {}
        if not isinstance(data, dict):
            return default
        return bool(data.get(key, default))

    def set_section_expanded(self, key: str, value: bool) -> None:
        data = self._s.value(_KEY_SECTION_EXPANDED, {}) or {}
        if not isinstance(data, dict):
            data = {}
        data[key] = bool(value)
        self._s.setValue(_KEY_SECTION_EXPANDED, data)

    # ------------------------------------------------------------------
    # 同步
    # ------------------------------------------------------------------
    def sync(self) -> None:
        self._s.sync()