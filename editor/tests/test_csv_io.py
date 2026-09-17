"""csv_io 单测：用真实 CSV 做往返测试。"""
import shutil
from pathlib import Path

import pytest

from editor.model.csv_io import load_tree, save_tree, read_header


class TestLoad:

    def test_load_real_data(self, template_path, sample_data_path):
        tree = load_tree(str(template_path), str(sample_data_path))
        assert len(tree) > 0
        # 至少有 test_checkBox
        cb = tree.find("test_checkBox")
        assert cb is not None
        assert cb.widget_category == "CHECKBOX"

    def test_group_hierarchy(self, template_path, sample_data_path):
        tree = load_tree(str(template_path), str(sample_data_path))
        g = tree.find("test_group")
        assert g is not None
        assert g.is_group
        assert g.group_props_name == "group_props"
        # 应至少有子控件
        assert len(g.children) > 0
        for c in g.children:
            assert c.props_name == "group_props"

    def test_levels(self, template_path, sample_data_path):
        tree = load_tree(str(template_path), str(sample_data_path))
        for node in tree.iter_all():
            if node.parent is None:
                assert node.level == 0
            else:
                assert node.level == node.parent.level + 1


class TestSave:

    def test_round_trip(self, template_path, sample_data_path, tmp_path):
        """加载 -> 保存 -> 再加载，节点数量与结构应一致。"""
        tree1 = load_tree(str(template_path), str(sample_data_path))
        out_path = tmp_path / "out.csv"
        save_tree(tree1, str(template_path), str(out_path))

        tree2 = load_tree(str(template_path), str(out_path))

        names1 = [n.control_name for n in tree1.iter_all()]
        names2 = [n.control_name for n in tree2.iter_all()]
        assert names1 == names2

        # 抽查关键字段
        for name in names1:
            n1 = tree1.find(name)
            n2 = tree2.find(name)
            assert n1.widget_category == n2.widget_category
            assert n1.object_name == n2.object_name
            assert n1.props_name == n2.props_name
            assert n1.description == n2.description

    def test_level_preserved_via_arrows(self, template_path, sample_data_path, tmp_path):
        """保存后的 CSV 里，子控件 object_name 应带 → 前缀。"""
        tree = load_tree(str(template_path), str(sample_data_path))
        out_path = tmp_path / "out.csv"
        save_tree(tree, str(template_path), str(out_path))

        with open(out_path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
        # 至少出现一次 → 前缀
        assert "→" in content


class TestHeader:

    def test_read_header(self, template_path):
        header = read_header(str(template_path))
        assert "control_name" in header
        assert "widget_category" in header
        assert "|" in header
        assert "||" in header