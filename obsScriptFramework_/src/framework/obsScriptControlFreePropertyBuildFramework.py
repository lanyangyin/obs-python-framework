# obsScriptFramework_/src/framework/obsScriptControlFreePropertyBuildFramework.py

# 保留原有的 build_controls 函数，并在其下方添加新函数

def apply_user_properties(
    control_manager,
    control_property_table_dictionary,
    cds,
    all_props_mapping=None,
):
    """
    根据 CSV 中定义的控件自由属性，调用对应的回调函数填充控件对象属性。

    参数：
        control_manager: 控件管理器实例
        control_property_table_dictionary: 包含控件定义的字典，必须包含键 "all_controls"
        cds: ControlDataSetFunction 实例，包含获取属性值的方法
        update_widget_for_props_dict: 已有的需要更新控件的映射字典，如果为 None 则重新获取

    返回：
        all_props_mapping: 计算出的控件属性组名称到控件标识名列表的映射字典
    """
    # 确定需要更新控件的映射
    if all_props_mapping is not None:
        all_props_mapping = control_manager.get_props_mapping()

    # 遍历所有控件数据，填充用户属性
    for controls_data in control_property_table_dictionary["all_controls"]:
        props_name = controls_data["property_name"]
        fold_props_name = cds.get_common_group_fold()
        if props_name in fold_props_name:
            continue
        if props_name in all_props_mapping:
            control_name = controls_data["group_properties"]["group_1"]["control_name"]
            if control_name in all_props_mapping[props_name]:
                # 合并公共自由属性和私有自由属性
                control_properties = controls_data["group_properties"].get("group_3", {})
                control_properties |= controls_data["group_properties"].get("group_4", {})

                # 获取控件对象
                control_manager_category = getattr(control_manager, controls_data["widget_category"].lower())
                control_manager_category_object = getattr(control_manager_category, controls_data["object_name"])

                # 遍历所有自由属性，调用对应的回调函数获取值并设置
                for control_properties_name in control_properties:
                    control_property_function_name = control_properties[control_properties_name]
                    if hasattr(cds, control_property_function_name):
                        get_property_function = getattr(cds, control_property_function_name)
                        control_property_value = get_property_function()
                        setattr(control_manager_category_object, control_properties_name, control_property_value)

    return all_props_mapping