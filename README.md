## 一、简单使用说明（给初上手者）

### 1.1 环境准备
- 安装 **OBS Studio**（版本 28.0 以上，支持 Python 脚本）。
- 在 OBS 中设置 Python 环境：`工具 → 脚本 → Python 设置`，选择 Python 3.9/3.10 解释器路径。
- 确保 OBS 能正常加载脚本。

### 1.2 文件放置
将整个 `obsScriptFramework_` 文件夹（包含 `plugins/`、`src/`、`widgetData.csv` 等）放置到 OBS 脚本目录中（通常为 `C:\Users\<用户名>\AppData\Roaming\obs-studio\scripts\` 或与 `obsScriptFramework.py` 同级）。  
主入口脚本 `obsScriptFramework.py` 应放在上述目录下。

### 1.3 快速上手步骤
1. **定义控件**  
   打开 `obsScriptFramework_/plugins/widgetData.csv`，按行添加或修改你的控件。每一行代表一个控件对象，列包括控件类型、名称、描述、回调函数等。  
   *参考示例文件内的已有控件即可快速理解*。

2. **实现回调函数**  
   - **按钮点击回调**：在 `plugins/ButtonFunction.py` 的 `BtnFunction` 类中，添加方法，方法名与 CSV 中 `callback` 列的值一致。  
   - **控件值变化回调**：在 `plugins/ControlFunction.py` 的 `ControlDataSetFunction` 类中，添加静态方法，方法名与 CSV 中 `modified_callback` 列的值一致。  
   - **前端事件回调**：在 `BtnFunction` 中添加以 `OBS_FRONTEND_EVENT_xxx` 命名的静态方法（参考 `ExplanatoryDictionary.py` 中的枚举）。

3. **修改描述信息（可选）**  
   编辑 `plugins/obsScriptDescription.html`，可自定义脚本在 OBS 中显示的介绍文字。

4. **加载脚本**  
   在 OBS 中：`工具 → 脚本 → 添加脚本`，选择 `obsScriptFramework.py`。  
   若一切正常，脚本属性页会显示 CSV 中定义的所有控件。

### 1.4 注意事项
- **控件名称唯一性**：同一脚本内 `control_name` 必须全局唯一（包括分组框的 `group_props_name`）。不要使用保留名称 `"group"`。  
- **分组框的 group_props_name**：所有分组框的 `group_props_name` 不能重名，且不能等于所在父容器的 `props_name`。  
- **动态控制可见/可用**：若需要在控件值变化时改变其他控件的可见性、可用性，请在 `ControlDataSetFunction` 的自由属性方法中返回 `True/False`，并在 CSV 中将目标控件的 `visible` / `enabled` 列设为对应的函数名。  
- **日志查看**：框架会自动在脚本所在目录生成 `LOG/` 文件夹，按日期存储日志。在 OBS 脚本日志窗口也可看到简要信息。  
- **修改 CSV 后需重载脚本**：每次编辑 `widgetData.csv` 后，需在 OBS 中重新加载脚本（右键脚本 → 重新加载）。

---

## 二、开发者文档（一）：框架架构与核心设计

### 2.1 设计目标
- **声明式 UI 开发**：通过 CSV 文件描述控件树及属性，无需手写 `obs_properties_add_xxx` 代码。  
- **动态属性绑定**：控件属性（如最小值、选项列表、可见性）可绑定到 Python 函数，支持运行时动态计算。  
- **回调统一管理**：按钮点击、控件修改、前端事件均通过统一的函数映射管理器调用用户自定义逻辑。  
- **状态持久化**：系统常用数据（如折叠分组状态）通过 `CommonDataManager` 自动保存到 JSON。  

### 2.2 整体模块划分
```
obsScriptFramework.py            # 脚本入口，整合所有框架模块
├── src/
│   ├── data/                    # 数据定义与全局变量
│   │   ├── obsScriptControlData.py       # 控件数据类（CheckBoxData等）
│   │   ├── obsScriptGlobalVariable.py    # 全局共享数据（路径、管理器实例）
│   │   └── ExplanatoryDictionary.py      # 事件/日志类型映射
│   ├── tool/                    # 工具类
│   │   ├── LogManager.py                 # 日志管理
│   │   ├── CommonDataManager.py          # 用户/系统通用数据管理（JSON）
│   │   └── scriptCsv2Json.py             # CSV → 控件树解析器
│   └── framework/               # 核心框架
│       ├── obsScriptControlDataFramework.py          # 控件管理器（ControlManager）
│       ├── obsScriptControlInnatePropertyBuildFramework.py   # 天赋属性构建（从CSV生成控件）
│       ├── obsScriptControlFreePropertyBuildFramework.py     # 自由属性构建（动态计算属性）
│       ├── obsSciptButtonFunctionFramework.py         # 按钮回调分发器
│       ├── obsScriptModifiedFunctionFramework.py      # 修改回调分发器
│       ├── obsTriggerFrontendEventFramework.py        # OBS 前端事件监听
│       └── obsScriptControlUiUpdaterFramework.py      # UI 状态同步（可见/可用/值）
├── plugins/                     # 用户扩展目录
│   ├── widgetData.csv           # 控件定义文件
│   ├── ButtonFunction.py        # 按钮回调实现
│   ├── ControlFunction.py       # 控件属性动态计算函数
│   └── GlobalVariable.py        # 用户全局变量
```

### 2.3 工作流程

#### 脚本生命周期钩子
| 钩子函数              | 作用                                                                 |
|----------------------|----------------------------------------------------------------------|
| `script_defaults`    | 初始化所有管理器、解析 CSV、构建控件树、绑定回调、应用自由属性        |
| `script_properties`  | 根据控件管理器中的控件列表，创建 `obs_properties_t` 并返回根属性集    |
| `script_load`        | 注册前端事件回调                                                    |
| `script_update`      | (预留) 当用户修改设置时触发                                        |
| `script_unload`      | 刷新日志缓存                                                         |

#### 控件构建流程
1. `ControlTemplateParser.parse_csv_files()` 读取 `widgetAttributeDefinitionData.csv`（模板）和 `widgetData.csv`（数据），生成包含层级关系的控件树字典。  
2. `build_controls()` 遍历控件树，调用 `ControlManager` 的 `create_widget()` 创建控件数据对象，并绑定 `modified_callback` 和 `click_callback`。  
3. `apply_user_properties()` 遍历所有控件，根据 CSV 中 `group_3`/`group_4` 列定义的“自由属性映射”，调用 `ControlDataSetFunction` 中对应方法计算实际属性值（如 `visible`、`items` 等），写入控件数据对象。  
4. `UIUpdater.update()` 在属性页首次显示时将所有控件数据对象的当前状态同步到 OBS 界面（可见性、数值等）。

#### 回调分发机制
- **按钮点击**：`obs_properties_add_button` 时传入的 `click_callback` 是 `ObsScriptButtonFunction.select(button_name)` 返回的闭包，该闭包再调用 `BtnFunction.button_name()`。  
- **控件值变化**：`obs_property_set_modified_callback` 传入的闭包由 `ModifiedFunction.property_modified(control_name, func_name)` 生成，内部检查 `allow_execution` 标志（由两个内置按钮控制），然后调用 `BtnFunction.func_name(control_name=...)`。  
- **前端事件**：`obs_frontend_add_event_callback` 注册的闭包由 `TriggerFrontendEvent.event_callback()` 返回，内部根据事件类型调用 `BtnFunction.<FrontendEvent(event).name>()`。

### 2.4 扩展点
- **新增控件类型**：在 `WidgetCategory` 枚举中添加、在 `ControlBaseData` 子类中定义专用字段、在 `script_properties` 和 `UIUpdater` 中添加对应处理分支。  
- **自定义属性计算**：在 `ControlDataSetFunction` 中添加带 `@add_clear_cache` 装饰器的静态方法，在 CSV 中将控件的 `visible`/`enabled`/`items` 等列设为该方法名。  
- **自定义用户数据**：通过 `CommonDataManager` 的实例 `sys_common_data_manager` 存取任意 JSON 数据。

---

## 三、开发者文档（二）：API 参考手册

### 3.1 控件数据类（`src.data.obsScriptControlData`）

所有控件类均继承自 `ControlBaseData`，其公共属性：
| 属性                         | 类型                  | 说明                               |
|-----------------------------|-----------------------|------------------------------------|
| `control_name`              | str                   | 全局唯一标识符                     |
| `object_name`               | str                   | 同分类下唯一对象名                 |
| `props_name`                | str                   | 所属属性集名称（必须为某个 group 的 `group_props_name`） |
| `description`               | str                   | 用户可见标签                       |
| `long_description`          | str                   | 帮助文本                           |
| `widget_variant`            | Enum                  | 具体变体（如 INT_SLIDER）          |
| `modified_callback_enabled` | bool                  | 是否启用修改回调                   |
| `modified_callback`         | Callable              | 值变化时回调函数                   |
| `visible`                   | bool                  | 可见性（可动态绑定）               |
| `enabled`                   | bool                  | 是否灰显（可动态绑定）             |
| `props` / `obj`             | Any (OBS 内部对象)    | 运行时由框架设置，用户不应修改     |

**专用控件特有属性**（摘录）：
- **DigitalBoxData**：`digital`（当前值）、`min_val`、`max_val`、`step`、`suffix`  
- **ComboBoxData**：`items`（`[{"label":..., "value":...}]`）、`label`、`value`  
- **GroupData**：`group_props_name`（子控件引用名）、`checked`（可勾选分组状态）、`folding_visible` 等折叠相关  
- **ColorBoxData**：`color_alpha/red/green/blue` 分量，以及 `color_value` 属性  
- **FontBoxData**：`font_face`、`font_size`、`font_style`、`font_bold` 等标志位

### 3.2 控件管理器（`obsScriptControlDataFramework.ControlManager`）

单例模式，通过 `get_control_manager()` 获取。

#### 主要方法
```python
# 创建控件（通常由框架调用，用户一般不需要直接调用）
cm.create_widget(category: WidgetCategory, control_name: str, object_name: str, **kwargs) -> ControlBaseData

# 按分类管理器访问（推荐）
cm.checkbox.add(control_name="my_check", object_name="my_check", description="Test", props_name="props")

# 获取指定控件
w = cm.get_widget_by_control_name("my_check")

# 获取所有控件（按 load_order 排序）
widgets = cm.get_widgets_by_load_order()

# 获取 props_name 到 control_name 列表的映射
mapping = cm.get_props_mapping()

# 获取基础分组控件
basic_group = cm.get_basic_group()   # 其 group_props_name 为 "props"
```

#### 分类管理器（如 `cm.checkbox`）提供的方法
- `add(control_name, object_name=None, **kwargs)`：添加控件，`kwargs` 对应数据类属性。  
- `__getattr__(object_name)`：通过 `object_name` 获取控件对象。  
- `__contains__`、`__iter__` 等。

### 3.3 UI 更新器（`obsScriptControlUiUpdaterFramework.UIUpdater`）

```python
updater = UIUpdater(script_settings, control_manager, log_manager)
updater.update(update_widget_for_props_dict: Dict[str, List[str]]) -> bool
```
- `update_widget_for_props_dict`：指定需要更新的控件（如 `{"props": ["check1", "slider1"]}`）。  
- 内部会根据控件的 `visible`、`enabled`、`digital`、`text` 等属性刷新 OBS 界面。

### 3.4 日志管理器（`LogManager`）

```python
log = LogManager(log_dir="path/to/logs", log_num_max=100, word_max=100000)
log.log_info(msg)
log.log_warning(msg)
log.log_error(msg)
log.log_exception(e, context="...")
log.flush()   # 强制保存缓存日志到文件
```

### 3.5 常用数据管理器（`CommonDataManager`）

```python
data_mgr = CommonDataManager(filepath="path/to/config.json")
# 存储
data_mgr.add_data(user_id="system", data_type="group_folded_props_names", item="audio_props", maximum=999)
# 读取
folded = data_mgr.get_data("system", "group_folded_props_names")
# 删除
data_mgr.remove_data("system", "group_folded_props_names", "audio_props")
```

### 3.6 用户回调编写规范

#### 按钮回调（在 `plugins/ButtonFunction.py` 中）
```python
class BtnFunction(metaclass=AliasMeta):
    def __init__(self, Log_manager, sys_c_d_m, control_manager, control_ui_updater_manager):
        self.Log_manager = Log_manager
        self.sys_c_d_m = sys_c_d_m
        self.control_manager = control_manager
        self.control_ui_updater_manager = control_ui_updater_manager

    def my_button_clicked(self, control_name: str, *args, **kwargs):
        self.Log_manager.log_info(f"Button {control_name} clicked")
        # 可以修改其他控件的属性，然后强制刷新 UI
        target = self.control_manager.get_widget_by_control_name("some_check")
        target.checked = not target.checked
        self.control_ui_updater_manager.update({"props": ["some_check"]})
        return True
```

#### 控件修改回调（在 `plugins/ControlFunction.py` 中）
```python
class ControlDataSetFunction(ClearableCache, metaclass=AliasMeta):
    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def my_modified_callback(control_name: str, *args, **kwargs):
        # 可返回 True/False 表示允许修改；或直接执行逻辑
        print(f"Control {control_name} changed")
        return True
```

#### 自由属性计算（同样在 `ControlDataSetFunction` 中）
```python
@staticmethod
@lru_cache(maxsize=None)
@add_clear_cache
def dynamic_visible(control_name: str):
    # 根据其他控件状态返回 True/False
    return obs.obs_data_get_bool(obs.obs_get_current_scene_as_source(), "some_flag")
```
然后在 CSV 中将目标控件的 `visible` 列设为 `dynamic_visible`。

### 3.7 CSV 文件格式要点

- `widgetAttributeDefinitionData.csv`：定义每个控件类型有哪些属性字段，以及哪些是必填（`O`）、可选（`X`）。  
- `widgetData.csv`：具体控件实例。  
  - 第一行必须与属性定义文件的列头一致。  
  - 使用 `→` 前缀表示缩进层级，表示父子关系。  
  - 分组框的 `group_props_name` 会创建新的属性集，其内部控件的 `props_name` 需指向该名称。  
  - 自由属性列（通常位于第三、四组）中填入函数名，框架会在 `apply_user_properties` 时调用。

### 3.8 内置特殊控件

- **允许执行控件修改回调**按钮（`control_name = "e58581e8aeb8e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"`）：开启回调执行。  
- **禁止执行控件修改回调**按钮（`control_name = "e7a681e6ada2e689a7e8a18ce68ea7e4bbb6e4bfaee694b9e59b9ee8b083"`）：临时禁止修改回调，用于调试。

### 3.9 常见陷阱及解决

- **修改回调不触发**：检查 CSV 中 `modified_callback_enabled` 是否为 `true`，且 `modified_callback` 列的函数名在 `BtnFunction` 中存在。同时确认“允许执行控件修改回调”按钮处于开启状态。  
- **控件可见性未刷新**：调用 `UIUpdater.update()` 并传入包含该控件 `props_name` 的字典。  
- **分组框折叠状态未保存**：框架自动将折叠状态存入 `sys_common_config.json`，无需手动处理。  
- **导入错误**：若直接运行测试代码，需将 `obsScriptFramework_` 所在目录加入 `sys.path`，或使用相对导入。生产环境（OBS 内）已处理。

---

> 以上文档基于 `obsScriptFramework.py` 及附属模块编写，版本对应为 `1.0.0`。如有框架更新，请以源码为准。