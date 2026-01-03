from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict as PyOrderedDict
from typing import Any, Union, Optional, Callable, List, Dict, Literal, TypeVar, OrderedDict, Set

import obspython as obs


# 控件分类
# ----------------------------------------------------------------------------------------------------------------
class WidgetCategory(Enum):
    """控件分类枚举，用于替代魔法字符串，确保类型安全。"""
    CHECKBOX = "CheckBox"
    """复选框"""
    DIGITALBOX = "DigitalBox"
    """数字框"""
    TEXTBOX = "TextBox"
    """文本框"""
    BUTTON = "Button"
    """按钮"""
    COMBOBOX = "ComboBox"
    """组合框"""
    PATHBOX = "PathBox"
    """路径选择框"""
    GROUP = "Group"
    """分组框"""
    COLORBOX = "ColorBox"
    """颜色选择框"""
    FONTBOX = "FontBox"
    """字体选择框"""
    LISTBOX = "ListBox"
    """列表框"""


# 控件类型
# ----------------------------------------------------------------------------------------------------------------
class CheckBoxVariant(Enum):
    """复选框 控件类型"""
    pass


class DigitalBoxVariant(Enum):
    """
    数字框 控件类型
    INT 表示整数数字框，
    FLOAT 表示浮点数数字框，
    INT_SLIDER 表示整数数字框带滑块，
    FLOAT_SLIDER 表示浮点数数字框带滑块，
    """
    INT = "Int"
    """整数"""
    FLOAT = "Float"
    """浮点数"""
    INT_SLIDER = "IntSlider"
    """整数带滑块"""
    FLOAT_SLIDER = "FloatSlider"
    """浮点数带滑块"""


class TextBoxVariant(Enum):
    """
    文本框 类型
    DEFAULT 表示单行文本框，
    PASSWORD 表示单行密码文本框，
    MULTILINE 表示多行文本框，
    INFO 表示不可编辑的只读文本框，效果类似于标签。
    """
    DEFAULT = obs.OBS_TEXT_DEFAULT
    """单行"""
    PASSWORD = obs.OBS_TEXT_PASSWORD
    """单行密码"""
    MULTILINE = obs.OBS_TEXT_MULTILINE
    """多行"""
    INFO = obs.OBS_TEXT_INFO
    """不可编辑"""


class TextBoxInfoVariant(Enum):
    """
    文本框信息类型
    NORMAL 表示正常信息，
    WARNING 表示警告信息，
    ERROR 表示错误信息
    """
    NORMAL = obs.OBS_TEXT_INFO_NORMAL
    """正常信息"""
    WARNING = obs.OBS_TEXT_INFO_WARNING
    """警告信息"""
    ERROR = obs.OBS_TEXT_INFO_ERROR
    """错误信息"""


class ButtonVariant(Enum):
    """
    按钮 类型
    DEFAULT 表示标准普通按钮，
    URL 表示可打开指定 URL 的链接按钮。
    """
    DEFAULT = obs.OBS_BUTTON_DEFAULT
    """普通"""
    URL = obs.OBS_BUTTON_URL
    """打开链接"""


class ComboBoxVariant(Enum):
    """
    组合框 类型
    EDITABLE 表示可编辑组合框，仅适用于字符串格式，用户可以输入自己的内容，
    LIST 表示不可编辑组合框
    """
    EDITABLE = obs.OBS_COMBO_TYPE_EDITABLE
    """可编辑"""
    LIST = obs.OBS_COMBO_TYPE_LIST
    """不可编辑"""


class ListBoxVariant(Enum):
    """
    列表框 类型
    STRINGS 表示字符串列表框，
    FILES 表示文件路径列表框，
    FILES_AND_URLS 表示文件路径和网址列表框。
    """
    STRINGS = obs.OBS_EDITABLE_LIST_TYPE_STRINGS
    """字符串"""
    FILES = obs.OBS_EDITABLE_LIST_TYPE_FILES
    """文件路径"""
    FILES_AND_URLS = obs.OBS_EDITABLE_LIST_TYPE_FILES_AND_URLS
    """文件路径和网址"""


class GroupVariant(Enum):
    """
    分组框 类型
    NORMAL 表示标准普通分组框，
    CHECKABLE 表示拥有复选框的分组框。
    """
    NORMAL = obs.OBS_GROUP_NORMAL
    """标准"""
    CHECKABLE = obs.OBS_GROUP_CHECKABLE
    """拥有复选框"""


class ColorBoxVariant(Enum):
    """
    颜色选择框 类型
    COLOR 无透明度。
    ALPHA 带透明度。
    """
    COLOR = "color"
    """无透明度"""
    ALPHA = "alpha"
    """带透明度"""


class FontBoxVariant(Enum):
    """
    字体选择框 类型
    null
    """


class PathBoxVariant(Enum):
    """
    路径对话框 类型
    FILE 表示读取文件的对话框，
    FILE_SAVE 表示写入文件的对话框，
    DIRECTORY 表示选择文件夹的对话框。
    """
    FILE = obs.OBS_PATH_FILE
    """读取文件"""
    FILE_SAVE = obs.OBS_PATH_FILE_SAVE
    """写入文件"""
    DIRECTORY = obs.OBS_PATH_DIRECTORY
    """选择文件夹"""


# 控件属性
# ----------------------------------------------------------------------------------------------------------------
@dataclass
class ControlBaseData:
    """
    所有控件的基类数据模型。
    注意：dataclass 主要用于存储数据，复杂逻辑应放在管理器类中。
    """
    widget_category: WidgetCategory = None
    """📵🥚控件的基本类型"""
    props_name: str = "props"
    """📵🥚控件所属属性集的名称"""
    object_name: str = ""
    """📵🥚控件对象名"""
    control_name: str = ""
    """📵🥚控件的唯一标识名，用于在脚本内部引用。"""
    description: str = ""
    """📵🥚显示给用户的简短描述/标签。"""
    long_description: str = "长描述示例"
    """📵🥚显示给用户的详细帮助信息。"""
    widget_variant: Union[
        CheckBoxVariant,
        ComboBoxVariant,
        PathBoxVariant,
        ButtonVariant,
        GroupVariant,
        ColorBoxVariant,
        FontBoxVariant,
        ListBoxVariant,
        TextBoxVariant,
        DigitalBoxVariant
    ] = None
    """📵🥚控件在 OBS API 中的功能类型 (如 OBS_TEXT_DEFAULT)。"""
    modified_callback_enabled: bool = False
    """📵🥚该控件的值变化时是否触发修改回调函数。"""
    load_order: int = 0
    """📵控件的加载顺序，数值越小越靠前。"""
    props: Any = None
    """📵控件所属属性集对象 (obs_properties_t)。"""
    obj: Any = None
    """📵控件对应的 OBS 底层对象 (obs_property_t)。"""
    visible: bool = True
    """控件的可见状态。"""
    enabled: bool = True
    """控件的可用（是否灰显）状态。"""


@dataclass
class CheckBoxData(ControlBaseData):
    """复选框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.CHECKBOX
    """📵🥚控件的基本类型"""
    checked: bool = False
    """复选框的选中状态。"""


@dataclass
class DigitalBoxData(ControlBaseData):
    """数字框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.DIGITALBOX
    """📵🥚控件的基本类型"""
    widget_variant: DigitalBoxVariant = DigitalBoxVariant.INT
    """📵🥚数字框的变体类型。"""
    suffix: str = ""
    """📵🥚显示在数值后的单位后缀 (如 '%', 'px')。"""
    value: Union[int, float] = 0
    """当前显示的数值。"""
    min_val: Union[int, float] = 0  # 避免与内置函数 `min` 冲突
    """允许的最小值。"""
    max_val: Union[int, float] = 100  # 避免与内置函数 `max` 冲突
    """允许的最大值。"""
    step: Union[int, float] = 1
    """调整时的步长。"""


@dataclass
class TextBoxData(ControlBaseData):
    """文本框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.TEXTBOX
    """📵🥚控件的基本类型"""
    widget_variant: TextBoxVariant = TextBoxVariant.DEFAULT
    """📵🥚OBS 文本框类型常量。"""
    info_type: TextBoxInfoVariant = TextBoxInfoVariant.NORMAL
    """仅当 widget_variant 为 OBS_TEXT_INFO 时有效的信息类型。"""
    text: str = ""
    """文本框中的文字内容。"""


@dataclass
class ButtonData(ControlBaseData):
    """按钮控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.BUTTON
    """📵🥚控件的基本类型"""
    widget_variant: ButtonVariant = ButtonVariant.DEFAULT
    """📵🥚OBS 按钮类型常量。"""
    callback: Optional[Callable[[Any, Any], bool]] = None
    """📵🥚按钮被点击时触发的回调函数。"""
    url: str = ""
    """📵🥚仅当 widget_variant 为 OBS_BUTTON_URL 时有效的跳转链接。"""


@dataclass
class ComboBoxData(ControlBaseData):
    """组合框（下拉列表）控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.COMBOBOX
    """📵🥚控件的基本类型"""
    widget_variant: ComboBoxVariant = ComboBoxVariant.LIST
    """📵🥚OBS 组合框类型常量。"""
    display_text: str = ""  # 明确区分显示文本和值
    """当前显示在下拉框中的文本。"""
    value: str = ""
    """当前选中项对应的内部值。"""
    items: List[Dict[Literal["label", "value"], str]] = field(default_factory=list)
    """下拉框的选项列表，每个项是 {'label': '...', 'value': '...'}。"""


@dataclass
class ListBoxData(ControlBaseData):
    """列表框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.LISTBOX
    """📵🥚控件的基本类型"""
    widget_variant: ListBoxVariant = ListBoxVariant.STRINGS
    """📵🥚OBS 列表框类型常量。"""
    filter_str: str = "*.*"
    """📵🥚文件类型过滤器（如 '*.png;*.jpg'）。"""
    default_path: str = ""
    """📵🥚对话框的默认起始路径。"""
    items: List[Dict[Literal["value", "label", "selected", "hidden"], Any]] = field(default_factory=list)
    """表框中的项目列表，每个项目是字典格式。"""


@dataclass
class GroupData(ControlBaseData):
    """分组框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.GROUP
    """📵🥚控件的基本类型"""
    widget_variant: GroupVariant = GroupVariant.NORMAL
    """📵🥚OBS 分组框类型常量。"""
    group_props_name: str = "GroupProps"
    """📵🥚该分组所包含控件使用的属性集名称。"""
    group_props: Any = None
    """📵该分组所包含控件使用的属性集对象。"""
    folding_control_obj: Any = None  # 更清晰的命名
    """📵仅当 widget_variant 为 OBS_GROUP_CHECKABLE 时关联的折叠控制对象。"""
    checked: bool = True  # 对于可勾选分组
    """仅当 widget_variant 为 OBS_GROUP_CHECKABLE 时有效，表示分组是否被勾选。"""


@dataclass
class ColorBoxData(ControlBaseData):
    """颜色选择框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.COLORBOX
    """📵🥚控件的基本类型"""
    widget_variant: ColorBoxVariant = ColorBoxVariant.ALPHA
    """📵🥚颜色对话框的变体类型：COLOR（无透明度）或 ALPHA（带透明度）。"""
    color_alpha: int = 0xFF
    """透明度"""
    color_red: int = 0xFF
    """红色"""
    color_green: int = 0xFF
    """绿色"""
    color_blue: int = 0xFF
    """蓝色"""

    @property
    def color_value(self) -> int:
        """当前颜色值（ARGB格式的整数）。"""
        bgr = (self.color_blue * 0x10000) + (self.color_green * 0x100) + self.color_red
        if self.widget_variant == ColorBoxVariant.ALPHA:
            return (self.color_alpha * 0x1000000) + bgr
        elif self.widget_variant == ColorBoxVariant.COLOR:
            return bgr
        else:
            return bgr


@dataclass
class FontBoxData(ControlBaseData):
    """字体选择框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.FONTBOX
    """📵🥚控件的基本类型"""
    font_data: Any = None
    """📵字体数据对象（obs_data_t），包含字体信息。"""
    font_face: str = "Kai"
    """字体系列名称"""
    font_size: int = 36
    """字体大小"""
    font_style: Literal["Regular", "Bold", "Light", "Black"] = "Regular"
    """字体样式 Regular, Bold, Light, Black"""
    font_bold: bool = False
    """字体标志位 粗体。"""
    font_italic: bool = False
    """字体标志位 斜体。"""
    font_underline: bool = False
    """字体标志位 下划线。"""
    font_strikeout: bool = False
    """字体标志位 删除线。"""

    @property
    def font_flags(self):
        """字体标志位"""
        font_bold = 1 if self.font_bold else 0
        font_italic = 1 if self.font_italic else 0
        font_underline = 1 if self.font_underline else 0
        font_strikeout = 1 if self.font_strikeout else 0
        return int(f"0b{font_bold}{font_italic}{font_underline}{font_strikeout}", 2)


@dataclass
class PathBoxData(ControlBaseData):
    """路径选择框控件的专用数据模型。"""
    widget_category: WidgetCategory = WidgetCategory.PATHBOX
    """📵🥚控件的基本类型"""
    widget_variant: PathBoxVariant = PathBoxVariant.FILE
    """📵🥚OBS 路径框类型常量。"""
    default_path: str = ""
    """📵🥚对话框打开时的初始路径。"""
    path_text: str = ""  # 明确这是路径文本
    """当前显示或选中的路径字符串。"""
    filter_str: str = "*.*"  # 避免与内置函数 `filter` 冲突
    """文件对话框的文件类型过滤器 (如 '*.png;*.jpg')。"""


# 控件管理
# ----------------------------------------------------------------------------------------------------------------
class ControlManager:
    """
    控件管理器，负责管理所有控件的添加、查询和唯一性验证。

    特性：
    1. 按控件分类组织控件
    2. 确保control_name全局唯一
    3. 确保同一分类下object_name唯一
    4. 自动管理load_order
    5. 提供方便的访问接口
    6. 维护基础group控件和group_props_name约束
    """

    def __init__(self):
        """初始化控件管理器"""
        # 按分类存储控件的数据字典
        self._widgets_by_category: Dict[WidgetCategory, Dict[str, ControlBaseData]] = {
            category: PyOrderedDict() for category in WidgetCategory
        }

        # 全局control_name集合，用于确保唯一性
        self._global_control_names: Set[str] = set()

        # 按分类的object_name集合，用于确保同一分类下唯一性
        self._object_names_by_category: Dict[WidgetCategory, Set[str]] = {
            category: set() for category in WidgetCategory
        }

        # 按props_name分组的控件字典
        self._widgets_by_props: Dict[str, List[str]] = {}

        # 存储所有group控件的group_props_name，用于唯一性检查
        self._group_props_names: Set[str] = set()

        # 加载顺序计数器
        self._load_order_counter = 0

        # 基础group控件（特殊控件，不参与常规管理）
        self._basic_group: Optional[GroupData] = None

        # 为每个分类创建动态属性，允许通过.语法访问分类管理器
        self._setup_category_properties()

        # 创建基础group控件
        self._create_basic_group()

    def _setup_category_properties(self):
        """为每个控件分类设置动态属性"""
        for category in WidgetCategory:
            # 创建分类管理器实例
            category_manager = _CategoryManager(self, category)

            # 设置为实例属性
            # 使用分类枚举值的名称作为属性名（小写）
            prop_name = category.name.lower()
            setattr(self, prop_name, category_manager)

    def _create_basic_group(self):
        """创建基础group控件"""
        # 使用特殊的load_order值，不参与常规排序
        basic_group = GroupData(
            widget_category=WidgetCategory.GROUP,
            control_name="group",
            object_name="base",
            description="分组框",
            widget_variant=GroupVariant.NORMAL,
            group_props_name="props",
            props_name="",
            load_order=-1  # 特殊值，表示不参与常规排序
        )

        # 将基础group控件单独存储，不添加到常规映射中
        self._basic_group = basic_group

        # 将基础group的group_props_name添加到集合中，这样其他控件可以使用"props"
        self._group_props_names.add(basic_group.group_props_name)

        # 注意：不添加到 _widgets_by_category, _widgets_by_props 等常规映射中
        # 这样它就完全独立于常规控件管理系统

    def _validate_uniqueness(self, control_name: str, category: WidgetCategory, object_name: str) -> None:
        """
        验证控件名称的唯一性

        参数:
            control_name: 控件的全局唯一标识名
            category: 控件分类
            object_name: 控件在同一分类下的对象名

        异常:
            ValueError: 如果名称违反唯一性约束
        """
        # 检查是否是基础group控件的名称
        if control_name == "group":
            raise ValueError(f"control_name 'group' 是保留名称，用于基础group控件")

        # 验证control_name全局唯一
        if control_name in self._global_control_names:
            raise ValueError(f"control_name '{control_name}' 已存在，必须是全局唯一的")

        # 验证object_name在同一分类下唯一
        if object_name in self._object_names_by_category[category]:
            raise ValueError(f"object_name '{object_name}' 在分类 {category.value} 中已存在")

    def _validate_group_props_name(self, widget: ControlBaseData) -> None:
        """
        验证group控件的group_props_name约束

        参数:
            widget: group控件数据对象

        异常:
            ValueError: 如果违反group_props_name约束
        """
        if not isinstance(widget, GroupData):
            return

        # 1. 非基础group控件的group_props_name不能等于props_name
        if widget.group_props_name == widget.props_name:
            raise ValueError(
                f"group控件 '{widget.control_name}' 的 "
                f"group_props_name '{widget.group_props_name}' 不能等于 props_name"
            )

        # 2. 所有group控件的group_props_name不能重名（包括基础group的）
        if widget.group_props_name in self._group_props_names:
            raise ValueError(
                f"group_props_name '{widget.group_props_name}' 已存在，"
                f"所有group控件的group_props_name不能重名"
            )

    def _validate_props_name(self, widget: ControlBaseData) -> None:
        """
        验证控件的props_name必须来自某个group控件的group_props_name

        参数:
            widget: 控件数据对象

        异常:
            ValueError: 如果props_name无效
        """
        # 验证props_name必须存在于已注册的group_props_name中
        if widget.props_name not in self._group_props_names:
            raise ValueError(
                f"控件 '{widget.control_name}' 的 props_name '{widget.props_name}' "
                f"必须来自某个group控件的group_props_name"
            )

    def _add_control_to_maps(self, widget: ControlBaseData) -> None:
        """
        将控件添加到各种映射中

        参数:
            widget: 控件数据对象
        """
        category = widget.widget_category

        # 添加到分类字典
        self._widgets_by_category[category][widget.control_name] = widget

        # 添加到全局control_name集合
        self._global_control_names.add(widget.control_name)

        # 添加到分类object_name集合
        self._object_names_by_category[category].add(widget.object_name)

        # 添加到props_name分组字典
        props_name = widget.props_name
        if props_name not in self._widgets_by_props:
            self._widgets_by_props[props_name] = []
        self._widgets_by_props[props_name].append(widget.control_name)

        # 如果是Group，还需要处理group_props_name
        if category == WidgetCategory.GROUP and hasattr(widget, 'group_props_name'):
            group_props_name = widget.group_props_name
            self._group_props_names.add(group_props_name)

            if group_props_name not in self._widgets_by_props:
                self._widgets_by_props[group_props_name] = []

    def _get_widget_class(self, category: WidgetCategory, **kwargs) -> type:
        """
        根据分类获取对应的数据类

        参数:
            category: 控件分类
            **kwargs: 控件属性

        返回:
            对应的数据类
        """
        widget_classes = {
            WidgetCategory.CHECKBOX: CheckBoxData,
            WidgetCategory.DIGITALBOX: DigitalBoxData,
            WidgetCategory.TEXTBOX: TextBoxData,
            WidgetCategory.BUTTON: ButtonData,
            WidgetCategory.COMBOBOX: ComboBoxData,
            WidgetCategory.LISTBOX: ListBoxData,
            WidgetCategory.GROUP: GroupData,
            WidgetCategory.COLORBOX: ColorBoxData,
            WidgetCategory.FONTBOX: FontBoxData,
            WidgetCategory.PATHBOX: PathBoxData,
        }

        return widget_classes.get(category)

    def create_widget(self, category: WidgetCategory, control_name: str, object_name: Optional[str] = None,
                      **kwargs) -> ControlBaseData:
        """
        创建新的控件实例

        参数:
            category: 控件分类
            control_name: 控件的全局唯一标识名
            object_name: 控件对象名，如果为None则使用control_name
            **kwargs: 控件属性

        返回:
            创建的控件数据对象

        异常:
            ValueError: 如果名称违反唯一性约束或其他验证失败
        """
        # 如果未提供object_name，使用control_name
        if object_name is None:
            object_name = control_name

        # 验证唯一性
        self._validate_uniqueness(control_name, category, object_name)

        # 获取对应的数据类
        widget_class = self._get_widget_class(category, **kwargs)
        if widget_class is None:
            raise ValueError(f"不支持的分类: {category}")

        # 设置widget_category
        kwargs['widget_category'] = category

        # 设置control_name和object_name
        kwargs['control_name'] = control_name
        kwargs['object_name'] = object_name

        # 设置load_order
        if 'load_order' not in kwargs:
            kwargs['load_order'] = self._load_order_counter
            self._load_order_counter += 1

        # 创建控件实例
        widget = widget_class(**kwargs)

        # 验证props_name必须来自group_props_name
        self._validate_props_name(widget)

        # 验证group控件的group_props_name约束
        self._validate_group_props_name(widget)

        # 添加到各种映射中
        self._add_control_to_maps(widget)

        return widget

    def get_widgets_by_load_order(self) -> List[ControlBaseData]:
        """
        获取按load_order排序的控件列表（不包含基础group控件）

        返回:
            按load_order升序排列的控件列表
        """
        all_widgets = []
        for category_dict in self._widgets_by_category.values():
            all_widgets.extend(category_dict.values())

        # 按load_order排序
        return sorted(all_widgets, key=lambda w: w.load_order)

    def get_props_mapping(self) -> Dict[str, List[str]]:
        """
        获取props_name到控件control_name的映射字典（不包含基础group控件）

        返回:
            props_name到控件control_name列表的映射字典
        """
        return self._widgets_by_props.copy()

    def get_widget_by_control_name(self, control_name: str) -> Optional[ControlBaseData]:
        """
        通过control_name查找控件

        参数:
            control_name: 控件的全局唯一标识名

        返回:
            控件数据对象，如果不存在则返回None
        """
        # 首先检查是否是基础group控件
        if control_name == "group":
            return self._basic_group

        # 在常规控件中查找
        for category_dict in self._widgets_by_category.values():
            if control_name in category_dict:
                return category_dict[control_name]
        return None

    def get_basic_group(self) -> GroupData:
        """
        获取基础group控件

        返回:
            基础group控件数据对象
        """
        return self._basic_group

    def clear(self):
        """清除所有常规控件，但保留基础group控件"""
        self._widgets_by_category = {category: PyOrderedDict() for category in WidgetCategory}
        self._global_control_names.clear()
        self._object_names_by_category = {category: set() for category in WidgetCategory}
        self._widgets_by_props.clear()
        self._group_props_names.clear()
        self._load_order_counter = 0

        # 重新创建基础group控件
        self._create_basic_group()

    @property
    def total_widgets(self) -> int:
        """获取常规控件总数（不包含基础group控件）"""
        return len(self._global_control_names)

    @property
    def available_group_props_names(self) -> Set[str]:
        """获取所有可用的group_props_name"""
        return self._group_props_names.copy()

    def __str__(self) -> str:
        """字符串表示"""
        result = [f"ControlManager (共 {self.total_widgets} 个常规控件)"]

        # 基础group控件信息
        if self._basic_group:
            result.append(
                f"基础group控件: {self._basic_group.control_name} (group_props_name: {self._basic_group.group_props_name})")
        else:
            result.append(f"基础group控件: 未初始化")

        result.append(f"可用group_props_name: {', '.join(sorted(self._group_props_names))}")

        # 各分类控件数量
        for category in WidgetCategory:
            count = len(self._widgets_by_category[category])
            if count > 0:
                result.append(f"  {category.value}: {count} 个")

        return "\n".join(result)


class _CategoryManager:
    """
    分类管理器，提供特定分类的控件操作接口
    """

    def __init__(self, manager: 'ControlManager', category: WidgetCategory):
        """
        初始化分类管理器

        参数:
            manager: 父控件管理器
            category: 控件分类
        """
        self._manager = manager
        self._category = category

    def add(self, control_name: str, object_name: Optional[str] = None, **kwargs) -> ControlBaseData:
        """
        向该分类添加控件

        参数:
            control_name: 控件的全局唯一标识名
            object_name: 控件对象名，如果为None则使用control_name
            **kwargs: 控件属性

        返回:
            创建的控件数据对象
        """
        # 确保设置了正确的分类
        kwargs['widget_category'] = self._category

        # 调用父管理器的创建方法
        return self._manager.create_widget(self._category, control_name, object_name, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """
        通过属性名获取控件

        参数:
            name: 控件的control_name

        返回:
            控件数据对象

        异常:
            AttributeError: 如果控件不存在
        """
        # 首先尝试从父管理器的分类字典中获取
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})

        if name in widgets_dict:
            return widgets_dict[name]

        # 如果找不到，抛出AttributeError
        raise AttributeError(f"分类 '{self._category.value}' 中没有名为 '{name}' 的控件")

    def __getitem__(self, key: str) -> Any:
        """支持通过[]语法访问控件"""
        return self.__getattr__(key)

    def __contains__(self, key: str) -> bool:
        """检查控件是否存在"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return key in widgets_dict

    def __iter__(self):
        """迭代该分类的所有控件"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return iter(widgets_dict.values())

    def __len__(self) -> int:
        """获取该分类的控件数量"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return len(widgets_dict)

    def keys(self):
        """获取所有控件的control_name"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return widgets_dict.keys()

    def values(self):
        """获取所有控件对象"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return widgets_dict.values()

    def items(self):
        """获取(control_name, 控件对象)对"""
        widgets_dict = self._manager._widgets_by_category.get(self._category, {})
        return widgets_dict.items()

    def __str__(self) -> str:
        """字符串表示"""
        count = len(self)
        return f"{self._category.value}管理器 (共 {count} 个控件)"


# 单例控件管理器实例
# ----------------------------------------------------------------------------------------------------------------
_global_control_manager = None


def get_control_manager() -> ControlManager:
    """
    获取全局控件管理器单例

    返回:
        全局控件管理器实例
    """
    global _global_control_manager
    if _global_control_manager is None:
        _global_control_manager = ControlManager()
    return _global_control_manager


# 使用示例
# ----------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # 获取控件管理器
    cm = get_control_manager()

    print("=" * 60)
    print("控件管理器使用示例")
    print("=" * 60)

    # 1. 获取基础group控件
    print("\n1. 基础group控件")
    print("-" * 40)
    basic_group = cm.get_basic_group()
    print(f"基础group控件: {basic_group.control_name}")
    print(f"  props_name: {basic_group.props_name}")
    print(f"  group_props_name: {basic_group.group_props_name}")
    print(f"可用group_props_name: {cm.available_group_props_names}")

    # 2. 添加控件示例
    print("\n2. 添加控件示例")
    print("-" * 40)

    # 添加一个复选框，使用基础group的group_props_name作为props_name
    cm.checkbox.add(
        control_name="enable_feature",
        object_name="enable_feature_checkbox",
        description="启用高级功能",
        checked=True,
        props_name="props"  # 来自基础group的group_props_name
    )
    print(f"添加了复选框: enable_feature (props_name: 'props')")

    # 添加一个数字框
    cm.digitalbox.add(
        control_name="volume_level",
        object_name="volume_slider",
        description="音量大小",
        widget_variant=DigitalBoxVariant.INT_SLIDER,
        value=75,
        min_val=0,
        max_val=100,
        suffix="%",
        props_name="props"  # 来自基础group的group_props_name
    )
    print(f"添加了数字框: volume_level (props_name: 'props')")

    # 3. 添加一个新分组框
    print("\n3. 添加新分组框示例")
    print("-" * 40)

    # 添加一个可勾选分组框
    cm.group.add(
        control_name="audio_settings",
        object_name="audio_group",
        description="音频设置",
        widget_variant=GroupVariant.CHECKABLE,
        group_props_name="audio_props",  # 新的group_props_name
        props_name="props",  # 来自基础group的group_props_name
        checked=True
    )
    print(f"添加了分组框: audio_settings")
    print(f"  group_props_name: 'audio_props'")
    print(f"  props_name: 'props'")

    # 现在可以向audio_props添加控件
    cm.checkbox.add(
        control_name="enable_echo",
        object_name="echo_checkbox",
        description="启用回声消除",
        checked=False,
        props_name="audio_props"  # 来自audio_settings分组的group_props_name
    )
    print(f"添加了复选框: enable_echo (props_name: 'audio_props')")

    # 4. 验证规则测试
    print("\n4. 验证规则测试")
    print("-" * 40)

    # 测试1: 尝试使用无效的props_name
    try:
        cm.checkbox.add(
            control_name="test_invalid_props",
            object_name="test_invalid",
            description="测试无效props_name",
            checked=True,
            props_name="invalid_props"  # 不存在于任何group的group_props_name中
        )
    except ValueError as e:
        print(f"测试1 - 使用无效props_name: {e}")

    # 测试2: 尝试添加group_props_name重复的分组
    try:
        cm.group.add(
            control_name="duplicate_group",
            object_name="dup_group",
            description="重复分组",
            widget_variant=GroupVariant.NORMAL,
            group_props_name="audio_props",  # 已经存在
            props_name="props"
        )
    except ValueError as e:
        print(f"测试2 - 重复group_props_name: {e}")

    # 测试3: 尝试添加group_props_name等于props_name的分组
    try:
        cm.group.add(
            control_name="invalid_group",
            object_name="invalid_grp",
            description="无效分组",
            widget_variant=GroupVariant.NORMAL,
            group_props_name="props",  # 等于props_name，这是不允许的（基础group除外）
            props_name="props"
        )
    except ValueError as e:
        print(f"测试3 - group_props_name等于props_name: {e}")

    # 测试4: 尝试使用保留名称"group"作为control_name
    try:
        cm.checkbox.add(
            control_name="group",  # 保留名称
            object_name="group_checkbox",
            description="测试保留名称",
            checked=True,
            props_name="props"
        )
    except ValueError as e:
        print(f"测试4 - 使用保留名称: {e}")

    # 5. 添加更多分组和控件
    print("\n5. 添加更多分组和控件")
    print("-" * 40)

    # 添加另一个分组框
    cm.group.add(
        control_name="video_settings",
        object_name="video_group",
        description="视频设置",
        widget_variant=GroupVariant.NORMAL,
        group_props_name="video_props",
        props_name="props"
    )
    print(f"添加了分组框: video_settings (group_props_name: 'video_props')")

    # 向video_props添加控件
    cm.combobox.add(
        control_name="resolution",
        object_name="res_combo",
        description="分辨率",
        widget_variant=ComboBoxVariant.LIST,
        display_text="1920x1080",
        value="1920x1080",
        items=[
            {"label": "1920x1080 (全高清)", "value": "1920x1080"},
            {"label": "1280x720 (高清)", "value": "1280x720"},
            {"label": "3840x2160 (4K)", "value": "3840x2160"}
        ],
        props_name="video_props"  # 来自video_settings分组的group_props_name
    )
    print(f"添加了组合框: resolution (props_name: 'video_props')")

    # 6. 显示统计信息
    print("\n6. 统计信息")
    print("-" * 40)
    print(cm)

    # 7. 按load_order排序的控件列表（不包含基础group）
    print("\n7. 按load_order排序的控件列表（不包含基础group）")
    print("-" * 40)

    sorted_widgets = cm.get_widgets_by_load_order()
    for widget in sorted_widgets:
        props_info = f"props_name: {widget.props_name}"
        if widget.widget_category == WidgetCategory.GROUP:
            props_info += f", group_props_name: {widget.group_props_name}"
        print(f"  [{widget.load_order:2d}] {widget.widget_category.value}: {widget.control_name} ({props_info})")

    # 8. 获取props_name映射（不包含基础group）
    print("\n8. props_name到控件的映射（不包含基础group）")
    print("-" * 40)

    props_mapping = cm.get_props_mapping()
    for props_name, control_names in props_mapping.items():
        print(f"  {props_name}: {', '.join(control_names)}")

    # 9. 通过control_name查找控件测试
    print("\n9. 通过control_name查找控件")
    print("-" * 40)

    # 查找基础group控件
    basic_group = cm.get_widget_by_control_name("group")
    print(f"查找基础group控件: {'成功' if basic_group else '失败'}")

    # 查找常规控件
    volume_widget = cm.get_widget_by_control_name("volume_level")
    print(f"查找volume_level: {'成功' if volume_widget else '失败'}")

    # 查找不存在的控件
    non_existent = cm.get_widget_by_control_name("non_existent")
    print(f"查找不存在的控件: {'成功' if non_existent else '失败'}")

    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)
