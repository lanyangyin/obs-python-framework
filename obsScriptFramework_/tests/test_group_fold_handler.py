"""GroupFoldHandler 单元测试。"""
from unittest.mock import MagicMock, call

import pytest

from src.data.obsScriptControlData import GroupVariant, WidgetCategory
from src.framework.obsScriptControlDataFramework import ControlManager
from src.framework.groupFoldHandler import GroupFoldHandler
from src.tool.CommonDataManager import CommonDataManager


# ---------- fixtures ----------
@pytest.fixture
def cm() -> ControlManager:
    cm = ControlManager()
    cm.group.add(
        control_name="my_group",
        object_name="my_group",
        description="测试分组",
        widget_variant=GroupVariant.CHECKABLE,
        group_props_name="my_props",
        props_name="props",
    )
    # 往分组里加两个子控件，用于验证 props 映射
    cm.checkbox.add(
        control_name="cb1", object_name="cb1",
        description="子1", props_name="my_props", checked=True,
    )
    cm.checkbox.add(
        control_name="cb2", object_name="cb2",
        description="子2", props_name="my_props", checked=True,
    )
    return cm


@pytest.fixture
def sys_data(tmp_path) -> CommonDataManager:
    return CommonDataManager(str(tmp_path / "sys.json"))


@pytest.fixture
def mock_ui_updater():
    return MagicMock(name="UIUpdater")


@pytest.fixture
def mock_log():
    return MagicMock(name="LogManager")


@pytest.fixture
def handler(cm, sys_data, mock_ui_updater, mock_log) -> GroupFoldHandler:
    return GroupFoldHandler(
        sys_common_data_manager=sys_data,
        control_ui_updater_manager=mock_ui_updater,
        control_manager=cm,
        log_manager=mock_log,
    )


@pytest.fixture
def mock_modified_fn():
    """Mock ModifiedFunction，property_modified 返回一个可调用的 mock。"""
    mf = MagicMock(name="ModifiedFunction")
    inner = MagicMock(name="inner_callback", return_value=True)
    mf.property_modified.return_value = inner
    mf._inner = inner
    return mf


# ---------- 测试用例 ----------
class TestFoldToggle:

    def test_initial_state_is_expanded(self, handler, cm, sys_data):
        """新建的分组框默认应为展开状态。"""
        widget = cm.get_widget_by_control_name("my_group")
        assert handler._is_expanded(widget.group_props_name) is True

    def test_collapse_from_expanded(self, handler, cm, sys_data, mock_ui_updater, mock_modified_fn):
        """从展开状态折叠：应写入持久化数据，并只刷新分组框自身。"""
        widget = cm.get_widget_by_control_name("my_group")
        callback = handler.make_callback(
            control_name="my_group",
            inner_callback_name="test_callback",
            modified_function_manager=mock_modified_fn,
        )

        result = callback(None, None, None)

        assert result is True
        assert widget.checked is False
        assert widget.folding_visible is False
        assert widget.folding_enabled is False
        assert "my_props" in sys_data.get_data("system", "group_folded_props_names")

        # UI 更新应只包含分组框自身
        assert mock_ui_updater.update.call_count == 1
        update_kwargs = mock_ui_updater.update.call_args.kwargs
        assert update_kwargs["update_widget_for_props_dict"] == {
            "props": ["my_group"],
        }

        # 内部回调被调用一次
        mock_modified_fn.property_modified.assert_called_once_with("my_group", "test_callback")
        mock_modified_fn._inner.assert_called_once()

    def test_expand_from_collapsed(self, handler, cm, sys_data, mock_ui_updater, mock_modified_fn):
        """从折叠状态展开：应移除持久化数据，并刷新分组框及其子控件。"""
        widget = cm.get_widget_by_control_name("my_group")

        # 先手动折叠
        sys_data.add_data("system", "group_folded_props_names", "my_props", 999)
        widget.checked = False
        widget.folding_visible = False
        widget.folding_enabled = False

        callback = handler.make_callback(
            control_name="my_group",
            inner_callback_name=None,
            modified_function_manager=mock_modified_fn,
        )
        result = callback(None, None, None)

        assert result is True
        assert widget.checked is True
        assert widget.folding_visible is True
        assert widget.folding_enabled is True
        assert "my_props" not in sys_data.get_data("system", "group_folded_props_names")

        # UI 更新应包含分组框自身 + 子控件列表
        assert mock_ui_updater.update.call_count == 1
        update_kwargs = mock_ui_updater.update.call_args.kwargs
        assert update_kwargs["update_widget_for_props_dict"]["props"] == ["my_group"]
        assert update_kwargs["update_widget_for_props_dict"]["my_props"] == ["cb1", "cb2"]

        # 内部回调为 None，不调用
        mock_modified_fn.property_modified.assert_not_called()

    def test_toggle_twice_returns_to_original(self, handler, cm, sys_data, mock_ui_updater, mock_modified_fn):
        """连续折叠两次应回到展开状态。"""
        widget = cm.get_widget_by_control_name("my_group")
        callback = handler.make_callback("my_group", None, mock_modified_fn)

        callback(None, None, None)  # 折叠
        callback(None, None, None)  # 展开

        assert widget.checked is True
        assert "my_props" not in sys_data.get_data("system", "group_folded_props_names")


class TestEdgeCases:

    def test_unknown_control_returns_false(self, handler, mock_ui_updater, mock_log, mock_modified_fn):
        """控件不存在时应返回 False 且记录错误，不抛异常。"""
        callback = handler.make_callback("no_such_group", None, mock_modified_fn)
        result = callback(None, None, None)

        assert result is False
        mock_ui_updater.update.assert_not_called()
        mock_log.log_error.assert_called_once()
        assert "no_such_group" in mock_log.log_error.call_args.args[0]

    def test_inner_callback_none_skips_invocation(self, handler, mock_modified_fn):
        """inner_callback_name 为 None 时不调用 property_modified。"""
        callback = handler.make_callback("my_group", None, mock_modified_fn)
        callback(None, None, None)
        mock_modified_fn.property_modified.assert_not_called()

    def test_inner_callback_exception_is_caught(self, handler, mock_modified_fn, mock_log):
        """内部回调抛异常时应被捕获，不影响折叠逻辑。"""
        mock_modified_fn._inner.side_effect = RuntimeError("boom")

        callback = handler.make_callback("my_group", "test_callback", mock_modified_fn)
        result = callback(None, None, None)

        assert result is True  # 折叠仍然成功
        mock_log.log_error.assert_called()
        # 错误信息包含回调名
        error_msgs = [c.args[0] for c in mock_log.log_error.call_args_list]
        assert any("test_callback" in msg for msg in error_msgs)


class TestCacheClear:

    def test_cache_clear_called_when_provided(self, cm, sys_data, mock_ui_updater, mock_log, mock_modified_fn):
        """传入 control_data_set_functions 时，状态变化应触发其 clear()。"""
        mock_cdsf = MagicMock(name="ControlDataSetFunctions")
        handler = GroupFoldHandler(
            sys_common_data_manager=sys_data,
            control_ui_updater_manager=mock_ui_updater,
            control_manager=cm,
            log_manager=mock_log,
            control_data_set_functions=mock_cdsf,
        )

        callback = handler.make_callback("my_group", None, mock_modified_fn)
        callback(None, None, None)

        mock_cdsf.clear.assert_called_once()

    def test_cache_clear_not_called_when_none(self, handler, mock_modified_fn):
        """未传入 control_data_set_functions 时不应报错。"""
        callback = handler.make_callback("my_group", None, mock_modified_fn)
        result = callback(None, None, None)
        assert result is True