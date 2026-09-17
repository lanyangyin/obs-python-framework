"""新建控件的对话框。"""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QComboBox, QVBoxLayout, QMessageBox,
)

from editor.model import WidgetNode, WidgetTree
from editor.model.widget_node import WidgetNode as _WN  # noqa: F401


# 从 obsScriptFramework_ 的枚举里抽取分类名
def _list_widget_categories() -> list:
    try:
        from src.data.obsScriptControlData import WidgetCategory
        return [c.value for c in WidgetCategory]
    except Exception:
        return ["CHECKBOX", "DIGITALBOX", "TEXTBOX", "BUTTON",
                "COMBOBOX", "PATHBOX", "GROUP", "COLORBOX", "FONTBOX", "LISTBOX"]


class NewNodeDialog(QDialog):
    """收集新建控件所需的基本字段。"""

    def __init__(self, parent, tree: WidgetTree):
        super().__init__(parent)
        self.setWindowTitle("新建控件")
        self.resize(420, 260)
        self._tree = tree

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._control_name = QLineEdit()
        form.addRow("control_name *", self._control_name)

        self._widget_category = QComboBox()
        for cat in _list_widget_categories():
            self._widget_category.addItem(cat)
        form.addRow("widget_category *", self._widget_category)

        self._object_name = QLineEdit()
        self._object_name.setPlaceholderText("留空则同 control_name")
        form.addRow("object_name", self._object_name)

        self._description = QLineEdit()
        form.addRow("description", self._description)

        self._widget_variant = QLineEdit()
        self._widget_variant.setPlaceholderText("可选，如 INT_SLIDER")
        form.addRow("widget_variant", self._widget_variant)

        self._props_name = QComboBox()
        self._props_name.setEditable(True)
        for name in sorted(tree.group_props_names()):
            self._props_name.addItem(name)
        form.addRow("props_name", self._props_name)

        self._group_props_name = QLineEdit()
        self._group_props_name.setPlaceholderText("仅 GROUP 需要")
        form.addRow("group_props_name", self._group_props_name)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        name = self._control_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "control_name 不能为空")
            return
        if name in self._tree.all_control_names():
            QMessageBox.warning(self, "提示", f"control_name '{name}' 已存在")
            return
        self.accept()

    def result_node(self) -> WidgetNode:
        control_name = self._control_name.text().strip()
        category = self._widget_category.currentText()
        object_name = self._object_name.text().strip() or control_name
        description = self._description.text().strip()
        variant = self._widget_variant.text().strip() or None
        props_name = self._props_name.currentText().strip() or "props"
        group_props_name = self._group_props_name.text().strip() or None

        return WidgetNode(
            control_name=control_name,
            widget_category=category,
            object_name=object_name,
            props_name=props_name,
            description=description,
            widget_variant=variant,
            group_props_name=group_props_name,
        )