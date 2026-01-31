from typing import Callable, Any


class ModifiedFunction:

    def __init__(self, start_property_name, end_property_name, **kwargs):
        self.start_property_name = start_property_name
        self.end_property_name = end_property_name
        self.ObsScriptGlobalVariable = kwargs["a_s_g_v"]
        self.isScript_propertiesIs = True

    def property_modified(self, property_name) -> Callable[[Any, Any, Any], None]:
        def build_pm(ps, p, st):
            self.ObsScriptGlobalVariable.Log_manager.log_info(f"监测到控件变动: {property_name}")
            if property_name == self.start_property_name:
                self.isScript_propertiesIs = True
            if property_name == self.end_property_name:
                self.isScript_propertiesIs = False
            if not self.isScript_propertiesIs:
                pass
        return build_pm