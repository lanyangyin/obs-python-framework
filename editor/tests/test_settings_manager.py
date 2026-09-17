"""settings_manager 单元测试。"""
import json
from pathlib import Path

import pytest

from editor import settings_manager
from editor.settings_manager import (
    EditorSettings, LIGHT_PRESET, DARK_PRESET,
    preset, load_settings, save_settings,
)


@pytest.fixture
def tmp_settings_file(tmp_path, monkeypatch):
    """把 _SETTINGS_FILE 指到临时路径。"""
    path = tmp_path / "editor_settings.json"
    monkeypatch.setattr(settings_manager, "_SETTINGS_FILE", path)
    return path


class TestPresets:

    def test_light_preset(self):
        s = preset("light")
        assert s.theme == "light"
        assert s.foreground == LIGHT_PRESET["foreground"]

    def test_dark_preset(self):
        s = preset("dark")
        assert s.theme == "dark"
        assert s.foreground == DARK_PRESET["foreground"]

    def test_unknown_falls_back_to_light(self):
        s = preset("whatever")
        assert s.theme == "light"


class TestLoadSave:

    def test_load_missing_returns_default(self, tmp_settings_file):
        s = load_settings()
        assert s.theme == "light"

    def test_save_then_load(self, tmp_settings_file):
        original = EditorSettings(theme="dark", font_size=16,
                                  foreground="#111111")
        save_settings(original)

        loaded = load_settings()
        assert loaded.theme == "dark"
        assert loaded.font_size == 16
        assert loaded.foreground == "#111111"

    def test_unknown_fields_ignored(self, tmp_settings_file):
        tmp_settings_file.write_text(
            json.dumps({"theme": "dark", "unknown_field": 42}),
            encoding="utf-8",
        )
        s = load_settings()
        assert s.theme == "dark"

    def test_corrupt_json_falls_back(self, tmp_settings_file):
        tmp_settings_file.write_text("this is not json {{{", encoding="utf-8")
        s = load_settings()
        assert s.theme == "light"

    def test_empty_file_falls_back(self, tmp_settings_file):
        tmp_settings_file.write_text("", encoding="utf-8")
        s = load_settings()
        assert s.theme == "light"


class TestFileLocation:

    def test_get_settings_file_path(self, tmp_settings_file):
        assert settings_manager.get_settings_file_path() == tmp_settings_file