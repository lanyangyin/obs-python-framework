"""WidgetTree 单测。"""
import pytest

from editor.model.widget_node import WidgetNode
from editor.model.widget_tree import WidgetTree


@pytest.fixture
def tree() -> WidgetTree:
    t = WidgetTree()
    g = WidgetNode(control_name="g1", widget_category="GROUP",
                   props_name="props", group_props_name="g1_props")
    cb = WidgetNode(control_name="cb1", widget_category="CHECKBOX",
                    props_name="g1_props")
    t.add_root(g)
    t.add_child(g, cb)
    return t


class TestAddRemove:

    def test_add_root(self):
        t = WidgetTree()
        n = WidgetNode(control_name="a")
        t.add_root(n)
        assert len(t) == 1
        assert "a" in t

    def test_add_child(self, tree):
        assert len(tree) == 2
        assert tree.find("g1") is not None
        assert tree.find("cb1") is not None

    def test_remove_subtree(self, tree):
        tree.remove(tree.find("g1"))
        assert len(tree) == 0
        assert "g1" not in tree
        assert "cb1" not in tree

    def test_duplicate_control_name_raises(self, tree):
        with pytest.raises(ValueError, match="control_name 'cb1' 已存在"):
            tree.add_root(WidgetNode(control_name="cb1"))

    def test_duplicate_group_props_name_raises(self, tree):
        with pytest.raises(ValueError, match="group_props_name 'g1_props' 已被"):
            tree.add_root(WidgetNode(
                control_name="g2", widget_category="GROUP",
                props_name="props", group_props_name="g1_props",
            ))

    def test_remove_frees_group_props_name(self, tree):
        tree.remove(tree.find("g1"))
        # 移除后 g1_props 应可重新使用
        t2 = WidgetTree()
        t2.add_root(WidgetNode(
            control_name="new_g", widget_category="GROUP",
            props_name="props", group_props_name="g1_props",
        ))
        assert "g1_props" in t2.group_props_names()


class TestMove:

    def test_move_to_new_parent(self, tree):
        g2 = WidgetNode(control_name="g2", widget_category="GROUP",
                        props_name="props", group_props_name="g2_props")
        tree.add_root(g2)
        cb = tree.find("cb1")
        tree.move(cb, g2)
        assert cb.parent is g2
        assert g2.children == [cb]

    def test_move_to_root(self, tree):
        cb = tree.find("cb1")
        tree.move(cb, None)
        assert cb.parent is None
        assert cb in tree.roots()

    def test_move_to_own_subtree_raises(self, tree):
        g = tree.find("g1")
        with pytest.raises(ValueError, match="不能把节点"):
            tree.move(g, tree.find("cb1"))


class TestIteration:

    def test_iter_all_depth_first(self, tree):
        names = [n.control_name for n in tree.iter_all()]
        assert names == ["g1", "cb1"]

    def test_iter_breadth_first(self, tree):
        names = [n.control_name for n in tree.iter_breadth_first()]
        assert names == ["g1", "cb1"]

    def test_group_props_names_includes_basic(self, tree):
        assert "props" in tree.group_props_names()
        assert "g1_props" in tree.group_props_names()