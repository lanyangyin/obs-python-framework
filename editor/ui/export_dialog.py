"""导出 OBS 脚本模板对话框。"""
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPlainTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QDialogButtonBox, QFileDialog, QMessageBox,
    QLineEdit, QPushButton, QWidget, QFormLayout,
)

from editor.model import WidgetTree, generate_all, summarize


class ExportTemplateDialog(QDialog):
    """
    预览 + 导出。

    流程：选目录 -> 预览每个文件 -> 确认 -> 写入
    """

    def __init__(self, tree: WidgetTree, default_dir: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出 OBS 脚本模板")
        self.resize(900, 620)

        self._tree = tree
        self._files: Dict[str, str] = generate_all(tree)
        self._summary = summarize(tree)

        layout = QVBoxLayout(self)

        # --- 摘要 ---
        summary = QLabel(
            f"将生成 <b>{len(self._files)}</b> 个文件，"
            f"共 <b>{self._summary['button_callbacks']}</b> 个按钮回调、"
            f"<b>{self._summary['control_callbacks']}</b> 个控件回调。"
        )
        layout.addWidget(summary)

        # --- 目录选择 ---
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("导出目录"))
        self._dir_edit = QLineEdit(default_dir or str(Path.cwd()))
        dir_row.addWidget(self._dir_edit)
        btn_pick = QPushButton("浏览...")
        btn_pick.clicked.connect(self._on_pick_dir)
        dir_row.addWidget(btn_pick)
        layout.addLayout(dir_row)

        # --- 文件列表 + 预览 ---
        splitter = QSplitter(Qt.Horizontal)

        self._file_list = QListWidget()
        for rel in self._files.keys():
            self._file_list.addItem(QListWidgetItem(rel))
        self._file_list.currentRowChanged.connect(self._on_file_selected)
        splitter.addWidget(self._file_list)

        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setLineWrapMode(QPlainTextEdit.NoWrap)
        splitter.addWidget(self._preview)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        # --- 按钮 ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("导出")
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 默认选中第一个文件
        if self._file_list.count() > 0:
            self._file_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    def _on_pick_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "选择导出目录", self._dir_edit.text()
        )
        if d:
            self._dir_edit.setText(d)

    def _on_file_selected(self, row: int):
        if row < 0:
            return
        rel = self._file_list.item(row).text()
        content = self._files.get(rel, "")
        self._preview.setPlainText(content)

    def _on_export(self):
        target = Path(self._dir_edit.text().strip())
        if not target:
            QMessageBox.warning(self, "提示", "请先选择导出目录")
            return
        if not target.exists():
            try:
                target.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                QMessageBox.warning(self, "错误", f"目录无法创建：{e}")
                return

        # 检查覆盖
        existing = []
        for rel in self._files:
            if (target / rel).exists():
                existing.append(rel)

        if existing:
            msg = "以下文件已存在，是否覆盖？\n\n" + "\n".join(existing)
            if QMessageBox.question(
                self, "覆盖确认", msg,
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return

        # 写入
        try:
            for rel, content in self._files.items():
                path = target / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "写入失败", str(e))
            return

        QMessageBox.information(
            self, "完成",
            f"已导出 {len(self._files)} 个文件到：\n{target}"
        )
        self.accept()