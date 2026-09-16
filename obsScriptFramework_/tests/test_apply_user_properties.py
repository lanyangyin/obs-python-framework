def test_apply_user_properties_with_folded_group(tmp_path):
    """分组框折叠时，apply_user_properties 不应抛 KeyError。"""
    from src.framework.obsScriptControlFreePropertyBuildFramework import apply_user_properties
    from src.framework.obsScriptControlDataFramework import ControlManager
    from src.data.obsScriptControlData import GroupVariant
    from plugins.ControlFunction import ControlDataSetFunction
    from unittest.mock import MagicMock

    cm = ControlManager()
    cm.group.add(
        control_name="g", object_name="g", description="G",
        widget_variant=GroupVariant.CHECKABLE,
        group_props_name="g_props", props_name="props",
    )
    cm.checkbox.add(
        control_name="cb", object_name="cb", description="C",
        props_name="g_props", checked=True,
    )

    sys_data = MagicMock()
    sys_data.get_data.return_value = ["g_props"]  # 模拟已折叠

    cdsf = MagicMock(spec=ControlDataSetFunction)
    cdsf.get_common_group_fold.return_value = {"g_props"}

    log = MagicMock()
    control_property_table_dictionary = {
        "all_controls": [
            {
                "object_name": "g",
                "widget_category": "GROUP",
                "props_name": "props",
                "source_line": 2,
                "properties": {"control_name": "g"},
                "group_properties": {
                    "group_1": {"object_name": "g", "description": "G"},
                    "group_3": {"visible": "default_true"},
                    "group_4": {},
                },
            },
            {
                "object_name": "cb",
                "widget_category": "CHECKBOX",
                "props_name": "g_props",
                "source_line": 3,
                "properties": {"control_name": "cb"},
                "group_properties": {
                    "group_1": {"object_name": "cb", "description": "C"},
                    "group_3": {"visible": "default_true"},
                    "group_4": {"checked": "checked_reference_data"},
                },
            },
        ]
    }

    # 不应抛异常
    apply_user_properties(
        log_manager=log,
        control_manager=cm,
        control_property_table_dictionary=control_property_table_dictionary,
        ControlDataSetFunctions=cdsf,
    )