"""CommonDataManager 单元测试：增删改查、持久化、旧格式转换。"""
import json

import pytest

from src.tool.CommonDataManager import CommonDataManager


@pytest.fixture
def mgr(tmp_path) -> CommonDataManager:
    return CommonDataManager(str(tmp_path / "data.json"))


class TestAddGet:

    def test_add_and_get(self, mgr):
        mgr.add_data("u1", "title", "t1")
        assert mgr.get_data("u1", "title") == ["t1"]

    def test_add_dedup_moves_front(self, mgr):
        mgr.add_data("u1", "title", "t1")
        mgr.add_data("u1", "title", "t2")
        mgr.add_data("u1", "title", "t1")  # 再次添加 t1，应移到最前
        assert mgr.get_data("u1", "title") == ["t1", "t2"]

    def test_add_respects_maximum(self, mgr):
        for i in range(6):
            mgr.add_data("u1", "title", f"t{i}", maximum=3)
        assert mgr.get_data("u1", "title") == ["t5", "t4", "t3"]

    def test_get_nonexistent_returns_empty(self, mgr):
        assert mgr.get_data("no_such", "title") == []
        assert mgr.get_data("u1", "no_such") == []


class TestRemoveUpdate:

    def test_remove(self, mgr):
        mgr.add_data("u1", "title", "t1")
        assert mgr.remove_data("u1", "title", "t1") is True
        assert mgr.get_data("u1", "title") == []

    def test_remove_nonexistent(self, mgr):
        assert mgr.remove_data("u1", "title", "t1") is False

    def test_update(self, mgr):
        mgr.add_data("u1", "title", "old")
        assert mgr.update_data("u1", "title", "old", "new") is True
        assert mgr.get_data("u1", "title") == ["new"]

    def test_update_nonexistent(self, mgr):
        assert mgr.update_data("u1", "title", "old", "new") is False


class TestClearAndQuery:

    def test_clear_specific_type(self, mgr):
        mgr.add_data("u1", "title", "t1")
        mgr.add_data("u1", "tag", "tag1")
        mgr.clear_user_data("u1", "title")
        assert mgr.get_data("u1", "title") == []
        assert mgr.get_data("u1", "tag") == ["tag1"]

    def test_clear_all(self, mgr):
        mgr.add_data("u1", "title", "t1")
        mgr.add_data("u1", "tag", "tag1")
        mgr.clear_user_data("u1")
        assert mgr.get_user_data_types("u1") == []

    def test_get_all_users(self, mgr):
        mgr.add_data("u1", "title", "t1")
        mgr.add_data("u2", "title", "t2")
        assert sorted(mgr.get_all_users()) == ["u1", "u2"]

    def test_get_user_data_types(self, mgr):
        mgr.add_data("u1", "title", "t1")
        mgr.add_data("u1", "tag", "tag1")
        assert sorted(mgr.get_user_data_types("u1")) == ["tag", "title"]

    def test_get_all_data(self, mgr):
        mgr.add_data("u1", "title", "t1")
        assert mgr.get_all_data() == {"u1": {"title": ["t1"]}}


class TestPersistence:

    def test_data_persisted(self, tmp_path):
        path = tmp_path / "data.json"
        mgr1 = CommonDataManager(str(path))
        mgr1.add_data("u1", "title", "t1")

        mgr2 = CommonDataManager(str(path))
        assert mgr2.get_data("u1", "title") == ["t1"]

    def test_old_format_conversion(self, tmp_path):
        """旧格式：{user_id: [items]}，应自动转为新格式。"""
        path = tmp_path / "old.json"
        path.write_text(json.dumps({"u1": ["t1", "t2"]}), encoding="utf-8")

        mgr = CommonDataManager(str(path), default_data_type="title")
        assert mgr.get_data("u1", "title") == ["t1", "t2"]