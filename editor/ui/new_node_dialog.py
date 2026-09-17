"""新建控件的对话框。"""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QComboBox, QVBoxLayout, QMessageBox,
)

from editor.model import WidgetNode, WidgetTree, list_variants_for, default_variant_for

def _list_widget_categories() -> list:
    try:
        from src.data.obsScriptControlData import WidgetCategory
        return [c.value for c in WidgetCategory]
    except Exception:
        return ["CHECKBOX", "DIGITALBOX", "TEXTBOX", "BUTTON",
                "COMBOBOX", "PATHBOX", "GROUP", "COLORBOX", "FONTBOX", "LISTBOX"]


class NewNodeDialog(QDialog):
    """收集新建控件所需的基本字段。props_name 由位置自动推导，不在这里填。"""

    def __init__(self, parent, tree: WidgetTree):
        super().__init__(parent)
        self.setWindowTitle("新建控件")
        self.resize(420, 240)
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

        self._widget_variant = QComboBox()
        self._widget_variant.setEditable(True)  # 允许手输未知值
        form.addRow("widget_variant", self._widget_variant)

        # 连接 category 变化 → 重建 variant 选项
        self._widget_category.currentTextChanged.connect(
            self._on_category_changed
        )

        self._group_props_name = QLineEdit()
        self._group_props_name.setPlaceholderText("仅当分类为 GROUP 时填写")
        form.addRow("group_props_name", self._group_props_name)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        # 初始填充
        self._on_category_changed(self._widget_category.currentText())

    def _on_accept(self):
        name = self._control_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "control_name 不能为空")
            return
        if name in self._tree.all_control_names():
            QMessageBox.warning(self, "提示", f"control_name '{name}' 已存在")
            return
        category = self._widget_category.currentText()
        gpn = self._group_props_name.text().strip()
        if category == "GROUP" and not gpn:
            QMessageBox.warning(self, "提示", "分组框必须填写 group_props_name")
            return
        if gpn and gpn in self._tree.group_props_names():
            QMessageBox.warning(self, "提示", f"group_props_name '{gpn}' 已被使用")
            return
        self.accept()

    def _on_category_changed(self, category: str):
        """根据 category 重建 widget_variant 下拉的选项。"""
        old_text = self._widget_variant.currentText()

        self._widget_variant.blockSignals(True)
        self._widget_variant.clear()
        self._widget_variant.addItem("")  # 空选项

        for name in list_variants_for(category):
            self._widget_variant.addItem(name)

        # 恢复：如果旧值在新选项里就用旧值；否则清空
        if old_text and old_text in [
            self._widget_variant.itemText(i)
            for i in range(self._widget_variant.count())
        ]:
            self._widget_variant.setCurrentText(old_text)
        else:
            default = default_variant_for(category)
            if default:
                self._widget_variant.setCurrentText(default)
            else:
                self._widget_variant.setCurrentText("")

        self._widget_variant.blockSignals(False)

    def result_node(self) -> WidgetNode:
        control_name = self._control_name.text().strip()
        category = self._widget_category.currentText()
        object_name = self._object_name.text().strip() or control_name
        description = self._description.text().strip()
        variant = self._widget_variant.text().strip() or None
        group_props_name = self._group_props_name.text().strip() or None

        # props_name 先随便填，AddNodeCommand.redo() 会重算
        return WidgetNode(
            control_name=control_name,
            widget_category=category,
            object_name=object_name,
            props_name="props",
            description=description,
            widget_variant=variant,
            group_props_name=group_props_name,
        )