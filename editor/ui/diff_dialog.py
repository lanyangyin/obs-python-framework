"""保存前差异确认对话框。"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QDialogButtonBox,
)

from editor.model import DiffReport


class DiffDialog(QDialog):
    """
    展示当前树与磁盘 CSV 的差异。
    用户可选择「保存」或「取消」。
    """

    def __init__(self, report: DiffReport, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认保存")
        self.resize(760, 520)
        self._report = report

        layout = QVBoxLayout(self)

        # 顶部摘要
        summary = QLabel(
            f"<b>变更摘要：</b> {report.summary()}"
        )
        layout.addWidget(summary)

        # 提示
        hint = QLabel(
            "以下是与磁盘上 CSV 的差异。点击「保存」将写入这些变更。"
        )
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)

        # 差异树
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["变更", "字段", "原值", "新值"])
        self._tree.setColumnWidth(0, 220)
        self._tree.setColumnWidth(1, 140)
        self._tree.setColumnWidth(2, 180)
        self._populate()
        layout.addWidget(self._tree)

        # 按钮
        buttons = QDialogButtonBox()
        btn_save = buttons.addButton("保存", QDialogButtonBox.AcceptRole)
        btn_cancel = buttons.addButton("取消", QDialogButtonBox.RejectRole)
        btn_save.setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # 填充
    # ------------------------------------------------------------------
    def _populate(self):
        report = self._report

        if report.added:
            added_root = QTreeWidgetItem(self._tree, [f"新增 ({len(report.added)})"])
            self._set_color(added_root, "#2a7")
            added_root.setExpanded(True)
            for node in report.added:
                child = QTreeWidgetItem(added_root, [
                    node.control_name,
                    "",
                    "",
                    f"{node.widget_category} / {node.object_name}",
                ])
                self._set_color(child, "#2a7")

        if report.removed:
            removed_root = QTreeWidgetItem(self._tree, [f"删除 ({len(report.removed)})"])
            self._set_color(removed_root, "#c44")
            removed_root.setExpanded(True)
            for node in report.removed:
                child = QTreeWidgetItem(removed_root, [
                    node.control_name,
                    "",
                    f"{node.widget_category} / {node.object_name}",
                    "",
                ])
                self._set_color(child, "#c44")

        if report.modified:
            mod_root = QTreeWidgetItem(self._tree, [f"修改 ({len(report.modified)})"])
            self._set_color(mod_root, "#c80")
            mod_root.setExpanded(True)
            for nd in report.modified:
                node_item = QTreeWidgetItem(mod_root, [
                    nd.control_name,
                    f"({nd.widget_category})",
                    "",
                    f"{len(nd.field_changes)} 项",
                ])
                self._set_color(node_item, "#c80")
                node_item.setExpanded(True)
                for fc in nd.field_changes:
                    field_label = fc.field
                    if field_label.startswith("prop::"):
                        field_label = "自由属性: " + field_label[len("prop::"):]
                    QTreeWidgetItem(node_item, [
                        "",
                        field_label,
                        _fmt(fc.old),
                        _fmt(fc.new),
                    ])

    def _set_color(self, item: QTreeWidgetItem, hex_color: str):
        brush = QBrush(QColor(hex_color))
        for col in range(item.columnCount()):
            item.setForeground(col, brush)


def _fmt(value):
    """复用 model 里的格式化逻辑。"""
    from editor.model.diff import _fmt as model_fmt
    return model_fmt(value)