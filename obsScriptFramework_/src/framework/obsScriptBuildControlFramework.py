class ObsScriptBuildControlFramework:
    def __init__(self, *args, **kwargs):
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]

    def fill_attributes(self):
        if not self.ObsScriptGlobalVariable.update_widget_for_props_dict:
            self.ObsScriptGlobalVariable.update_widget_for_props_dict = self.ObsScriptGlobalVariable.control_manager.get_props_mapping()

        update_widget_for_props_name = set()
        for props_name in self.ObsScriptGlobalVariable.update_widget_for_props_dict:
            update_widget_for_props_name |= set(self.ObsScriptGlobalVariable.update_widget_for_props_dict[props_name])

        # 设定控件用户属性
        for controls_data in control_property_table_dictionary["all_controls"]:
            if controls_data["group_properties"]["group_1"]["control_name"] in update_widget_for_props_name:
                controls = getattr(
                    getattr(
                        self.ObsScriptGlobalVariable.control_manager,
                        controls_data["widget_category"].lower()
                    ),
                    controls_data["object_name"]
                )
                control_properties = controls_data["group_properties"].get("group_3", {}) | controls_data[
                    "group_properties"].get("group_4", {})
                for control_properties_name in control_properties:
                    if hasattr(
                            self.ObsScriptGlobalVariable.cds,
                            controls_data["group_properties"]["group_1"]["control_name"]
                    ):
                        setattr(
                            controls, control_properties_name,
                            getattr(
                                self.ObsScriptGlobalVariable.cds,
                                controls_data["group_properties"]["group_1"]["control_name"]
                            )
                        )
