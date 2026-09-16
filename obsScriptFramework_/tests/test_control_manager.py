"""ControlManager 单元测试：创建、校验、查询。"""
import pytest

from src.data.obsScriptControlData import (
    WidgetCategory, GroupVariant, DigitalBoxVariant,
)
from src.framework.obsScriptControlDataFramework import ControlManager


@pytest.fixture
def cm() -> ControlManager:
    """每个测试用全新的 ControlManager。"""
    return ControlManager()


# ---------- 基础分组 ----------
class TestBasicGroup:

    def test_basic_group_exists(self, cm):
        basic = cm.get_basic_group()
        assert basic is not None
        assert basic.control_name == "group"
        assert basic.group_props_name == "props"

    def test_basic_group_not_counted(self, cm):
        assert cm.total_widgets == 0
        assert "props" in cm.available_group_props_names


# ---------- 创建控件 ----------
class TestCreateWidget:

    def test_create_checkbox(self, cm):
        w = cm.checkbox.add(
            control_name="cb1", object_name="cb1",
            description="勾选", props_name="props", checked=True,
        )
        assert w.control_name == "cb1"
        assert w.widget_category == WidgetCategory.CHECKBOX
        assert cm.total_widgets == 1

    def test_create_group_then_child(self, cm):
        g = cm.group.add(
            control_name="g1", object_name="g1", description="分组",
            widget_variant=GroupVariant.NORMAL,
            group_props_name="my_props", props_name="props",
        )
        assert g.group_props_name == "my_props"

        child = cm.checkbox.add(
            control_name="cb_in_g1", object_name="cb_in_g1",
            description="子控件", props_name="my_props", checked=False,
        )
        assert child.props_name == "my_props"

    def test_object_name_defaults_to_control_name(self, cm):
        w = cm.checkbox.add(
            control_name="only_name",
            description="X", props_name="props", checked=True,
        )
        assert w.object_name == "only_name"

    def test_load_order_increments(self, cm):
        a = cm.checkbox.add(control_name="a", object_name="a",
                            description="A", props_name="props", checked=True)
        b = cm.checkbox.add(control_name="b", object_name="b",
                            description="B", props_name="props", checked=True)
        assert a.load_order < b.load_order

    def test_digitalbox_variant(self, cm):
        w = cm.digitalbox.add(
            control_name="d", object_name="d", description="数字",
            props_name="props",
            widget_variant=DigitalBoxVariant.INT_SLIDER,
            min_val=0, max_val=100, step=1, digital=50,
        )
        assert w.widget_variant == DigitalBoxVariant.INT_SLIDER


# ---------- 校验 ----------
class TestValidation:

    def test_duplicate_control_name(self, cm):
        cm.checkbox.add(control_name="dup", object_name="dup1",
                        description="A", props_name="props", checked=True)
        with pytest.raises(ValueError, match="control_name 'dup' 已存在"):
            cm.checkbox.add(control_name="dup", object_name="dup2",
                            description="B", props_name="props", checked=True)

    def test_reserved_name_group(self, cm):
        with pytest.raises(ValueError, match="保留名称"):
            cm.checkbox.add(control_name="group", object_name="g",
                            description="X", props_name="props", checked=True)

    def test_invalid_props_name(self, cm):
        with pytest.raises(ValueError, match="props_name 'nonexistent' 无效"):
            cm.checkbox.add(control_name="c", object_name="c",
                            description="X", props_name="nonexistent", checked=True)

    def test_group_props_name_equals_props_name(self, cm):
        with pytest.raises(ValueError, match="不能等于 props_name"):
            cm.group.add(
                control_name="bad_g", object_name="bg", description="X",
                widget_variant=GroupVariant.NORMAL,
                group_props_name="props",  # 与 props_name 相同
                props_name="props",
            )

    def test_duplicate_group_props_name(self, cm):
        cm.group.add(control_name="g1", object_name="g1", description="G1",
                     widget_variant=GroupVariant.NORMAL,
                     group_props_name="my_props", props_name="props")
        with pytest.raises(ValueError, match="group_props_name 'my_props' 已存在"):
            cm.group.add(control_name="g2", object_name="g2", description="G2",
                         widget_variant=GroupVariant.NORMAL,
                         group_props_name="my_props", props_name="props")

    def test_duplicate_object_name_in_same_category(self, cm):
        cm.checkbox.add(control_name="c1", object_name="same",
                        description="A", props_name="props", checked=True)
        with pytest.raises(ValueError, match="object_name 'same' 在分类"):
            cm.checkbox.add(control_name="c2", object_name="same",
                            description="B", props_name="props", checked=True)

    def test_same_object_name_different_category_ok(self, cm):
        """不同分类可以有相同 object_name。"""
        cm.checkbox.add(control_name="cb", object_name="same",
                        description="A", props_name="props", checked=True)
        # 不抛异常
        w = cm.digitalbox.add(control_name="db", object_name="same",
                              description="B", props_name="props",
                              min_val=0, max_val=10, step=1, digital=5)
        assert w.object_name == "same"


# ---------- 查询 ----------
class TestQueries:

    def test_get_widget_by_control_name(self, cm):
        cm.checkbox.add(control_name="cb", object_name="cb",
                        description="X", props_name="props", checked=True)
        w = cm.get_widget_by_control_name("cb")
        assert w is not None
        assert w.control_name == "cb"

    def test_get_widget_by_control_name_basic_group(self, cm):
        w = cm.get_widget_by_control_name("group")
        assert w is not None
        assert w.control_name == "group"

    def test_get_widget_by_control_name_missing(self, cm):
        assert cm.get_widget_by_control_name("no_such") is None

    def test_get_widgets_by_load_order(self, cm):
        cm.checkbox.add(control_name="a", object_name="a",
                        description="A", props_name="props", checked=True)
        cm.checkbox.add(control_name="b", object_name="b",
                        description="B", props_name="props", checked=True)
        widgets = cm.get_widgets_by_load_order()
        assert [w.control_name for w in widgets] == ["a", "b"]

    def test_get_props_mapping(self, cm):
        cm.checkbox.add(control_name="a", object_name="a",
                        description="A", props_name="props", checked=True)
        cm.group.add(control_name="g", object_name="g", description="G",
                     widget_variant=GroupVariant.NORMAL,
                     group_props_name="my_props", props_name="props")
        cm.checkbox.add(control_name="b", object_name="b",
                        description="B", props_name="my_props", checked=True)

        mapping = cm.get_props_mapping()
        assert "props" in mapping
        assert "a" in mapping["props"]
        assert "g" in mapping["props"]
        assert "b" in mapping["my_props"]

    def test_clear_keeps_basic_group(self, cm):
        cm.checkbox.add(control_name="a", object_name="a",
                        description="A", props_name="props", checked=True)
        cm.clear()
        assert cm.total_widgets == 0
        assert cm.get_basic_group() is not None
        assert "props" in cm.available_group_props_names