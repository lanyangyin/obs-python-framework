# obsScriptFramework_/src/framework/obsScriptControlFreePropertyBuildFramework.py
from src.data.obsScriptControlData import WidgetCategory, GroupVariant, TextBoxVariant


def _is_property_supported(widget, prop_name: str) -> bool:
    """
    判断某个自由属性是否适用于给定控件。
    不支持的属性会被静默跳过，避免在 CSV 中误配置时抛异常。

    注意：这里的规则是硬编码的，阶段 4 会抽成适用性表。
    """
    category = getattr(widget, "widget_category", None)
    variant = getattr(widget, "widget_variant", None)

    if category == WidgetCategory.GROUP:
        # 普通分组框没有 checked 属性
        if variant == GroupVariant.NORMAL and prop_name == "checked":
            return False
    elif category == WidgetCategory.TEXTBOX:
        # 非 INFO 文本框没有 info_type 属性
        if variant != TextBoxVariant.INFO and prop_name == "info_type":
            return False
    return True


def _log_unsupported_property(log_manager, controls_data, control_name, prop_name, widget):
    """记录一条被跳过的自由属性，使用 DEBUG 级别，避免刷屏。"""
    category = getattr(widget, "widget_category", None)
    variant = getattr(widget, "widget_variant", None)
    category_str = category.value if category else "?"
    variant_str = f"/{variant.name}" if variant else ""
    log_manager.log_debug(
        f"⏭️第 {controls_data.get('source_line', '?')} 行: "
        f"控件 '{control_name}'（{category_str}{variant_str}）"
        f"不支持属性 '{prop_name}'，已跳过。"
    )


def apply_user_properties(
    log_manager,
    control_manager,
    control_property_table_dictionary,
    ControlDataSetFunctions,
    all_props_mapping=None,
):
    """
    根据 CSV 中定义的控件自由属性，调用对应的回调函数填充控件对象属性。
    拉取控件自由属性到控件管理器中

    参数：
        log_manager: 日志管理器实例
        control_manager: 控件管理器实例
        control_property_table_dictionary: 包含控件定义的字典，必须包含键 "all_controls"
        ControlDataSetFunctions: ControlDataSetFunction 实例，包含获取属性值的方法
        all_props_mapping: 已有的需要更新控件的映射字典，如果为 None 则重新获取

    返回：
        all_props_mapping: 计算出的控件属性组名称到控件标识名列表的映射字典
    """

    # 统一清理动态属性缓存，保证本次运行使用最新的状态
    ControlDataSetFunctions.clear()

    # 确定需要更新控件的映射
    if all_props_mapping is None:
        all_props_mapping = control_manager.get_props_mapping()

    fold_props_name = ControlDataSetFunctions.get_common_group_fold()

    # 遍历所有控件数据，填充用户属性
    for controls_data in control_property_table_dictionary["all_controls"]:
        props_name = controls_data["props_name"]
        if props_name in fold_props_name:
            log_manager.log_debug(
                f'被折叠的控件：'
                f'{controls_data["group_properties"]["group_1"]["control_name"]}'
            )

        if props_name not in all_props_mapping:
            continue

        # 合并所有属性
        all_props = {}
        all_props.update(controls_data.get("properties", {}))
        for group_key, group_props in controls_data.get("group_properties", {}).items():
            all_props.update(group_props)

        control_name = all_props.get("control_name")
        if not control_name:
            continue
        if control_name not in all_props_mapping[props_name]:
            continue

        # 合并公共自由属性和私有自由属性
        control_properties = controls_data["group_properties"].get("group_3", {})
        control_properties |= controls_data["group_properties"].get("group_4", {})
        log_manager.log_debug(f"拉取[{control_name}]自由属性：{control_properties}")

        # 获取控件对象
        try:
            control_manager_category = getattr(
                control_manager, controls_data["widget_category"].lower()
            )
            control_manager_category_object = getattr(
                control_manager_category, controls_data["object_name"]
            )
        except AttributeError as e:
            log_manager.log_error(
                f"[自由属性拉取失败] 第 {controls_data.get('source_line', '?')} 行: "
                f"未找到控件 '{control_name}' "
                f"(category={controls_data['widget_category']}, "
                f"object_name='{controls_data['object_name']}')。\n"
                f"  异常信息: {e}"
            )
            continue

        # 遍历所有自由属性，调用对应的回调函数获取值并设置
        for control_properties_name in control_properties:
            if not _is_property_supported(
                control_manager_category_object, control_properties_name
            ):
                _log_unsupported_property(
                    log_manager, controls_data, control_name,
                    control_properties_name, control_manager_category_object
                )
                continue

            control_property_function_name = control_properties[control_properties_name]
            """控件自由属性值的获取函数的名称"""

            if not hasattr(ControlDataSetFunctions, str(control_property_function_name)):
                log_manager.log_error(
                    f"[自由属性函数未找到] 第 {controls_data.get('source_line', '?')} 行: "
                    f"控件 '{control_name}' 的属性 '{control_properties_name}' "
                    f"指定的函数 '{control_property_function_name}' "
                    f"在 ControlDataSetFunction 中不存在。\n"
                    f"  请在 plugins/ControlFunction.py 的 ControlDataSetFunction "
                    f"类中定义该方法，或检查 CSV 中该列的拼写。"
                )
                continue

            get_property_function = getattr(
                ControlDataSetFunctions, control_property_function_name
            )
            """控件自由属性值的获取函数，类型是函数"""

            try:
                control_property_value = get_property_function(control_name=control_name)
            except Exception as e:
                log_manager.log_error(
                    f"[自由属性计算失败] 第 {controls_data.get('source_line', '?')} 行: "
                    f"控件 '{control_name}' 的属性 '{control_properties_name}' "
                    f"调用 '{control_property_function_name}' 时抛出异常。\n"
                    f"  异常类型: {type(e).__name__}\n"
                    f"  异常信息: {e}"
                )
                continue

            setattr(
                control_manager_category_object,
                control_properties_name,
                control_property_value,
            )
            log_manager.log_debug(
                f"拉取[{control_name}]自由属性：{control_properties_name}"
                f"|属性值获取回调函数名：{control_property_function_name}"
            )

    return all_props_mapping