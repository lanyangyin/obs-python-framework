"""validator 单测。"""
from editor.model.widget_node import WidgetNode
from editor.model.widget_tree import WidgetTree
from editor.model.validator import validate, has_errors, ValidationError


def _make_tree() -> WidgetTree:
    t = WidgetTree()
    g = WidgetNode(control_name="g1", widget_category="GROUP",
                   props_name="props", group_props_name="g1_props")
    t.add_root(g)
    cb = WidgetNode(control_name="cb1", widget_category="CHECKBOX",
                    props_name="g1_props")
    t.add_child(g, cb)
    return t


class TestCleanTree:

    def test_no_errors(self):
        t = _make_tree()
        errors = validate(t)
        assert errors == []


class TestControlName:

    def test_reserved_name(self):
        t = WidgetTree()
        t.add_root(WidgetNode(control_name="group", props_name="props"))
        errors = validate(t)
        assert any(e.field == "control_name" and "保留" in e.message for e in errors)

    def test_empty_control_name(self):
        t = WidgetTree()
        # 绕过 add_root 的校验直接往 _roots 里塞
        t._roots.append(WidgetNode(control_name="", source_line=5))
        errors = validate(t)
        assert any(e.field == "control_name" for e in errors)


class TestGroupPropsName:

    def test_missing_group_props_name(self):
        t = WidgetTree()
        g = WidgetNode(control_name="g", widget_category="GROUP",
                       props_name="props", group_props_name=None)
        # 绕过 register 校验
        t._index["g"] = g
        t._roots.append(g)
        errors = validate(t)
        assert any(e.field == "group_props_name" and "缺少" in e.message for e in errors)

    def test_group_props_equals_props(self):
        t = WidgetTree()
        g = WidgetNode(control_name="g", widget_category="GROUP",
                       props_name="props", group_props_name="props")
        t._index["g"] = g
        t._roots.append(g)
        errors = validate(t)
        assert any("不能等于" in e.message for e in errors)


class TestPropsName:

    def test_invalid_props_name(self):
        t = WidgetTree()
        n = WidgetNode(control_name="c", props_name="nonexistent")
        t._index["c"] = n
        t._roots.append(n)
        errors = validate(t)
        assert any(e.field == "props_name" for e in errors)


class TestWarnings:

    def test_orphan_group_props_name_warning(self):
        t = WidgetTree()
        g = WidgetNode(control_name="g", widget_category="GROUP",
                       props_name="props", group_props_name="orphan_props")
        t.add_root(g)
        errors = validate(t)
        warnings = [e for e in errors if e.severity == "warning"]
        assert any("未被任何子控件使用" in e.message for e in warnings)

    def test_unsupported_field_warning(self):
        t = WidgetTree()
        n = WidgetNode(
            control_name="c", widget_category="GROUP",
            props_name="props", group_props_name="g_props",
            widget_variant="NORMAL",
        )
        n.properties["checked"] = "some_func"
        t.add_root(n)
        errors = validate(t)
        warnings = [e for e in errors if e.severity == "warning"]
        assert any("不支持属性 'checked'" in e.message for e in warnings)


class TestHelpers:

    def test_has_errors(self):
        assert has_errors([ValidationError("a", "f", "msg", "error")]) is True
        assert has_errors([ValidationError("a", "f", "msg", "warning")]) is False
        assert has_errors([]) is False