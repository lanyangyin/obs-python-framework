"""编辑器主窗口。"""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QWidget, QVBoxLayout,
)

from editor.model import (
    WidgetTree, load_tree, save_tree, validate,
    default_template_path, default_data_path,
)
from editor.ui.tree_panel import TreePanel


class PropertyPanelPlaceholder(QWidget):
    """Step 3 会替换为真正的属性面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("选中左侧控件后，属性将在这里显示。\n\n（Step 3 实现）")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(label)

    def set_node(self, node):
        pass


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
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

        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        tb.addAction(act_exit)

    def _build_central(self):
        splitter = QSplitter(Qt.Horizontal)

        self.tree_panel = TreePanel()
        self.tree_panel.node_selected.connect(self._on_node_selected)

        self.property_panel = PropertyPanelPlaceholder()

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
        self.status_bar.addPermanentWidget(self.validation_label)

    # ------------------------------------------------------------------
    # 动作
    # ------------------------------------------------------------------
    def _load_default(self):
        try:
            self._tree = load_tree(self._current_template_path, self._current_data_path)
            self.tree_panel.load_tree(self._tree)
            self._modified = False
            self._refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载默认 CSV:\n{e}")

    def action_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 widgetData.csv", self._current_data_path,
            "CSV 文件 (*.csv);;所有文件 (*)",
        )
        if not path:
            return
        try:
            self._tree = load_tree(self._current_template_path, path)
            self._current_data_path = path
            self.tree_panel.load_tree(self._tree)
            self._modified = False
            self._refresh_status()
        except Exception as e:
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

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------
    def _refresh_status(self):
        if self._tree is None:
            self.status_label.setText("未加载")
            self.validation_label.setText("")
            return

        self.status_label.setText(f"节点数: {len(self._tree)}")

        errors = validate(self._tree)
        n_err = sum(1 for e in errors if e.severity == "error")
        n_warn = sum(1 for e in errors if e.severity == "warning")
        if n_err or n_warn:
            self.validation_label.setText(f"⚠ {n_err} 错误 / {n_warn} 警告")
            self.validation_label.setStyleSheet("color: #c44; font-weight: 600;")
        else:
            self.validation_label.setText("✓ 无问题")
            self.validation_label.setStyleSheet("color: #4a4; font-weight: 600;")