from typing import Callable, Dict
from obsScriptFramework.src.data.obsScriptControlData import *
import obspython as obs

# --- 2. 注册装饰器和注册表 ---
_control_creator_registry: Dict[WidgetCategory, Callable] = {}

def creates(control_type: WidgetCategory):
    """装饰器：自动注册控件创建函数到全局注册表"""

    def decorator(creator_func: Callable) -> Callable:
        if control_type in _control_creator_registry:
            raise ValueError(f"控件类型 {control_type} 已注册")
        _control_creator_registry[control_type] = creator_func
        return creator_func

    return decorator

# --- 3. 各控件的具体创建函数 ---

@creates(WidgetCategory.TEXTBOX)
def _create_textbox(w) -> None:
    """
    创建文本框控件
    支持类型: OBS_TEXT_DEFAULT(默认), OBS_TEXT_PASSWORD(密码),
             OBS_TEXT_MULTILINE(多行), OBS_TEXT_INFO(信息文本)
    """
    log_save(obs.LOG_INFO, f"文本框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量（假设w.Type已经是OBS常量或可转换的字符串）
    obs_text_type = getattr(obs, f"OBS_TEXT_{w.Type}", obs.OBS_TEXT_DEFAULT) if isinstance(w.Type, str) else w.Type
    w.Obj = obs.obs_properties_add_text(w.Props, w.Name, w.Description, obs_text_type)

    # 如果是信息文本类型，设置信息类型
    if hasattr(w, 'InfoType') and obs_text_type == obs.OBS_TEXT_INFO:
        obs.obs_property_text_set_info_type(w.Obj, w.InfoType)

@creates(WidgetCategory.BUTTON)
def _create_button(w) -> None:
    """
    创建按钮控件
    支持类型: OBS_BUTTON_DEFAULT(默认), OBS_BUTTON_URL(URL链接)
    """
    log_save(obs.LOG_INFO, f"按钮控件: {w.Name} 【{w.Description}】")

    # 创建按钮（回调函数w.Callback需提前定义）
    w.Obj = obs.obs_properties_add_button(w.Props, w.Name, w.Description, w.Callback)

    # 设置按钮类型
    obs_button_type = getattr(obs, f"OBS_BUTTON_{w.Type}", obs.OBS_BUTTON_DEFAULT) if isinstance(w.Type,
                                                                                                 str) else w.Type
    obs.obs_property_button_set_type(w.Obj, obs_button_type)

    # 如果是URL按钮，设置URL地址
    if obs_button_type == obs.OBS_BUTTON_URL and hasattr(w, 'Url'):
        obs.obs_property_button_set_url(w.Obj, w.Url)

@creates(WidgetCategory.COMBOBOX)
def _create_combobox(w) -> None:
    """
    创建组合框（下拉列表）控件
    支持类型: OBS_COMBO_TYPE_LIST(列表), OBS_COMBO_TYPE_EDITABLE(可编辑)
    """
    log_save(obs.LOG_INFO, f"组合框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_combo_type = getattr(obs, f"OBS_COMBO_TYPE_{w.Type}", obs.OBS_COMBO_TYPE_LIST) if isinstance(w.Type,
                                                                                                     str) else w.Type

    # 创建组合框，格式固定为字符串
    w.Obj = obs.obs_properties_add_list(
        w.Props,
        w.Name,
        w.Description,
        obs_combo_type,
        obs.OBS_COMBO_FORMAT_STRING
    )

    # 如果有预定义选项列表，则添加选项
    if hasattr(w, 'DictionaryList') and w.DictionaryList:
        # 首先添加默认选项（如果有）
        if hasattr(w, 'Text') and hasattr(w, 'Value'):
            obs.obs_property_list_insert_string(w.Obj, 0, w.Text, w.Value)

        # 添加其他选项（排除默认选项避免重复）
        for item in w.DictionaryList:
            item_label = item.get("label", "")
            item_value = item.get("value", "")
            if item_label != getattr(w, 'Text', ""):
                obs.obs_property_list_add_string(w.Obj, item_label, item_value)

@creates(WidgetCategory.PATHBOX)
def _create_pathbox(w) -> None:
    """
    创建路径选择框控件
    支持类型: OBS_PATH_FILE(文件), OBS_PATH_DIRECTORY(目录)
    """
    log_save(obs.LOG_INFO, f"路径对话框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_path_type = getattr(obs, f"OBS_PATH_{w.Type}", obs.OBS_PATH_FILE) if isinstance(w.Type, str) else w.Type

    # 获取过滤器、起始路径等可选参数
    filter_str = getattr(w, 'Filter', "*.*")
    default_path = getattr(w, 'StartPath', "")

    w.Obj = obs.obs_properties_add_path(
        w.Props,
        w.Name,
        w.Description,
        obs_path_type,
        filter_str,
        default_path
    )

@creates(WidgetCategory.GROUP)
def _create_group(w) -> None:
    """
    创建分组框控件
    支持类型: OBS_GROUP_NORMAL(普通), OBS_GROUP_CHECKABLE(可勾选)
    """
    log_save(obs.LOG_INFO, f"分组框控件: {w.Name} 【{w.Description}】")

    # 将字符串类型转换为OBS常量
    obs_group_type = getattr(obs, f"OBS_GROUP_{w.Type}", obs.OBS_GROUP_NORMAL) if isinstance(w.Type, str) else w.Type

    # 确保分组有对应的属性集对象
    if not hasattr(w, 'GroupProps'):
        log_save(obs.LOG_WARNING, f"分组 {w.Name} 缺少GroupProps属性")
        return

    w.Obj = obs.obs_properties_add_group(
        w.Props,
        w.Name,
        w.Description,
        obs_group_type,
        w.GroupProps
    )

    # 如果是可勾选分组，创建额外的折叠控制复选框
    if obs_group_type == obs.OBS_GROUP_CHECKABLE:
        folding_name = f"{w.Name}_folding"
        folding_desc = f"{w.Description}[折叠]"
        w.FoldingObj = obs.obs_properties_add_bool(w.Props, folding_name, folding_desc)
        log_save(obs.LOG_INFO, f"创建可勾选分组折叠控制: {folding_name}")

@creates(WidgetCategory.CHECKBOX)
def _create_checkbox(w):
    """创建复选框控件"""
    log_save(obs.LOG_INFO, f"复选框控件: {w.Name} 【{w.Description}】")
    w.Obj = obs.obs_properties_add_bool(w.Props, w.Name, w.Description)

@creates(WidgetCategory.DIGITALBOX)
def _create_digitalbox(w):
    """创建数字输入或滑块控件"""
    log_save(obs.LOG_INFO, f"数字框控件: {w.Name} 【{w.Description}】")
    type_map = {
        "IntSlider": obs.obs_properties_add_int_slider,
        "Int": obs.obs_properties_add_int,
        "FloatSlider": obs.obs_properties_add_float_slider,
        "Float": obs.obs_properties_add_float,
    }
    creator_func = type_map.get(w.Type, obs.obs_properties_add_float_slider)
    w.Obj = creator_func(w.Props, w.Name, w.Description, w.Min, w.Max, w.Step)
    if w.Suffix:
        obs.obs_property_int_set_suffix(w.Obj, w.Suffix)

# --- 4. 辅助函数：获取创建器 ---
def get_control_creator(control_type: WidgetCategory):
    """根据控件类型字符串获取对应的创建函数"""
    try:
        return _control_creator_registry.get(control_type)
    except ValueError:
        log_save(obs.LOG_WARNING, f"未知的控件类型: {control_type}")
        return None

def _init_property_sets(widgets):
    """职责1：初始化所有需要的属性集"""
    props_dict = {"props": obs.obs_properties_create()}
    for props_name in widget.props_Collection:
        props_dict[props_name] = obs.obs_properties_create()
    for w in widgets:
        w.Props = props_dict[w.PropsName]
        if w.WidgetType == WidgetCategory.GROUP:
            w.GroupProps = props_dict[w.GroupPropsName]
    return props_dict

def _create_control_for_widget(w):
    """为单个控件对象执行创建和通用设置"""
    # 1. 获取对应的创建函数
    creator = get_control_creator(w.WidgetType)
    if not creator:
        log_save(obs.LOG_WARNING, f"未找到 {w.WidgetType} 的创建器，跳过")
        return

    # 2. 执行创建
    creator(w)

    # 3. 设置长描述（所有控件通用）
    if hasattr(w, 'LongDescription') and w.LongDescription:
        obs.obs_property_set_long_description(w.Obj, w.LongDescription)

    # 4. 设置修改回调（根据条件）
    callback_conditions = [
        getattr(w, 'ModifiedIs', False),
        (w.WidgetType == WidgetCategory.GROUP and
         getattr(w, 'Type', None) == obs.OBS_GROUP_CHECKABLE)
    ]

    if any(callback_conditions):
        log_save(obs.LOG_INFO, f"为{w.WidgetType}: 【{w.Description}】添加触发回调")
        obs.obs_property_set_modified_callback(
            w.Obj,
            lambda ps, p, st, name=w.Name: property_modified(name)
        )

        # 分组框的特殊折叠控件回调
        if w.WidgetType == WidgetCategory.GROUP and hasattr(w, 'FoldingObj'):
            obs.obs_property_set_modified_callback(
                w.FoldingObj,
                lambda ps, p, st, name=f"{w.Name}_folding": property_modified(name)
            )

def script_properties():
    """主属性创建函数"""
    log_save(obs.LOG_INFO, "script_properties 被调用")

    # 1. 初始化属性集
    all_widgets = widget.get_sorted_controls().copy()
    props_dict = _init_property_sets(all_widgets)

    # 2. 创建所有控件
    for w in all_widgets:
        _create_control_for_widget(w)

    # 3. 更新界面并返回
    update_ui_interface_data()
    return props_dict["props"]
