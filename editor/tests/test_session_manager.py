"""session_manager 单元测试。"""
from pathlib import Path

import pytest

from editor.session_manager import SessionManager


@pytest.fixture
def sm(tmp_path):
    """用临时 ini 文件构造 SessionManager，不污染注册表。"""
    ini = tmp_path / "session.ini"
    return SessionManager(settings_path=str(ini))


@pytest.fixture
def real_files(tmp_path):
    """创建 3 个真实存在的文件用于最近文件测试。"""
    files = []
    for i in range(3):
        f = tmp_path / f"file{i}.csv"
        f.write_text("a,b\n1,2\n", encoding="utf-8")
        files.append(f)
    return files


class TestRecentFiles:

    def test_empty_initial(self, sm):
        assert sm.recent_files() == []

    def test_add_single(self, sm, real_files):
        sm.add_recent_file(str(real_files[0]))
        recent = sm.recent_files()
        assert len(recent) == 1
        assert Path(recent[0]).name == "file0.csv"

    def test_newest_first(self, sm, real_files):
        for f in real_files:
            sm.add_recent_file(str(f))
        recent = sm.recent_files()
        assert [Path(p).name for p in recent] == \
               ["file2.csv", "file1.csv", "file0.csv"]

    def test_dedup(self, sm, real_files):
        sm.add_recent_file(str(real_files[0]))
        sm.add_recent_file(str(real_files[1]))
        sm.add_recent_file(str(real_files[0]))
        recent = sm.recent_files()
        assert len(recent) == 2
        assert Path(recent[0]).name == "file0.csv"

    def test_max_10(self, sm, tmp_path):
        for i in range(15):
            f = tmp_path / f"f{i}.csv"
            f.write_text("x", encoding="utf-8")
            sm.add_recent_file(str(f))
        assert len(sm.recent_files()) == 10

    def test_nonexistent_filtered(self, sm, real_files):
        sm.add_recent_file(str(real_files[0]))
        sm.add_recent_file(str(real_files[1]))
        # 删除一个
        real_files[1].unlink()
        recent = sm.recent_files()
        assert len(recent) == 1
        assert Path(recent[0]).name == "file0.csv"

    def test_clear(self, sm, real_files):
        sm.add_recent_file(str(real_files[0]))
        sm.clear_recent_files()
        assert sm.recent_files() == []


class TestLastDataPath:

    def test_empty_initially(self, sm):
        assert sm.last_data_path() is None

    def test_set_and_get(self, sm, real_files):
        sm.set_last_data_path(str(real_files[0]))
        assert Path(sm.last_data_path()).name == "file0.csv"

    def test_nonexistent_returns_none(self, sm, real_files):
        sm.set_last_data_path(str(real_files[0]))
        real_files[0].unlink()
        assert sm.last_data_path() is None


class TestLastDirectory:

    def test_default_when_unset(self, sm):
        d = sm.last_directory()
        assert Path(d).is_dir()

    def test_set_from_file(self, sm, real_files):
        sm.set_last_directory(str(real_files[0]))
        d = sm.last_directory()
        assert Path(d) == real_files[0].parent

    def test_set_from_directory(self, sm, tmp_path):
        sm.set_last_directory(str(tmp_path))
        assert Path(sm.last_directory()) == tmp_path


class TestSectionExpanded:

    def test_default_true(self, sm):
        assert sm.get_section_expanded("core", True) is True
        assert sm.get_section_expanded("free", True) is True

    def test_set_false(self, sm):
        sm.set_section_expanded("core", False)
        assert sm.get_section_expanded("core") is False

    def test_persists_between_sections(self, sm):
        sm.set_section_expanded("core", False)
        sm.set_section_expanded("free", True)
        assert sm.get_section_expanded("core") is False
        assert sm.get_section_expanded("free") is True


class TestPersistence:

    def test_settings_persist(self, tmp_path, real_files):
        ini = tmp_path / "session.ini"

        sm1 = SessionManager(settings_path=str(ini))
        sm1.add_recent_file(str(real_files[0]))
        sm1.set_section_expanded("core", False)
        sm1.sync()

        sm2 = SessionManager(settings_path=str(ini))
        assert len(sm2.recent_files()) == 1
        assert sm2.get_section_expanded("core") is False