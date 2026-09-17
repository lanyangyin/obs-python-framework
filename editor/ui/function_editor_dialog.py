"""函数体编辑对话框。"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPlainTextEdit,
    QDialogButtonBox, QMessageBox,
)

from editor.model.function_editor import (
    FunctionLocation, read_function_body, write_function_body, reload_module,
)


class FunctionEditorDialog(QDialog):
    """编辑某个回调函数体的对话框。"""

    def __init__(self, loc: FunctionLocation, parent=None):
        super().__init__(parent)
        self._loc = loc
        self._deleted = False
        self._init_error = None

        try:
            self._build_ui()
        except Exception as e:
            import traceback
            self._init_error = (
                f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
            )
            print(f"[FunctionEditorDialog] 初始化失败:\n{self._init_error}",
                  file=sys.stderr)

    def _build_ui(self):
        self.setWindowTitle(f"编辑函数：{self._loc.function_name}")
        self.resize(760, 560)

        layout = QVBoxLayout(self)

        info = QLabel(
            f"<b>文件：</b> {self._loc.source_path}<br>"
            f"<b>类：</b> {self._loc.class_name}　"
            f"<b>方法：</b> {self._loc.function_name}"
        )
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        sig_label = QLabel("函数签名（只读，装饰器与 def 保持不变）")
        sig_label.setStyleSheet("color: #888; margin-top: 4px;")
        layout.addWidget(sig_label)

        self._sig_view = QPlainTextEdit()
        self._sig_view.setPlainText(self._loc.signature)
        self._sig_view.setReadOnly(True)
        self._sig_view.setFixedHeight(80)
        self._sig_view.setFont(self._mono_font())
        layout.addWidget(self._sig_view)

        body_label = QLabel("函数体（可编辑，不含外层缩进）")
        body_label.setStyleSheet("color: #888; margin-top: 4px;")
        layout.addWidget(body_label)

        self._body_edit = QPlainTextEdit()
        self._body_edit.setPlainText(read_function_body(self._loc))
        self._body_edit.setFont(self._mono_font())
        self._body_edit.setTabStopDistance(32)
        layout.addWidget(self._body_edit, 1)

        hint = QLabel(
            "保存后编辑器自动重载模块并刷新预览。若重载失败，请手动重启编辑器。"
        )
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText("保存并重载")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        btn_delete = buttons.addButton("删除函数", QDialogButtonBox.DestructiveRole)
        btn_delete.clicked.connect(self._on_delete)

        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    @staticmethod
    def _mono_font():
        try:
            f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        except AttributeError:
            # PySide6 旧版本兼容
            f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        f.setPointSize(10)
        return f

    def _on_save(self):
        new_body = self._body_edit.toPlainText()

        # 语法预检：把 body 包成一个临时函数编译
        check_src = "def _check():\n"
        for line in new_body.splitlines():
            check_src += ("    " + line if line.strip() else "") + "\n"
        check_src += "    pass\n"
        try:
            compile(check_src, "<check>", "exec")
        except SyntaxError as e:
            QMessageBox.critical(
                self, "语法错误",
                f"函数体存在语法错误，未保存：\n\n{e}"
            )
            return

        try:
            write_function_body(self._loc, new_body)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
            return

        try:
            reload_module(self._loc.module_name)
        except Exception as e:
            QMessageBox.warning(
                self, "重载失败",
                f"源码已保存，但模块重载失败：\n{e}\n\n"
                f"请手动重启编辑器让改动生效。"
            )

        self.accept()

    def _on_delete(self):
        answer = QMessageBox.question(
            self, "确认删除",
            f"确认删除函数 '{self._loc.function_name}'？\n\n"
            f"将从 {self._loc.source_path.name} 中移除它的定义。\n"
            f"引用该函数的控件字段也会被清空。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self._deleted = True
        self.accept()

    def was_deleted(self) -> bool:
        return self._deleted