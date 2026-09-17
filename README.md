# OBS Script Framework

一套面向**OBS Studio**的 Python 脚本开发框架，配套一个**PySide6 图形化编辑器**，用于可视化地维护脚本界面（CSV 声明式控件）。

- **框架侧**：让 OBS 脚本用 CSV 描述控件树，运行时自动生成属性页、绑定回调、动态计算属性。
- **编辑器侧**：不用手改 CSV，用树形视图 + 属性面板 + 实时预览可视化地维护控件。

---

## 目录

1. 快速开始
2. 目录结构
3. 编辑器使用说明
4. 框架使用说明
5. 开发者文档
6. 打包与部署
7. 常见问题

---

## 一、快速开始

### 1.1 环境准备

- **OBS Studio**：28.0 以上，启用 Python 脚本支持。
- **Python**：推荐 3.9 / 3.10 / 3.11。
- **编辑器依赖**：`PySide6-Essentials`（开发时），PyInstaller（打包时）。

```
# 开发环境
python -m venv .venv
.venv\Scripts\activate
pip install PySide6-Essentials pytest

# 打包环境（可选）
pip install pyinstaller
```

### 1.2 两种运行方式

**方式 A：使用打包好的编辑器（推荐给最终用户）**

解压`OBS脚本编辑器.zip`，双击：

- `OBS脚本编辑器_silent.exe`—**无控制台**，日常使用
- `OBS脚本编辑器.exe`—**带控制台**，排查问题

**方式 B：源码运行（推荐给开发者）**

```
python -m editor.main
```

### 1.3 修改控件

1. 启动编辑器。
2. 左侧树选中控件 → 右侧属性面板修改字段。
3. 中间预览区实时反映修改结果。
4. 点工具栏「保存」写回`obsScriptFramework_/plugins/widgetData.csv`。
5. 在 OBS 中重新加载脚本即可看到新界面。

### 1.4 加载脚本到 OBS

1. 把整个`obsScriptFramework_`目录放到 OBS 脚本目录（`工具 → 脚本 → 打开脚本目录`）。
2. 把`obsScriptFramework.py`放在`obsScriptFramework_`的**同级目录**。
3. OBS 中：`工具 → 脚本 → +`→ 选择`obsScriptFramework.py`。
4. 属性页显示 CSV 中定义的所有控件。

---

## 二、目录结构

```
obs-python-framework/
│
├── obsScriptFramework.py              # OBS 脚本入口（加载到 OBS 用）
├── obsScriptFramework_/               # 框架主体
│   ├── src/
│   │   ├── data/                      # 数据定义
│   │   │   ├── obsScriptControlData.py
│   │   │   ├── obsScriptGlobalVariable.py
│   │   │   ├── ExplanatoryDictionary.py
│   │   │   └── widgetAttributeDefinitionData.csv
│   │   ├── tool/                      # 工具类
│   │   │   ├── LogManager.py
│   │   │   ├── CommonDataManager.py
│   │   │   └── scriptCsv2Json.py
│   │   └── framework/                 # 核心框架
│   │       ├── obsScriptControlDataFramework.py
│   │       ├── obsScriptControlInnatePropertyBuildFramework.py
│   │       ├── obsScriptControlFreePropertyBuildFramework.py
│   │       ├── obsSciptButtonFunctionFramework.py
│   │       ├── obsScriptModifiedFunctionFramework.py
│   │       ├── obsTriggerFrontendEventFramework.py
│   │       ├── obsScriptControlUiUpdaterFramework.py
│   │       └── groupFoldHandler.py
│   └── plugins/                       # 用户扩展目录（编辑器编辑的目标）
│       ├── widgetData.csv             # 控件定义
│       ├── ButtonFunction.py          # 按钮回调
│       ├── ControlFunction.py         # 属性回调
│       ├── GlobalVariable.py          # 用户全局变量
│       └── obsScriptDescription.html  # 脚本介绍
│
├── editor/                            # 编辑器源码
│   ├── main.py                        # 源码入口
│   ├── _bootstrap.py                  # 路径与 mock 引导
│   ├── logging_config.py
│   ├── settings_manager.py
│   ├── session_manager.py
│   ├── model/                         # 数据层（不依赖 Qt）
│   │   ├── widget_node.py
│   │   ├── widget_tree.py
│   │   ├── csv_io.py
│   │   ├── validator.py
│   │   ├── diff.py
│   │   ├── props_utils.py
│   │   ├── function_editor.py
│   │   ├── function_registry.py
│   │   ├── template_generator.py
│   │   ├── value_resolver.py
│   │   └── variant_registry.py
│   ├── ui/                            # UI 层（PySide6）
│   │   ├── main_window.py
│   │   ├── tree_panel.py
│   │   ├── preview_panel.py
│   │   ├── property_panel.py
│   │   ├── commands.py
│   │   ├── collapsible_section.py
│   │   ├── diff_dialog.py
│   │   ├── export_dialog.py
│   │   ├── function_editor_dialog.py
│   │   ├── new_node_dialog.py
│   │   ├── settings_dialog.py
│   │   └── style_utils.py
│   └── tests/                         # 编辑器单元测试
│
├── editor_main.py                     # 打包入口
├── editor_debug.spec                  # PyInstaller spec（带控制台）
├── editor_silent.spec                 # PyInstaller spec（无控制台）
├── build.bat                          # 一键构建脚本
├── README.md
├── LICENSE
│
└── dist/                              # 打包输出（构建后生成）
    ├── OBS脚本编辑器.exe
    ├── OBS脚本编辑器_silent.exe
    ├── obsScriptFramework_/
    ├── README.txt
    └── OBS脚本编辑器.zip
```

---

## 三、编辑器使用说明

### 3.1 界面布局

```
┌─────────────┬─────────────┬─────────────────────┐
│  控件树     │  OBS 预览   │  属性面板           │
│  (QTreeView)│  (预览模拟) │  (动态表单)         │
│             │             │                     │
│  ● 内置按钮 │  [✓] 复选框 │  control_name: ...  │
│  ▸ 分组框   │  [ ] 数字框 │  description: ...   │
│  ● 控件1    │  [ ] 按钮   │  自由属性: ...      │
│  ● 控件2    │             │                     │
└─────────────┴─────────────┴─────────────────────┘
```

- **左栏**：控件树。绿色节点正常，红色/黄色表示校验错误/警告。
- **中栏**：模拟 OBS 属性页，点击任意控件 → 左右两栏同步选中。
- **右栏**：属性面板，按当前控件类型动态显示字段。

### 3.2 常用操作

| 操作 | 快捷键 / 方式 |
| --- | --- |
| 新建控件 | 工具栏「新建控件」；右键菜单；插入到选中节点之后 |
| 新建子控件 | 右键分组框 → 「新建子控件」 |
| 删除控件 | Delete 前先选中；工具栏「删除选中」 |
| 上移 / 下移 | 工具栏；右键菜单 |
| 拖拽排序 | 直接拖动节点（不能越过内置按钮） |
| 撤销 / 重做 | Ctrl+Z / Ctrl+Y |
| 搜索字段 | 属性面板顶部搜索框，匹配字段名 / 标签 / 值 |
| 打开日志目录 | 工具栏按钮 |
| 打开设置 | 工具栏「设置...」 |

### 3.3 属性面板

每个控件显示两组可折叠区域：

- **结构化字段**：`control_name`、`object_name`、`props_name`、`description`、`widget_variant`等
- **自由属性**：来自 CSV 第 3/4 组的动态属性，如`visible`、`enabled`、`items`、`checked`、`digital`等

**函数名字段**（如`checked`、`modified_callback`）以可编辑下拉框显示，候选来自`ControlFunction.py`/`ButtonFunction.py`。

字段右侧有一个`{}`按钮：

- 点击 → 打开函数编辑器，直接编辑该函数的源码（不离开编辑器）
- 函数不存在时 → 询问是否创建
- 函数编辑器内可删除函数，删除后所有引用自动清空

### 3.4 预览面板

- **实时反映**控件树中每个控件的外观。
- **点击任意控件**→ 树里同步选中，属性面板加载。
- **`visible=False`**的控件用**红色虚线框**标识（不隐藏）。
- **`enabled=False`**的控件用**灰色背景**标识。
- **`visible=False & enabled=False`**用**粗红虚线 + 灰底**。
- **鼠标悬停**显示`long_description`。
- **组合框**可下拉、**列表框**可滚动，同时不影响「点击选中」。
- 「刷新数值」按钮重新解析所有回调函数的返回值。

### 3.5 校验与提示

状态栏右下角显示`⚠ N 错误 / M 警告（点击查看）`。

- 点击 → 弹出错误列表，双击可跳转到对应节点
- 树节点标色：红色 = 错误，黄色 = 警告，默认 = 无问题

### 3.6 设置与主题

`工具栏 → 设置...`：

- **主题**：浅色 / 深色 / 自定义
- **字体**：字体系列、字号（可打开系统字体对话框）
- **颜色**：前景、背景、强调色、输入框、树、属性面板、预览标签等 10 项

配置保存在项目根目录`editor_settings.json`。

### 3.7 最近文件与路径记忆

- 工具栏「最近文件」下拉，保存最近 10 个打开过的 CSV
- 自动记忆上次打开的目录，作为文件对话框初始位置
- 折叠面板状态也持久化
- 打包后（exe 模式）**忽略会话路径**，强制加载 exe 同目录的`obsScriptFramework_`

### 3.8 导出脚本模板

`工具栏 → 导出脚本模板`：

- 从当前控件树反向生成`ButtonFunction.py`、`ControlFunction.py`、`GlobalVariable.py`
- 自动提取 CSV 中引用到的所有函数名，生成空实现
- 预览每个文件的内容，确认后导出到指定目录
- 已存在同名文件时提示覆盖

---

## 四、框架使用说明

### 4.1 设计目标

- **声明式 UI**：CSV 描述控件树，无需手写`obs_properties_add_xxx`
- **动态属性绑定**：控件属性可绑定到 Python 函数，运行时动态计算
- **回调统一管理**：按钮点击、控件修改、前端事件都走统一分发器
- **状态持久化**：折叠状态等通过`CommonDataManager`自动保存

### 4.2 脚本生命周期

| 钩子 | 作用 |
| --- | --- |
| script_defaults | 初始化管理器、解析 CSV、构建控件树、绑定回调、应用自由属性 |
| script_properties | 创建 obs_properties_t 并返回根属性集 |
| script_load | 注册前端事件回调 |
| script_update | 用户修改设置时触发（预留） |
| script_unload | 刷新日志缓存 |

### 4.3 控件构建流程

1. `ControlTemplateParser.parse_csv_files()`读取模板 CSV + 数据 CSV，生成控件树字典
2. `build_controls()`遍历树，创建控件数据对象，绑定回调
3. `apply_user_properties()`根据自由属性映射调用`ControlDataSetFunction`计算实际值
4. `UIUpdater.update()`同步状态到 OBS 界面

### 4.4 回调分发

| 触发源 | 分发路径 |
| --- | --- |
| 按钮点击 | ObsScriptButtonFunction.select(name) → BtnFunction.name() |
| 控件修改 | ModifiedFunction.property_modified(name, fn) → BtnFunction.fn(control_name=...) |
| 前端事件 | TriggerFrontendEvent.event_callback() → BtnFunction.<EVENT_NAME>() |

### 4.5 内置控件

框架在运行时动态创建两个内置按钮：

| control_name | 描述 |
| --- | --- |
| e58581e8... | 允许执行控件修改回调 |
| e7a681e6... | 禁止执行控件修改回调 |

这两个按钮**不在 CSV 中**（编辑器会自动注入显示），`visible=False, enabled=False`。

---

## 五、开发者文档

### 5.1 控件数据类

所有控件类继承`ControlBaseData`：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| control_name | str | 全局唯一标识符 |
| object_name | str | 同分类下唯一对象名 |
| props_name | str | 所属属性集（来自某个 group 的 group_props_name） |
| description | str | 用户可见标签 |
| long_description | str | 帮助文本 |
| widget_variant | Enum | 具体变体（如 INT_SLIDER） |
| modified_callback_enabled | bool | 是否启用修改回调 |
| modified_callback | Callable | 值变化回调 |
| visible / enabled | bool | 可动态绑定 |
| props / obj | Any | OBS 内部对象，运行时由框架设置 |

**专用字段**：

- `DigitalBoxData`：`digital`、`min_val`、`max_val`、`step`、`suffix`
- `ComboBoxData`：`items`、`label`、`value`
- `GroupData`：`group_props_name`、`checked`、`folding_visible`
- `ColorBoxData`：`color_alpha/red/green/blue`、`color_value`
- `FontBoxData`：`font_face`、`font_size`、`font_style`、`font_bold`等

### 5.2 控件管理器

```
from src.framework.obsScriptControlDataFramework import get_control_manager

cm = get_control_manager()

# 添加控件
cm.checkbox.add(
    control_name="my_check",
    object_name="my_check",
    description="测试",
    props_name="props",
)

# 查询
widget = cm.get_widget_by_control_name("my_check")
widgets = cm.get_widgets_by_load_order()
mapping = cm.get_props_mapping()
```

### 5.3 编写回调

**按钮回调**（`plugins/ButtonFunction.py`）：

```
class BtnFunction(metaclass=AliasMeta):
    def __init__(self, Log_manager, sys_c_d_m, control_manager, control_ui_updater_manager):
        ...

    def my_button_clicked(self, control_name: str, *args, **kwargs):
        self.Log_manager.log_info(f"按钮 {control_name} 被点击")
        target = self.control_manager.get_widget_by_control_name("some_check")
        target.checked = not target.checked
        self.control_ui_updater_manager.update({"props": ["some_check"]})
        return True
```

**控件修改回调 / 自由属性函数**（`plugins/ControlFunction.py`）：

```
class ControlDataSetFunction(ClearableCache, metaclass=AliasMeta):
    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def my_modified_callback(control_name: str, *args, **kwargs):
        print(f"控件 {control_name} 变化")
        return True

    @staticmethod
    @lru_cache(maxsize=None)
    @add_clear_cache
    def dynamic_visible(*args, **kwargs):
        # 返回 True/False 控制可见性
        return obs.obs_data_get_bool(...)
```

**前端事件回调**（`BtnFunction`里）：

```
def OBS_FRONTEND_EVENT_SCENE_CHANGED(self, *args, **kwargs):
    self.Log_manager.log_info("场景已切换")
```

### 5.4 CSV 格式要点

**`widgetAttributeDefinitionData.csv`**：定义每种控件类型的字段要求。

- `-`开头表示模板行
- `O`= 必填，`X`= 不适用，其他 = 可选

**`widgetData.csv`**：具体控件实例。

- 第一行必须与模板文件列头一致
- 用`→`前缀表示缩进层级
- 分组框的`group_props_name`创建新属性集，子控件的`props_name`指向它
- 自由属性列（第 3/4 组）填函数名

### 5.5 编辑器扩展点

| 想做什么 | 在哪改 |
| --- | --- |
| 新增控件类型 | WidgetCategory 枚举 + ControlBaseData 子类 + UIUpdater handler |
| 新增字段类型 | editor/ui/property_panel.py 的 _make_editor / _make_property_editor |
| 新增校验规则 | editor/model/validator.py |
| 新增右键菜单项 | editor/ui/tree_panel.py 的 _on_context_menu |
| 新增预览渲染 | editor/ui/preview_panel.py 的 _build_leaf |
| 新增主题色 | editor/settings_manager.py 的 EditorSettings |
| 新增命令 | editor/ui/commands.py |

---

## 六、打包与部署

### 6.1 构建

```
cd D:\Documents\PycharmProjects\obs-python-framework
.\build.bat
```

脚本自动完成：

1. 检查 / 安装 PyInstaller
2. 清理旧构建
3. 打包`OBS脚本编辑器.exe`（带控制台，调试用）
4. 打包`OBS脚本编辑器_silent.exe`（无控制台，正式用）
5. 复制`obsScriptFramework_`到`dist/`
6. 生成`README.txt`
7. 打 zip 包

### 6.2 交付物

```
dist/
├── OBS脚本编辑器.exe           # 带控制台
├── OBS脚本编辑器_silent.exe    # 无控制台
├── obsScriptFramework_/        # 框架目录
├── README.txt
└── OBS脚本编辑器.zip            # 最终发布包
```

### 6.3 部署给用户

1. 把`OBS脚本编辑器.zip`发给用户
2. 用户解压到任意可写目录
3. 双击`OBS脚本编辑器_silent.exe`

**注意**：

- 不要放在`C:\Program Files\`（无写权限）
- 需要写权限：`LOG/`、`editor_settings.json`、`obsScriptFramework_/`
- exe 通过`sys.executable`定位同目录的`obsScriptFramework_`

### 6.4 源码模式 vs exe 模式

| 项 | 源码模式 | exe 模式 |
| --- | --- | --- |
| 项目根 | editor/ 的父目录 | exe 所在目录 |
| CSV 路径 | 会话记录的路径 | 强制使用 exe 同目录的 obsScriptFramework_ |
| 日志 | 项目根/LOG/ | exe目录/LOG/ |
| 设置 | 项目根/editor_settings.json | exe目录/editor_settings.json |

---

## 七、常见问题

### 7.1 编辑器相关

**Q：点击`{}`按钮没有反应？**
A：检查：

1. 控制台/日志有没有`请求编辑函数:...`输出
2. 字段里是否填了函数名（空值会提示先填）
3. 函数名是否合法（只能字母、数字、下划线，不能数字开头）

**Q：属性面板看不到`visible`/`enabled`的值？**
A：内置按钮的这两个字段用文本`False`显示（因为只读），普通控件用下拉（函数名）。

**Q：预览里的控件怎么分不清`visible=False`和`enabled=False`？**
A：三种状态颜色不同：

- 仅`visible=False`：红色细虚线
- 仅`enabled=False`：灰色背景
- 两者都`False`：粗红虚线 + 灰底

**Q：编辑函数后 OBS 里没生效？**
A：编辑器保存的是源码文件，OBS 需要重新加载脚本（`工具 → 脚本 → 右键脚本 → 重新加载`）。

### 7.2 框架相关

**Q：修改回调不触发？**
A：

1. CSV 里`modified_callback_enabled`是否`true`
2. 函数名是否在`BtnFunction`中存在
3. 确认两个内置按钮的`allow_execution`状态（默认`True`）

**Q：控件可见性没刷新？**
A：调用`UIUpdater.update({"props_name": ["control_name"]})`。

**Q：分组框折叠状态没保存？**
A：框架自动保存到`sys_common_config.json`，无需手动。

**Q：导入错误`No module named 'src'`？**
A：确保`obsScriptFramework_`目录与入口文件同级，且`sys.path`包含它。

### 7.3 打包相关

**Q：exe 启动后找不到`obsScriptFramework_`？**
A：必须把 exe 和`obsScriptFramework_`放在同一目录。

**Q：exe 闪退没有报错？**
A：用`OBS脚本编辑器.exe`（带控制台版本）启动，能看到完整错误。

**Q：exe 体积太大？**
A：spec 里已经`excludes`排除了 QtWebEngine、QtQuick3D 等大模块。如果还嫌大，可以进一步排除`PySide6.QtNetwork`等编辑器没用的模块。

**Q：想改 exe 图标？**
A：在`editor_debug.spec`/`editor_silent.spec`的`EXE(...)`里加上：

```
icon="editor/icon.ico",
```

---

## 版本

- 框架版本：`1.0.0`
- 编辑器版本：与框架同步
- 支持 Python：3.9 / 3.10 / 3.11
- 支持 OBS：28.0 以上

---

> 如有问题或建议，请提交 Issue。