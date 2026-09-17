"""WidgetNode 单测。"""
from editor.model.widget_node import WidgetNode


class TestConstruction:

    def test_defaults(self):
        n = WidgetNode()
        assert n.control_name == ""
        assert n.children == []
        assert n.parent is None
        assert n.level == 0

    def test_from_parsed_dict_checkbox(self):
        d = {
            "object_name": "cb1",
            "level": 0,
            "widget_category": "CHECKBOX",
            "props_name": "props",
            "group_props_name": None,
            "properties": {"control_name": "cb1"},
            "group_properties": {
                "group_1": {"object_name": "cb1", "description": "勾选框",
                            "long_description": "测试用", "widget_variant": None,
                            "modified_callback_enabled": True,
                            "modified_callback": "test_callback"},
                "group_3": {"visible": "default_true", "enabled": "default_true"},
                "group_4": {"checked": "checked_reference_data"},
            },
            "source_line": 2,
        }
        n = WidgetNode.from_parsed_dict(d)
        assert n.control_name == "cb1"
        assert n.widget_category == "CHECKBOX"
        assert n.object_name == "cb1"
        assert n.description == "勾选框"
        assert n.modified_callback_enabled is True
        assert n.modified_callback == "test_callback"
        assert n.source_line == 2
        # 自由属性应在 properties 里
        assert n.properties.get("visible") == "default_true"
        assert n.properties.get("checked") == "checked_reference_data"


class TestTreeOps:

    def test_add_child_updates_levels(self):
        p = WidgetNode(control_name="p")
        c = WidgetNode(control_name="c")
        g = WidgetNode(control_name="g")
        p.add_child(c)
        c.add_child(g)
        assert p.level == 0
        assert c.level == 1
        assert g.level == 2

    def test_add_child_reparents(self):
        p1 = WidgetNode(control_name="p1")
        p2 = WidgetNode(control_name="p2")
        c = WidgetNode(control_name="c")
        p1.add_child(c)
        assert c.parent is p1
        p2.add_child(c)
        assert c.parent is p2
        assert c not in p1.children
        assert c in p2.children

    def test_remove_child(self):
        p = WidgetNode(control_name="p")
        c = WidgetNode(control_name="c")
        p.add_child(c)
        p.remove_child(c)
        assert c.parent is None
        assert c not in p.children

    def test_iter_subtree(self):
        p = WidgetNode(control_name="p")
        c1 = WidgetNode(control_name="c1")
        c2 = WidgetNode(control_name="c2")
        p.add_child(c1)
        p.add_child(c2)
        names = [n.control_name for n in p.iter_subtree()]
        assert names == ["p", "c1", "c2"]

    def test_to_dict_round_trip(self):
        p = WidgetNode(control_name="p", description="parent")
        c = WidgetNode(control_name="c", description="child")
        p.add_child(c)
        d = p.to_dict()
        assert d["control_name"] == "p"
        assert len(d["children"]) == 1
        assert d["children"][0]["control_name"] == "c"