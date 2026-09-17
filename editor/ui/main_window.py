"""编辑器主窗口。"""
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QWidget, QVBoxLayout,
)

from editor.model import (
    WidgetTree, load_tree, save_tree, validate,
    default_template_path, default_data_path,
)
from editor.logging_config import get_logger, get_log_dir, log_exception
from editor.ui.tree_panel import TreePanel
from editor.ui.property_panel import PropertyPanel


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._log = get_logger()
        self._log.info("MainWindow 初始化")
        self.setWindowTitle("OBS Script Framework - 控件编辑器")
        self.resize(1200, 700)

        self._tree: Optional[WidgetTree] = None
        self._current_template_path: str = default_template_path()
        self._current_data_path: str = default_data_path()
        self._modified: bool = False

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        self._load_default()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        tb = QToolBar("主工具栏", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        act_open = QAction("打开...", self)
        act_open.triggered.connect(self.action_open)
        tb.addAction(act_open)

        act_save = QAction("保存", self)
        act_save.triggered.connect(self.action_save)
        tb.addAction(act_save)

        act_save_as = QAction("另存为...", self)
        act_save_as.triggered.connect(self.action_save_as)
        tb.addAction(act_save_as)

        tb.addSeparator()

        act_reload = QAction("重新加载", self)
        act_reload.triggered.connect(self.action_reload)
        tb.addAction(act_reload)

        tb.addSeparator()

        act_log = QAction("打开日志目录", self)
        act_log.triggered.connect(self.action_open_log_dir)
        tb.addAction(act_log)

        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        tb.addAction(act_exit)

    def _build_central(self):
        splitter = QSplitter(Qt.Horizontal)

        self.tree_panel = TreePanel()
        self.tree_panel.node_selected.connect(self._on_node_selected)

        self.property_panel = PropertyPanel()
        self.property_panel.node_edited.connect(self._on_node_edited)

        splitter.addWidget(self.tree_panel)
        splitter.addWidget(self.property_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])

        self.setCentralWidget(splitter)

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        self.validation_label = QLabel("")
        self.validation_label.setCursor(Qt.PointingHandCursor)
        self.validation_label.mousePressEvent = lambda ev: self._show_validation_dialog()
        self.status_bar.addPermanentWidget(self.validation_label)

        self._last_errors = []

    # ------------------------------------------------------------------
    # 动作
    # ------------------------------------------------------------------
    def _load_default(self):
        try:
            self._log.info(f"加载默认 CSV: {self._current_data_path}")
            self._tree = load_tree(self._current_template_path, self._current_data_path)
            self.tree_panel.load_tree(self._tree)
            self.property_panel.set_tree(self._tree)
            self._modified = False
            self._refresh_status()
            self._log.info(f"加载成功，节点数={len(self._tree)}")
        except Exception as e:
            log_exception(self._log, "加载默认 CSV 失败", e)
            QMessageBox.critical(self, "加载失败", f"无法加载默认 CSV:\n{e}")

    def action_open_log_dir(self):
        import os
        import subprocess
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(log_dir))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(log_dir)])
            else:
                subprocess.Popen(["xdg-open", str(log_dir)])
            self._log.info(f"打开日志目录: {log_dir}")
        except Exception as e:
            log_exception(self._log, "打开日志目录失败", e)
            QMessageBox.warning(self, "打开失败", f"无法打开目录：{log_dir}\n{e}")

    def action_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 widgetData.csv", self._current_data_path,
            "CSV 文件 (*.csv);;所有文件 (*)",
        )
        if not path:
            return
        try:
            self._log.info(f"打开文件: {path}")
            self._tree = load_tree(self._current_template_path, path)
            self._current_data_path = path
            self.tree_panel.load_tree(self._tree)
            self.property_panel.set_tree(self._tree)
            self._modified = False
            self._refresh_status()
            self._log.info(f"打开成功，节点数={len(self._tree)}")
        except Exception as e:
            log_exception(self._log, f"打开文件失败: {path}", e)
            QMessageBox.critical(self, "打开失败", str(e))

    def action_save(self):
        if self._tree is None:
            return
        try:
            save_tree(self._tree, self._current_template_path, self._current_data_path)
            self._modified = False
            self._refresh_status()
            self.status_bar.showMessage(f"已保存到 {self._current_data_path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def action_save_as(self):
        if self._tree is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self._current_data_path,
            "CSV 文件 (*.csv);;所有文件 (*)",
        )
        if not path:
            return
        try:
            save_tree(self._tree, self._current_template_path, path)
            self._current_data_path = path
            self._modified = False
            self._refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def action_reload(self):
        if self._tree is None:
            return
        try:
            self._tree = load_tree(self._current_template_path, self._current_data_path)
            self.tree_panel.load_tree(self._tree)
            self._modified = False
            self._refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "重载失败", str(e))

    # ------------------------------------------------------------------
    # 信号
    # ------------------------------------------------------------------
    def _on_node_selected(self, node):
        self.property_panel.set_node(node)
        if node is not None:
            self.status_bar.showMessage(
                f"选中: {node.control_name} ({node.widget_category})", 2000
            )

    def _on_node_edited(self, node, field: str):
        self._modified = True
        self._log.debug(f"编辑: {node.control_name}.{field}")
        if field in ("object_name", "description", "props_name", "group_props_name"):
            self._refresh_tree_label(node)
        self._refresh_status()

    def _refresh_tree_label(self, node):
        """刷新树中某个节点的显示文本。"""
        try:
            self.tree_panel.refresh_node_label(node)
        except AttributeError:
            # tree_panel 尚未实现这个接口，退化为整体重载（简单但不保留展开状态）
            # 后续 Step 4 再优化
            pass

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------
    def _refresh_status(self):
        if self._tree is None:
            self.status_label.setText("未加载")
            self.validation_label.setText("")
            self._last_errors = []
            return

        self.status_label.setText(f"节点数: {len(self._tree)}")

        errors = validate(self._tree)
        self._last_errors = errors

        # 把校验结果传播到树面板
        self.tree_panel.apply_validation(errors)

        n_err = sum(1 for e in errors if e.severity == "error")
        n_warn = sum(1 for e in errors if e.severity == "warning")
        if n_err or n_warn:
            self.validation_label.setText(f"⚠ {n_err} 错误 / {n_warn} 警告（点击查看）")
            self.validation_label.setStyleSheet("color: #c44; font-weight: 600;")
        else:
            self.validation_label.setText("✓ 无问题")
            self.validation_label.setStyleSheet("color: #4a4; font-weight: 600;")
        self._log.debug(
            f"校验完成: {n_err} 错误 / {n_warn} 警告"
        )

    def _show_validation_dialog(self):
        if not self._last_errors:
            QMessageBox.information(self, "校验结果", "当前没有错误或警告。")
            return

        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
            QDialogButtonBox,
        )

        dlg = QDialog(self)
        dlg.setWindowTitle("校验结果")
        dlg.resize(640, 400)
        layout = QVBoxLayout(dlg)

        list_widget = QListWidget()
        for e in self._last_errors:
            item = QListWidgetItem(str(e))
            if e.severity == "error":
                item.setForeground(QBrush(QColor("#c44")))
            else:
                item.setForeground(QBrush(QColor("#c80")))
            item.setData(Qt.UserRole, e.control_name)
            list_widget.addItem(item)

        def on_double_clicked(item):
            control_name = item.data(Qt.UserRole)
            if control_name and self.tree_panel.select_by_control_name(control_name):
                dlg.accept()

        list_widget.itemDoubleClicked.connect(on_double_clicked)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        dlg.exec()