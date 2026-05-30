以下是针对您的 **OBS Python 脚本快速开发框架** 的开发者文档。该文档面向希望使用此框架创建 OBS 脚本的开发者，涵盖了框架设计、核心组件、使用方法和扩展指南。

---

# OBS Python 脚本快速开发框架 —— 开发者文档

## 1. 框架概述

**obs-python-framework** 是一个用于快速开发 OBS Studio Python 脚本的声明式框架。  
开发者只需编辑 CSV 文件定义控件（复选框、数字框、按钮、分组等），并实现少量业务回调函数，即可自动生成完整的脚本设置界面，并自动处理 UI 状态同步、回调注册、折叠分组等复杂逻辑。

### 1.1 核心特性
- **声明式 UI**：通过 `widgetData.csv` 定义控件，无需手写 `obs.obs_properties_add_xxx`。
- **分层属性管理**：支持 `props_name`（属性集）和 `group_props_name`（分组集），实现控件嵌套与折叠。
- **两种属性填充方式**：
  - **天赋属性**：直接从 CSV 静态列读取（如 `min_val`, `max_val`）。
  - **自由属性**：通过回调函数动态计算（如从配置文件读取、依赖其他控件状态）。
- **回调系统**：统一管理控件值修改回调、按钮点击回调和 OBS 前端事件回调。
- **自动 UI 同步**：`UIUpdater` 自动将内存中控件的 `visible`、`enabled`、`value` 等状态同步到 OBS 界面。
- **折叠分组框**：支持可勾选分组框，子控件自动跟随折叠/展开，状态持久化。

### 1.2 适用场景
- 需要为 OBS 脚本提供复杂设置面板的开发者。
- 希望避免重复编写大量 OBS API 调用代码的开发者。
- 需要动态 UI（如根据复选框显示/隐藏一组控件）且希望逻辑集中在配置中的项目。

---

## 2. 项目结构

```
obs-python-framework/
├── obsScriptFramework_.py          # 框架主入口脚本（需放在 OBS 脚本目录）
├── plugins/                         # 用户业务代码目录
│   ├── ButtonFunction.py            # 按钮点击和控件变动回调实现
│   ├── ControlFunction.py           # 自由属性值获取函数
│   └── tool/                        # 辅助工具（如别名装饰器）
├── src/                             # 框架核心代码
│   ├── data/                        # 数据结构定义
│   │   ├── obsScriptControlData.py  # 控件数据类（CheckBoxData 等）
│   │   ├── obsScriptGlobalVariable.py # 全局变量（将被重构）
│   │   └── ExplanatoryDictionary.py  # 枚举与说明字典
│   ├── framework/                   # 核心功能模块
│   │   ├── obsScriptControlDataFramework.py        # ControlManager 控件管理器
│   │   ├── obsScriptControlInnatePropertyBuildFramework.py  # 天赋属性构建
│   │   ├── obsScriptControlFreePropertyBuildFramework.py   # 自由属性拉取
│   │   ├── obsScriptControlUiUpdaterFramework.py   # UIUpdater 界面同步
│   │   ├── obsScriptModifiedFunctionFramework.py   # ModifiedFunction 回调管理
│   │   ├── obsSciptButtonFunctionFramework.py      # 按钮回调包装
│   │   └── obsTriggerFrontendEventFramework.py     # 前端事件触发
│   └── tool/                        # 工具类
│       ├── LogManager.py            # 日志管理器
│       ├── CommonDataManager.py     # 常用数据持久化（用于折叠状态等）
│       └── scriptCsv2Json.py        # CSV 解析器（将 CSV 转为内部数据结构）
├── doc/                             # 文档（控件属性详细说明）
├── LOG/                             # 运行时日志输出目录
└── 配置文件（在脚本加载时自动生成）
```

---

## 3. 快速开始

### 3.1 安装与配置
1. 将整个 `obsScriptFramework_.py` 及同目录文件放入 OBS 的脚本目录（通常为 `C:\ProgramData\obs-studio\basic\scripts\` 或通过 OBS 脚本对话框添加）。
2. 修改 `plugins/ButtonFunction.py` 和 `plugins/ControlFunction.py` 实现自己的逻辑。
3. 编辑 `widgetData.csv` 定义所需的控件。
4. 在 OBS 中加载脚本，界面将自动生成。

### 3.2 第一个脚本示例

**步骤 1：定义控件（widgetData.csv）**

```csv
object_name,widget_category,|,control_name,description,long_description,widget_variant,modified_callback_enabled,modified_callback,||,suffix,callback,filter_str,default_path,group_props_name,|,visible,enabled,||,url,checked,min_val,max_val,step,digital,info_type,text,label,value,items,color_alpha,color_red,color_green,color_blue,font_face,font_size,font_style,font_bold,font_italic,font_underline,font_strikeout,path_text,|,load_order,props,obj,||,group_props,folding_control_obj,folding_visible,folding_enabled,color_value,font_data,font_flags
my_checkbox,CHECKBOX,|,enable_feature,启用高级功能,,,true,on_checkbox_changed,,,,,,,,,,default_true,default_true,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
my_button,BUTTON,|,exec_action,执行动作,,DEFAULT,false,,,X,on_button_click,,,,,,default_true,default_true,,,,url_reference_data,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

**步骤 2：实现回调函数（plugins/ButtonFunction.py）**

```python
from .tool.addAliases import add_aliases

class BtnFunction:
    def __init__(self, Log_manager, sys_c_d_m, control_manager, control_ui_updater_manager):
        self.Log_manager = Log_manager
        # 其他管理器可存储供后续使用

    @add_aliases("on_checkbox_changed")
    def checkbox_changed(self, control_name=None, **kwargs):
        self.Log_manager.log_info(f"复选框 {control_name} 状态已改变")
        # 可根据新值修改其他控件的可见性
        return True

    @add_aliases("on_button_click")
    def button_clicked(self, *args, **kwargs):
        self.Log_manager.log_info("按钮被点击")
        # 执行实际动作，如启动推流
        return True
```

**步骤 3：运行脚本**  
在 OBS 中加载脚本，即可看到复选框和按钮，点击按钮或修改复选框时会触发相应日志。

---

## 4. 核心组件详解

### 4.1 `ControlManager` —— 控件管理器

负责控件的创建、存储、唯一性验证和分组管理。

**主要方法：**
- `create_widget(category, control_name, object_name, **kwargs)` – 创建控件并加入管理。
- `get_widget_by_control_name(control_name)` – 通过唯一标识获取控件对象。
- `get_widgets_by_load_order()` – 返回按 `load_order` 排序的控件列表（用于 UI 生成）。
- `get_props_mapping()` – 返回 `{props_name: [control_name, ...]}` 字典，用于批量更新。
- `get_basic_group()` – 获取根分组控件（`group_props_name="props"`）。

**重要属性：**
- `_basic_group`：基础分组框，所有顶层控件的 `props_name` 默认为 `"props"`。
- `_group_props_names`：所有 `group_props_name` 的集合，用于验证 `props_name` 的合法性。

**使用示例（在框架内部自动调用）：**
```python
# 添加一个复选框，它属于 "props" 属性集
cm.checkbox.add(
    control_name="enable_feature",
    object_name="cb_enable",
    description="启用功能",
    checked=True,
    props_name="props"
)
```

### 4.2 `UIUpdater` —— 界面同步器

将控件模型（`ControlBaseData` 及其子类）的状态同步到 OBS 原生控件。

**核心方法：**
- `update(update_widget_for_props_dict)` – 接收 `{props_name: [control_names]}` 字典，仅更新指定的控件。

**工作原理：**
- 遍历需要更新的控件，根据控件类型调用对应的 `_update_xxx` 方法（如 `_update_checkbox`）。
- 这些方法会对比当前 OBS 中的值与模型中的值，如有变化则调用 `obs.obs_data_set_xxx` 写回设置。
- 同时更新 `visible` 和 `enabled` 状态（调用 `obs.obs_property_set_visible/enabled`）。

**开发者注意事项：**
- 不要在 `script_update` 或 `script_tick` 中直接修改控件的 `visible`/`enabled`，应修改模型后调用 `UIUpdater.update`。
- 折叠分组框的折叠状态通过 `CommonDataManager` 持久化，`UIUpdater` 会自动处理。

### 4.3 CSV 解析器 —— `ControlTemplateParser`

将两个 CSV 文件（属性定义 `widgetAttributeDefinitionData.csv` 和控件数据 `widgetData.csv`）转换为内部数据结构。

**核心方法：**
- `parse_csv_files(attribute_def_path, data_path, initial_props_name)`  
  返回字典，包含：
  - `all_controls`：所有控件的扁平列表。
  - `tree`：按缩进（`→`）组织的树形结构。
  - `templates`：每种控件类型支持的字段映射。

**缩进规则：**
- 使用 `→` 字符（U+2192）表示子控件，每多一个箭头表示深一级嵌套。
- 子控件的 `props_name` 会自动继承最近上层分组框的 `group_props_name`（如果存在）。

**字段分组：**
- CSV 标题行中的 `|` 和 `||` 用于分隔属性组。
  - 第一组（group_1）：基础属性（`control_name`、`description` 等）。
  - 第二组（group_2）：可选属性（如 `suffix`、`url`）。
  - 第三组（group_3）：动态自由属性（如 `checked` 列指向一个回调函数名）。
  - 第四组（group_4）：扩展自由属性。

### 4.4 回调系统

#### 4.4.1 按钮回调
- 在 CSV 中为按钮指定 `callback` 列（值为函数名）。
- 框架在 `obsScriptButtonFunctionFramework.py` 中包装，调用 `BtnFunction` 中对应的方法。
- 方法应接受 `(ps, p)` 参数，并返回 `True`。

#### 4.4.2 控件变动回调
- 在 CSV 中设置 `modified_callback_enabled` 为 `true`，`modified_callback` 列填写函数名。
- 框架在 `obsScriptModifiedFunctionFramework.py` 中统一管理执行许可（`allow_execution` 标志）。
- 回调函数定义在 `BtnFunction` 中，形式为：
  ```python
  def my_modified_callback(control_name=None, **kwargs):
      # 根据新值调整其他控件
      return True  # 或 False 阻止进一步传播
  ```

#### 4.4.3 自由属性获取函数
- 定义在 `ControlFunction` 类中，使用 `@lru_cache` 和 `@add_clear_cache` 装饰器。
- 函数名在 CSV 的 group_3/group_4 的列中指定，返回对应属性值。
- 例如：`checked_reference_data` 返回 `True/False`，`min_val_reference_data` 返回数值。

### 4.5 日志管理器 —— `LogManager`

提供带文件持久化的日志记录，自动按日期分割、限制文件数量。

**主要方法：**
- `log_info`, `log_warning`, `log_error`, `log_debug` – 记录到 OBS 日志并缓存。
- `flush()` – 强制将缓存写入文件。
- `log_exception(exception, context)` – 记录异常堆栈。

**配置：**  
在 `script_defaults` 中创建实例时指定日志目录和最大文件数。

---

## 5. 高级用法

### 5.1 创建折叠分组框

在 `widgetData.csv` 中定义 `widget_category=GROUP`，`widget_variant=CHECKABLE`，并指定唯一的 `group_props_name`。  
其子控件（缩进多一级）的 `props_name` 会自动指向该 `group_props_name`。

**示例：**
```csv
my_group,GROUP,|,audio_group,音频设置,,CHECKABLE,true,,,X,,,,,audio_props,|,default_true,default_true,|,X,checked_reference_data,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
→volume,DIGITALBOX,|,volume_level,音量,,INT_SLIDER,true,,,dB,,,,,,,|,default_true,default_true,|,X,,0,100,1,50,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

### 5.2 动态更新控件属性（自由属性）

在 CSV 的 group_3 或 group_4 列中填写函数名（如 `min_val: get_dynamic_min`），然后在 `ControlFunction` 中实现该函数：

```python
@lru_cache(maxsize=None)
@add_clear_cache
def get_dynamic_min(self, control_name=None, **kwargs):
    # 可以从配置文件、其他控件值等计算
    return 10
```

当脚本加载时，`apply_user_properties` 会调用该函数并将返回值设置到控件的 `min_val` 属性上。

**注意：** 自由属性只在脚本加载时拉取一次。如需运行时动态修改，应使用控件变动回调配合 `UIUpdater`。

### 5.3 监听 OBS 前端事件

在 `TriggerFrontendEvent` 中注册了回调，事件发生时会调用 `BtnFunction` 中与事件同名的方法。  
例如，要监听推流开始事件，在 `BtnFunction` 中实现：

```python
def STREAMING_STARTED(self, **kwargs):
    self.Log_manager.log_info("推流已开始")
    # 执行自定义动作
```

### 5.4 跨脚本数据共享

使用 `CommonDataManager` 存储用户常用数据（如历史标题、分类）。  
在框架中已用于存储折叠分组的状态（`system` 用户的 `group_folded_props_names`）。  
您可以扩展使用：

```python
# 保存用户最近输入
self.common_data_manager.add_data(user_id, "recent_texts", text, maximum=10)
# 读取
recent_list = self.common_data_manager.get_data(user_id, "recent_texts")
```

---

## 6. 常见问题与最佳实践

### Q1：控件没有显示出来？
- 检查 CSV 中 `widget_category` 是否为枚举值（如 `CHECKBOX` 大写）。
- 确认 `props_name` 有效（默认 `"props"` 存在，或已定义分组框）。
- 查看 OBS 日志（帮助 → 日志文件）是否有 `ValueError`。

### Q2：折叠分组框的子控件不隐藏？
- 确保子控件的 `props_name` 等于父分组的 `group_props_name`。
- 检查 `sys_common_config.json` 中 `system.group_folded_props_names` 列表是否正确更新。

### Q3：修改控件值后回调未执行？
- 确认 CSV 中 `modified_callback_enabled` 为 `true`，且 `modified_callback` 列填了正确的函数名。
- 检查 `ModifiedFunction.allow_execution` 是否为 `True`（可通过专用按钮控制）。

### Q4：如何调试？
- 使用 `LogManager.log_debug` 记录详细信息。
- 在 `ControlFunction` 中可临时关闭 `@lru_cache` 以便观察动态值变化。
- OBS 的脚本日志窗口会显示 `INFO` 级别以上日志。

### 最佳实践
1. **控件命名**：使用有意义的英文名称，避免特殊字符或中文（防止 hex 编码）。
2. **分组深度**：不超过 3 层，否则 UI 嵌套过深。
3. **自由属性函数**：尽量保持幂等，避免副作用。如需全局状态，使用 `CommonDataManager`。
4. **性能**：避免在 `property_modified` 回调中执行耗时操作（如网络请求），可启动后台线程但需注意 OBS API 只能在主线程调用。
5. **版本管理**：在 `ObsScriptGlobalData.version` 中设置脚本版本，便于用户更新。

---

## 7. 扩展指南

### 7.1 添加新的控件类型（如日期选择器）

1. 在 `obsScriptControlData.py` 中：
   - 为 `WidgetCategory` 添加新枚举项（如 `DATEPICKER`）。
   - 创建新的 `DatePickerData` 类，继承 `ControlBaseData`。
2. 在 `ControlManager._get_widget_class` 中添加映射。
3. 在 `UIUpdater` 中添加 `_update_datepicker` 方法，实现与 OBS 控件的同步。
4. 在 `script_properties` 中添加创建该控件的分支（调用 `obs.obs_properties_add_...`）。
5. 更新 `widgetAttributeDefinitionData.csv`，增加对应的列定义（`O`/`X`）。

### 7.2 修改 CSV 格式

- 属性定义文件决定了每列的含义。若需增加新的内置属性（如 `placeholder`），需：
  - 在 `obsScriptControlData.py` 的对应数据类中添加属性。
  - 在 `build_controls` 中将其从 CSV 传递到数据对象。
  - 在 `UIUpdater` 中实现同步逻辑（如果需要从界面读取）。

### 7.3 集成外部库

由于 OBS Python 环境受限，建议将依赖库打包到脚本目录或使用 `sys.path.insert` 导入。注意不要与 OBS 内置 Python 库冲突。

---

## 8. 附录

### 8.1 控件属性 CSV 列参考

| 列名 | 适用控件 | 说明 |
|------|----------|------|
| `control_name` | 所有 | 唯一标识（内部使用） |
| `object_name` | 所有 | UI 对象名（同一分类下唯一） |
| `description` | 所有 | 显示标签 |
| `widget_variant` | 所有 | 具体变体（如 `INT_SLIDER`） |
| `modified_callback_enabled` | 所有 | 是否启用变动回调 |
| `modified_callback` | 所有 | 回调函数名（在 `BtnFunction` 中） |
| `checked` | CHECKBOX, GROUP(CHECKABLE) | 是否勾选 |
| `min_val`, `max_val`, `step`, `digital`, `suffix` | DIGITALBOX | 数值范围及步长 |
| `text`, `info_type` | TEXTBOX(INFO) | 只读文本及类型 |
| `url` | BUTTON(URL) | 跳转链接 |
| `label`, `value`, `items` | COMBOBOX | 选项列表 |
| `path_text`, `filter_str`, `default_path` | PATHBOX | 路径选择 |
| `group_props_name` | GROUP | 子控件的 `props_name` 值 |

### 8.2 依赖项
- OBS Studio 28.0 或更高版本（Python 3.9+ 内嵌环境）。
- Python 标准库（无外部依赖）。

### 8.3 许可与贡献
本框架为开放源代码，您可以在遵守 OBS 项目许可的前提下自由使用和修改。欢迎提交 issue 和 PR。

---

**文档版本**: 1.0  
**最后更新**: 2026-05-30  
**维护者**: 框架作者