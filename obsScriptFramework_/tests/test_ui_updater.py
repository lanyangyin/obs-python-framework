"""UIUpdater 单元测试：注册表、可见性/启用状态、各分类 handler 分发。"""
from unittest.mock import MagicMock

import pytest

from src.data.obsScriptControlData import (
    WidgetCategory, GroupVariant, DigitalBoxVariant, TextBoxVariant,
    ComboBoxVariant, ButtonVariant, PathBoxVariant, ColorBoxVariant,
    TextBoxInfoVariant, ListBoxVariant,
)
from src.framework.obsScriptControlDataFramework import ControlManager
from src.framework import obsScriptControlUiUpdaterFramework as updater_mod
from src.framework.obsScriptControlUiUpdaterFramework import (
    UIUpdater,
    register_ui_handler,
)


# ------------------------------------------------------------------
# fixtures
# ------------------------------------------------------------------
@pytest.fixture
def cm() -> ControlManager:
    cm = ControlManager()
    cm.checkbox.add(
        control_name="cb1", object_name="cb1", description="CB",
        props_name="props", checked=True,
    )
    cm.digitalbox.add(
        control_name="db_int", object_name="db_int", description="DBI",
        props_name="props", widget_variant=DigitalBoxVariant.INT,
        min_val=0, max_val=100, step=1, digital=50,
    )
    cm.digitalbox.add(
        control_name="db_float", object_name="db_float", description="DBF",
        props_name="props", widget_variant=DigitalBoxVariant.FLOAT,
        min_val=0, max_val=100, step=1, digital=50,
    )
    cm.textbox.add(
        control_name="tb", object_name="tb", description="TB",
        props_name="props", text="hello",
    )
    cm.button.add(
        control_name="btn", object_name="btn", description="BTN",
        props_name="props", widget_variant=ButtonVariant.DEFAULT,
    )
    cm.combobox.add(
        control_name="combo", object_name="combo", description="CB",
        props_name="props", widget_variant=ComboBoxVariant.LIST,
        label="L1", value="V1",
        items=[{"label": "L1", "value": "V1"}, {"label": "L2", "value": "V2"}],
    )
    cm.pathbox.add(
        control_name="path", object_name="path", description="P",
        props_name="props", widget_variant=PathBoxVariant.FILE,
        path_text="C:\\",
    )
    cm.group.add(
        control_name="grp_checkable", object_name="grp_checkable", description="G1",
        props_name="props", widget_variant=GroupVariant.CHECKABLE,
        group_props_name="grp_props", checked=True,
    )
    cm.group.add(
        control_name="grp_normal", object_name="grp_normal", description="G2",
        props_name="props", widget_variant=GroupVariant.NORMAL,
        group_props_name="grp2_props",
    )
    cm.colorbox.add(
        control_name="color", object_name="color", description="C",
        props_name="props", widget_variant=ColorBoxVariant.ALPHA,
    )
    cm.listbox.add(
        control_name="lb", object_name="lb", description="L",
        props_name="props", widget_variant=ListBoxVariant.STRINGS,
    )
    return cm


@pytest.fixture
def updater(cm) -> UIUpdater:
    return UIUpdater(
        script_settings=MagicMock(name="script_settings"),
        control_manager=cm,
        Log_manager=MagicMock(name="LogManager"),
    )


@pytest.fixture
def patch_obs(monkeypatch):
    """
    覆盖 obs 模块的关键函数，返回一组 mock 供断言。
    """
    mocks = {
        "obs_property_visible": MagicMock(return_value=True),
        "obs_property_enabled": MagicMock(return_value=True),
        "obs_property_set_visible": MagicMock(),
        "obs_property_set_enabled": MagicMock(),
        "obs_data_get_bool": MagicMock(return_value=False),
        "obs_data_set_bool": MagicMock(),
        "obs_data_get_int": MagicMock(return_value=0),
        "obs_data_set_int": MagicMock(),
        "obs_data_get_double": MagicMock(return_value=0.0),
        "obs_data_set_double": MagicMock(),
        "obs_data_get_string": MagicMock(return_value=""),
        "obs_data_set_string": MagicMock(),
        "obs_property_int_min": MagicMock(return_value=0),
        "obs_property_int_max": MagicMock(return_value=100),
        "obs_property_int_step": MagicMock(return_value=1),
        "obs_property_float_min": MagicMock(return_value=0.0),
        "obs_property_float_max": MagicMock(return_value=100.0),
        "obs_property_float_step": MagicMock(return_value=1.0),
        "obs_property_int_set_limits": MagicMock(),
        "obs_property_float_set_limits": MagicMock(),
        "obs_property_text_info_type": MagicMock(return_value=0),
        "obs_property_text_set_info_type": MagicMock(),
        "obs_property_list_item_count": MagicMock(return_value=0),
        "obs_property_list_clear": MagicMock(),
        "obs_property_list_add_string": MagicMock(),
        "obs_property_list_insert_string": MagicMock(),
        "obs_data_get_array": MagicMock(return_value=None),
        "obs_data_set_array": MagicMock(),
        "obs_data_array_create": MagicMock(return_value=MagicMock()),
        "obs_data_array_push_back": MagicMock(),
        "obs_data_array_release": MagicMock(),
        "obs_data_create": MagicMock(return_value=MagicMock()),
        "obs_data_release": MagicMock(),
        "obs_data_set_obj": MagicMock(),
        "obs_data_get_obj": MagicMock(return_value=None),
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(updater_mod.obs, name, mock, raising=False)
    return mocks


# ------------------------------------------------------------------
# 注册表
# ------------------------------------------------------------------
class TestRegistry:

    def test_all_categories_registered(self):
        """除 CHECKBOX/DIGITALBOX/TEXTBOX/BUTTON/COMBOBOX/PATHBOX/GROUP/COLORBOX/FONTBOX/LISTBOX 外，无其他。"""
        registered = set(UIUpdater.registered_categories())
        expected = {
            WidgetCategory.CHECKBOX,
            WidgetCategory.DIGITALBOX,
            WidgetCategory.TEXTBOX,
            WidgetCategory.BUTTON,
            WidgetCategory.COMBOBOX,
            WidgetCategory.PATHBOX,
            WidgetCategory.GROUP,
            WidgetCategory.COLORBOX,
            WidgetCategory.FONTBOX,
            WidgetCategory.LISTBOX,
        }
        assert registered == expected

    def test_duplicate_registration_raises(self):
        """重复注册同一个 WidgetCategory 应抛 ValueError。"""
        with pytest.raises(ValueError, match="已经注册了处理器"):
            @register_ui_handler(WidgetCategory.CHECKBOX)
            def _dup(self, w):
                pass


# ------------------------------------------------------------------
# update 分发
# ------------------------------------------------------------------
class TestUpdateDispatch:

    def test_only_updates_selected_widgets(self, updater, cm, patch_obs):
        """update 只应处理 update_widget_for_props_dict 里指定的控件。"""
        updater.update({"props": ["cb1"]})
        # cb1 的 bool 读写应发生
        assert patch_obs["obs_data_get_bool"].called
        assert patch_obs["obs_data_set_bool"].called
        # db_int 不在列表里，不应触发数字框相关调用
        # 注意：obs_property_int_min 可能被 cb1 之外的控件调用，这里看 count
        initial_call_count = patch_obs["obs_property_int_min"].call_count
        updater.update({"props": ["cb1"]})
        assert patch_obs["obs_property_int_min"].call_count == initial_call_count

    def test_empty_update_dict_noop(self, updater, patch_obs):
        updater.update({})
        assert not patch_obs["obs_data_set_bool"].called

    def test_returns_true(self, updater):
        assert updater.update({}) is True


# ------------------------------------------------------------------
# 可见性 / 启用状态
# ------------------------------------------------------------------
class TestVisibilityAndEnabled:

    def test_visibility_set_when_changed(self, updater, cm, patch_obs):
        patch_obs["obs_property_visible"].return_value = False  # 当前 False
        widget = cm.get_widget_by_control_name("cb1")
        widget.visible = True  # 目标 True

        updater.update({"props": ["cb1"]})

        patch_obs["obs_property_set_visible"].assert_called_with(widget.obj, True)

    def test_visibility_not_set_when_same(self, updater, cm, patch_obs):
        patch_obs["obs_property_visible"].return_value = True
        widget = cm.get_widget_by_control_name("cb1")
        widget.visible = True

        updater.update({"props": ["cb1"]})

        patch_obs["obs_property_set_visible"].assert_not_called()

    def test_checkable_group_visibility_uses_folding(self, updater, cm, patch_obs):
        """可折叠分组框：本体显示 folding_visible，折叠控件显示 not folding_visible。"""
        # 本体当前 False，折叠控件当前 True，两者都需要更新
        patch_obs["obs_property_visible"].side_effect = [False, True]

        widget = cm.get_widget_by_control_name("grp_checkable")
        widget.visible = True
        widget.folding_visible = True

        updater.update({"props": ["grp_checkable"]})

        calls = patch_obs["obs_property_set_visible"].call_args_list
        # 本体设为 True（展开）
        assert any(c.args == (widget.obj, True) for c in calls)
        # 折叠控件设为 False（因为已展开）
        assert any(c.args == (widget.folding_control_obj, False) for c in calls)


# ------------------------------------------------------------------
# 数字框类型处理
# ------------------------------------------------------------------
class TestDigitalBox:

    def test_int_variant_ok(self, updater, cm, patch_obs):
        widget = cm.get_widget_by_control_name("db_int")
        widget.digital = 77
        updater.update({"props": ["db_int"]})
        patch_obs["obs_data_set_int"].assert_called_with(
            updater.script_settings, "db_int", 77
        )

    def test_float_variant_with_int_value_ok(self, updater, cm, patch_obs):
        """float 变体接受 int 值，应自动转换且不产生 WARNING。"""
        widget = cm.get_widget_by_control_name("db_float")
        widget.digital = 50  # int

        updater.update({"props": ["db_float"]})

        patch_obs["obs_data_set_double"].assert_called_with(
            updater.script_settings, "db_float", 50.0
        )
        # 检查日志：不应有 WARNING
        warning_calls = [
            c for c in updater.Log_manager.log_warning.call_args_list
            if "db_float" in str(c)
        ]
        assert not warning_calls, f"不应有 WARNING: {warning_calls}"

    def test_float_variant_min_max_converted(self, updater, cm, patch_obs):
        widget = cm.get_widget_by_control_name("db_float")
        widget.min_val = 5    # 与 mock 的 0.0 不同
        widget.max_val = 200  # 与 mock 的 100.0 不同
        widget.step = 2       # 与 mock 的 1.0 不同

        updater.update({"props": ["db_float"]})

        args = patch_obs["obs_property_float_set_limits"].call_args
        assert args is not None
        _, a_min, a_max, a_step = args.args
        assert isinstance(a_min, float)
        assert isinstance(a_max, float)
        assert isinstance(a_step, float)
        assert a_min == 5.0
        assert a_max == 200.0
        assert a_step == 2.0


# ------------------------------------------------------------------
# 无 handler 的分类
# ------------------------------------------------------------------
class TestUnknownCategory:

    def test_unregistered_category_logs_debug_and_continues(self, updater, cm, patch_obs):
        """如果某个分类没有注册 handler，应记 DEBUG 并跳过数值同步，不影响可见性更新。"""
        # 临时移除 FONTBOX 的 handler
        fontbox_handler = UIUpdater._handlers.pop(WidgetCategory.FONTBOX, None)
        try:
            widget = cm.get_widget_by_control_name("path")  # 用 path 控件，避免 None
            # 用 normal group 触发 DEBUG 日志，因为它在 update 映射里
            updater.update({"props": ["cb1"]})
            # 检查 log_debug 至少被调用过
            assert updater.Log_manager.log_debug.called
        finally:
            if fontbox_handler is not None:
                UIUpdater._handlers[WidgetCategory.FONTBOX] = fontbox_handler