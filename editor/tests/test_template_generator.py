"""template_generator 单元测试。"""
from editor.model.widget_node import WidgetNode
from editor.model.widget_tree import WidgetTree
from editor.model.template_generator import (
    collect_function_names,
    generate_all,
    generate_button_function,
    generate_control_function,
    summarize,
    _looks_like_func_name,
)


def _make_tree():
    t = WidgetTree()
    cb = WidgetNode(
        control_name="cb1", widget_category="CHECKBOX",
        props_name="props",
        modified_callback_enabled=True,
        modified_callback="my_cb",
    )
    cb.properties["checked"] = "checked_reference_data"
    t.add_root(cb)

    btn = WidgetNode(control_name="btn1", widget_category="BUTTON",
                     props_name="props")
    btn.properties["click_callback"] = "my_button_handler"
    t.add_root(btn)
    return t


class TestCollect:

    def test_button_callback_collected(self):
        t = _make_tree()
        buttons, controls = collect_function_names(t)
        assert "my_button_handler" in buttons

    def test_modified_callback_collected(self):
        t = _make_tree()
        buttons, controls = collect_function_names(t)
        assert "my_cb" in controls

    def test_free_property_function_collected(self):
        t = _make_tree()
        buttons, controls = collect_function_names(t)
        assert "checked_reference_data" in controls

    def test_disabled_modified_callback_ignored(self):
        t = WidgetTree()
        n = WidgetNode(control_name="x", modified_callback_enabled=False,
                       modified_callback="should_not_appear")
        t.add_root(n)
        _, controls = collect_function_names(t)
        assert "should_not_appear" not in controls


class TestLooksLikeFuncName:

    def test_valid(self):
        assert _looks_like_func_name("default_true")
        assert _looks_like_func_name("my_func_1")

    def test_invalid(self):
        assert not _looks_like_func_name(None)
        assert not _looks_like_func_name("")
        assert not _looks_like_func_name("123abc")
        assert not _looks_like_func_name("has space")
        assert not _looks_like_func_name(123)

    def test_x_prefix_rejected(self):
        # CSV 里 X 表示"此列不适用"，不是函数名
        assert not _looks_like_func_name("X")


class TestGenerate:

    def test_generate_all_returns_three_files(self):
        t = _make_tree()
        files = generate_all(t)
        assert "plugins/ButtonFunction.py" in files
        assert "plugins/ControlFunction.py" in files
        assert "plugins/GlobalVariable.py" in files

    def test_generated_button_compiles(self):
        t = _make_tree()
        code = generate_button_function({"my_handler"})
        compile(code, "<test>", "exec")

    def test_generated_control_compiles(self):
        t = _make_tree()
        code = generate_control_function({"my_cb"})
        compile(code, "<test>", "exec")

    def test_button_function_contains_method(self):
        code = generate_button_function({"click_a", "click_b"})
        assert "def click_a(" in code
        assert "def click_b(" in code

    def test_control_function_contains_default_true(self):
        code = generate_control_function(set())
        assert "def default_true" in code
        assert "def default_false" in code

    def test_empty_button_set_produces_valid_class(self):
        code = generate_button_function(set())
        compile(code, "<test>", "exec")
        assert "class BtnFunction" in code

    def test_empty_control_set_produces_valid_class(self):
        code = generate_control_function(set())
        compile(code, "<test>", "exec")
        assert "class ControlDataSetFunction" in code


class TestSummary:

    def test_summary_counts(self):
        t = _make_tree()
        s = summarize(t)
        assert s["button_callbacks"] == 1
        assert s["control_callbacks"] >= 2  # my_cb + checked_reference_data
        assert s["total_nodes"] == 2