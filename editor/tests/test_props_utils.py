"""props_utils 单元测试。"""
from editor.model.widget_node import WidgetNode
from editor.model.widget_tree import WidgetTree
from editor.model.props_utils import recompute_props_names


def _make_tree():
    t = WidgetTree()
    g = WidgetNode(
        control_name="g1", widget_category="GROUP",
        props_name="props", group_props_name="g1_props",
    )
    t.add_root(g)
    cb = WidgetNode(control_name="cb1", widget_category="CHECKBOX",
                    props_name="props")
    t.add_child(g, cb)
    return t, g, cb


class TestRecompute:

    def test_root_becomes_basic_props(self):
        t = WidgetTree()
        n = WidgetNode(control_name="n", props_name="wrong")
        t.add_root(n)
        recompute_props_names(t, n)
        assert n.props_name == "props"

    def test_child_of_group_uses_group_props_name(self):
        t, g, cb = _make_tree()
        recompute_props_names(t, cb)
        assert cb.props_name == "g1_props"

    def test_child_of_non_group_inherits_parent_props(self):
        t = WidgetTree()
        parent = WidgetNode(control_name="p", widget_category="CHECKBOX",
                            props_name="props")
        t.add_root(parent)
        child = WidgetNode(control_name="c", props_name="props")
        t.add_child(parent, child)

        recompute_props_names(t, child)
        assert child.props_name == "props"

    def test_nested_groups(self):
        """嵌套分组：内层分组的子控件用自己的 group_props_name。"""
        t = WidgetTree()
        outer = WidgetNode(control_name="outer", widget_category="GROUP",
                           props_name="props", group_props_name="outer_props")
        t.add_root(outer)
        inner = WidgetNode(control_name="inner", widget_category="GROUP",
                           props_name="outer_props",
                           group_props_name="inner_props")
        t.add_child(outer, inner)
        leaf = WidgetNode(control_name="leaf", props_name="outer_props")
        t.add_child(inner, leaf)

        recompute_props_names(t, inner)
        assert inner.props_name == "outer_props"
        assert leaf.props_name == "inner_props"

    def test_recursive_override(self):
        """传入分组时，整棵子树都按位置重算。"""
        t, g, cb = _make_tree()
        cb.props_name = "wrong_value"
        recompute_props_names(t, g)
        assert g.props_name == "props"
        assert cb.props_name == "g1_props"

    def test_missing_group_props_name(self):
        """分组没有 group_props_name 时，子控件继承父的 props_name。"""
        t = WidgetTree()
        g = WidgetNode(control_name="g", widget_category="GROUP",
                       props_name="props", group_props_name=None)
        t.add_root(g)
        child = WidgetNode(control_name="c", props_name="props")
        t.add_child(g, child)

        recompute_props_names(t, child)
        assert child.props_name == "props"