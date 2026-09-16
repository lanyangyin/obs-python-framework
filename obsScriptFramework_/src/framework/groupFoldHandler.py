"""
可折叠分组框的折叠/展开逻辑处理器。

把原先内联在 build_controls 中的 group_folded_modified_callback 抽出为独立类，
方便单元测试和后续扩展。
"""
from typing import Callable, Optional, Any


class GroupFoldHandler:
    """
    处理可勾选分组框（GroupVariant.CHECKABLE）的折叠/展开逻辑。

    职责：
    1. 维护折叠状态（持久化到 CommonDataManager）
    2. 更新分组框自身的 folding_visible / folding_enabled / checked
    3. 计算需要刷新 UI 的控件映射
    4. 清理动态属性缓存（可选）
    5. 调用用户自定义的 modified_callback
    """

    # 持久化相关的常量
    FOLD_DATA_USER = "system"
    FOLD_DATA_TYPE = "group_folded_props_names"
    FOLD_DATA_MAX = 999

    def __init__(
        self,
        sys_common_data_manager: Any,
        control_ui_updater_manager: Any,
        control_manager: Any,
        log_manager: Any,
        control_data_set_functions: Optional[Any] = None,
    ) -> None:
        """
        :param sys_common_data_manager: CommonDataManager 实例，用于持久化折叠状态
        :param control_ui_updater_manager: UIUpdater 实例，用于刷新界面
        :param control_manager: ControlManager 实例，用于按名称查控件、取 props 映射
        :param log_manager: 日志管理器
        :param control_data_set_functions: 可选的 ControlDataSetFunction 实例，
                                          若非 None，则在状态变化时调用其 clear() 清理缓存
        """
        self.sys_common_data_manager = sys_common_data_manager
        self.control_ui_updater_manager = control_ui_updater_manager
        self.control_manager = control_manager
        self.log_manager = log_manager
        self.control_data_set_functions = control_data_set_functions

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def make_callback(
        self,
        control_name: str,
        inner_callback_name: Optional[str],
        modified_function_manager: Any,
    ) -> Callable:
        """
        为一个可折叠分组框生成 modified_callback。

        :param control_name: 分组框的 control_name
        :param inner_callback_name: 用户在 CSV 里配置的 modified_callback 函数名，
                                    可为 None（表示只做折叠，不调用用户回调）
        :param modified_function_manager: ModifiedFunction 实例
        :return: 可作为 obs_property_set_modified_callback 使用的回调函数
        """
        def group_folded_modified_callback(ps, p, st=None) -> bool:
            return self._handle_fold_toggle(
                control_name=control_name,
                inner_callback_name=inner_callback_name,
                modified_function_manager=modified_function_manager,
                ps=ps, p=p, st=st,
            )
        return group_folded_modified_callback

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------
    def _handle_fold_toggle(
        self,
        control_name: str,
        inner_callback_name: Optional[str],
        modified_function_manager: Any,
        ps: Any = None,
        p: Any = None,
        st: Any = None,
    ) -> bool:
        widget = self.control_manager.get_widget_by_control_name(control_name)
        if not widget:
            self.log_manager.log_error(
                f"[分组折叠失败] 未找到分组框 '{control_name}'，无法切换折叠状态。"
            )
            return False

        group_props_name = widget.group_props_name

        # 1. 切换持久化状态
        self._toggle_fold_state(group_props_name)

        # 2. 重新计算展开状态，同步到控件数据对象
        is_expanded = self._is_expanded(group_props_name)
        widget.folding_visible = is_expanded
        widget.folding_enabled = is_expanded
        widget.checked = is_expanded

        # 3. 计算需要刷新 UI 的控件映射
        if not is_expanded:
            self.log_manager.log_info(f"折叠分组框{control_name}")
            update_widget_for_props_dict = {
                widget.props_name: [control_name],
            }
        else:
            self.log_manager.log_info(f"展开分组框{control_name}")
            update_widget_for_props_dict = {
                widget.props_name: [control_name],
                widget.group_props_name: self.control_manager.get_props_mapping().get(
                    widget.group_props_name, []
                ),
            }

        # 4. 清理动态属性缓存（如果配置了）
        if self.control_data_set_functions is not None:
            self.control_data_set_functions.clear()

        # 5. 刷新 UI
        self.control_ui_updater_manager.update(
            update_widget_for_props_dict=update_widget_for_props_dict
        )

        # 6. 调用用户自定义的 modified_callback（如果有）
        if inner_callback_name:
            try:
                callback = modified_function_manager.property_modified(
                    control_name, inner_callback_name
                )
                callback(ps, p, st)
            except Exception as e:
                self.log_manager.log_error(
                    f"[分组折叠回调失败] 分组框 '{control_name}' 的内部回调 "
                    f"'{inner_callback_name}' 执行出错: {type(e).__name__}: {e}"
                )

        return True

    def _toggle_fold_state(self, group_props_name: str) -> None:
        """在持久化数据中切换折叠状态：存在则移除，不存在则添加。"""
        current = (
            self.sys_common_data_manager.get_data(
                self.FOLD_DATA_USER, self.FOLD_DATA_TYPE
            ) or []
        )
        if group_props_name in current:
            self.sys_common_data_manager.remove_data(
                self.FOLD_DATA_USER, self.FOLD_DATA_TYPE, group_props_name
            )
        else:
            self.sys_common_data_manager.add_data(
                self.FOLD_DATA_USER,
                self.FOLD_DATA_TYPE,
                group_props_name,
                self.FOLD_DATA_MAX,
            )

    def _is_expanded(self, group_props_name: str) -> bool:
        """判断分组框是否处于展开状态。"""
        current = (
            self.sys_common_data_manager.get_data(
                self.FOLD_DATA_USER, self.FOLD_DATA_TYPE
            ) or []
        )
        return group_props_name not in current