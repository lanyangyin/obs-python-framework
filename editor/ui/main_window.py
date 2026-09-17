"""编辑器主窗口。"""
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtGui import QAction, QKeySequence, QUndoStack
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QWidget, QVBoxLayout,
    QDialog,
)

from editor.model import (
    WidgetTree, load_tree, save_tree, validate,
    default_template_path, default_data_path,
)
from editor.model import load_tree, save_tree, validate, diff_trees
from editor.ui.diff_dialog import DiffDialog
from editor.logging_config import get_logger, get_log_dir, log_exception
from editor.ui.tree_panel import TreePanel
from editor.ui.property_panel import PropertyPanel
from editor.ui.commands import (
    AddNodeCommand, RemoveNodeCommand, MoveNodeCommand, EditFieldCommand,
)
from editor.ui.new_node_dialog import NewNodeDialog
from editor.settings_manager import load_settings, save_settings, EditorSettings
from editor.ui.style_utils import apply_to_app
from editor.ui.settings_dialog import SettingsDialog
from PySide6.QtWidgets import QApplication

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._log = get_logger()
        self._editor_settings = load_settings()
        self._log.info("MainWindow 初始化")
        self.setWindowTitle("OBS Script Framework - 控件编辑器")
        self.resize(1200, 700)

        self._tree: Optional[WidgetTree] = None
        self._current_template_path: str = default_template_path()
        self._current_data_path: str = default_data_path()
        self._modified: bool = False
        self._selected_node = None
        self._undo_stack = QUndoStack(self)
        self._undo_stack.indexChanged.connect(self._on_undo_stack_changed)

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

        # --- 文件 ---
        act_open = QAction("打开...", self)
        act_open.triggered.connect(self.action_open)
        tb.addAction(act_open)

        act_save = QAction("保存", self)
        act_save.triggered.connect(self.action_save)
        tb.addAction(act_save)

        act_save_as = QAction("另存为...", self)
        act_save_as.triggered.connect(self.action_save_as)
        tb.addAction(act_save_as)

        act_reload = QAction("重新加载", self)
        act_reload.triggered.connect(self.action_reload)
        tb.addAction(act_reload)

        tb.addSeparator()

        # --- 编辑 ---
        self._act_undo = QAction("撤销", self)
        self._act_undo.setShortcut(QKeySequence.Undo)
        self._act_undo.triggered.connect(self.action_undo)
        self._act_undo.setEnabled(False)
        tb.addAction(self._act_undo)

        self._act_redo = QAction("重做", self)
        self._act_redo.setShortcut(QKeySequence.Redo)
        self._act_redo.triggered.connect(self.action_redo)
        self._act_redo.setEnabled(False)
        tb.addAction(self._act_redo)

        tb.addSeparator()

        # --- 节点操作 ---
        self._act_add = QAction("新建控件", self)
        self._act_add.triggered.connect(self.action_add_node)
        tb.addAction(self._act_add)

        self._act_remove = QAction("删除选中", self)
        self._act_remove.triggered.connect(self.action_remove_node)
        self._act_remove.setEnabled(False)
        tb.addAction(self._act_remove)

        self._act_up = QAction("上移", self)
        self._act_up.triggered.connect(self.action_move_up)
        self._act_up.setEnabled(False)
        tb.addAction(self._act_up)

        self._act_down = QAction("下移", self)
        self._act_down.triggered.connect(self.action_move_down)
        self._act_down.setEnabled(False)
        tb.addAction(self._act_down)

        tb.addSeparator()

        act_settings = QAction("设置...", self)
        act_settings.triggered.connect(self.action_open_settings)
        tb.addAction(act_settings)

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
        self.tree_panel.node_move_requested.connect(self._on_node_move_requested)
        self.tree_panel.context_add_requested.connect(self._on_context_add)
        self.tree_panel.context_add_child_requested.connect(self._on_context_add_child)
        self.tree_panel.context_remove_requested.connect(self._on_context_remove)
        self.tree_panel.context_move_up_requested.connect(self._on_context_move_up)
        self.tree_panel.context_move_down_requested.connect(self._on_context_move_down)

        self.property_panel = PropertyPanel()
        self.property_panel.field_edit_committed.connect(self._on_field_edit_committed)

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
        self._undo_stack.blockSignals(True)
        self._undo_stack.clear()
        self._undo_stack.blockSignals(False)

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
        self._undo_stack.blockSignals(True)
        self._undo_stack.clear()
        self._undo_stack.blockSignals(False)

    def _load_disk_tree(self):
        """
        加载磁盘上的当前数据文件，用于差异对比。
        文件不存在时返回 None。
        """
        from pathlib import Path
        if not Path(self._current_data_path).exists():
            return None
        try:
            return load_tree(self._current_template_path, self._current_data_path)
        except Exception as e:
            self._log.warning(f"加载磁盘 CSV 失败（跳过差异对比）：{e}")
            return None

    def _do_save(self, path: str):
        """实际写入文件。"""
        try:
            save_tree(self._tree, self._current_template_path, path)
            self._current_data_path = path
            self._modified = False
            self._refresh_status()
            self.status_bar.showMessage(f"已保存到 {path}", 3000)
            self._log.info(f"保存成功: {path}")
        except Exception as e:
            log_exception(self._log, "保存失败", e)
            QMessageBox.critical(self, "保存失败", str(e))

    def action_save(self):
        if self._tree is None:
            return

        disk_tree = self._load_disk_tree()
        report = diff_trees(disk_tree, self._tree)

        if report.is_empty:
            # 无变化，直接保存（等同于刷新文件）
            self._do_save(self._current_data_path)
            return

        dlg = DiffDialog(report, self)
        if dlg.exec() != QDialog.Accepted:
            self._log.info("保存取消（用户未确认差异）")
            return

        self._do_save(self._current_data_path)

    def action_save_as(self):
        if self._tree is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self._current_data_path,
            "CSV 文件 (*.csv);;所有文件 (*)",
        )
        if not path:
            return

        # 另存为：以目标路径的磁盘文件为基准（若存在）
        from pathlib import Path
        disk_tree = None
        if Path(path).exists():
            try:
                disk_tree = load_tree(self._current_template_path, path)
            except Exception as e:
                self._log.warning(f"加载目标路径 CSV 失败（跳过差异对比）：{e}")

        report = diff_trees(disk_tree, self._tree)
        if not report.is_empty:
            dlg = DiffDialog(report, self)
            if dlg.exec() != QDialog.Accepted:
                self._log.info("另存为取消（用户未确认差异）")
                return

        self._do_save(path)

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
        self._undo_stack.blockSignals(True)
        self._undo_stack.clear()
        self._undo_stack.blockSignals(False)

    # ------------------------------------------------------------------
    # 信号
    # ------------------------------------------------------------------
    def _on_node_selected(self, node):
        self._selected_node = node
        self.property_panel.set_node(node)
        self._update_node_action_states()
        if node is not None:
            self.status_bar.showMessage(
                f"选中: {node.control_name} ({node.widget_category})", 2000
            )

    def _on_field_edit_committed(self, node, field, old_value, new_value):
        """属性面板提交了一次字段编辑，记录到 undo stack。"""
        if field.startswith("prop::"):
            prop_name = field[len("prop::"):]
            cmd = EditFieldCommand(
                node, field, old_value, new_value,
                notify_callback=self._on_edit_command_applied,
                property_name=prop_name,
            )
        else:
            cmd = EditFieldCommand(
                node, field, old_value, new_value,
                notify_callback=self._on_edit_command_applied,
            )
        self._undo_stack.push(cmd)

    def _on_edit_command_applied(self, node, field):
        """
        EditFieldCommand 的 redo/undo/mergeWith 完成时调用。
        做轻量刷新，不重建整棵树。
        """
        # 刷新树标签（object_name / description 之类会影响显示）
        self.tree_panel.refresh_node_label(node)
        # 如果属性面板当前显示的就是这个节点，同步刷新对应字段
        if self.property_panel.current_node() is node:
            self.property_panel.refresh_field(field)
        self._refresh_status()

    def _refresh_tree_label(self, node):
        """刷新树中某个节点的显示文本。"""
        try:
            self.tree_panel.refresh_node_label(node)
        except AttributeError:
            # tree_panel 尚未实现这个接口，退化为整体重载（简单但不保留展开状态）
            # 后续 Step 4 再优化
            pass

    def _update_node_action_states(self):
        node = self._selected_node
        self._act_remove.setEnabled(node is not None)
        if node is None:
            self._act_up.setEnabled(False)
            self._act_down.setEnabled(False)
            return

        parent = node.parent
        siblings = parent.children if parent is not None else self._tree.roots()
        try:
            idx = siblings.index(node)
        except ValueError:
            idx = -1
        self._act_up.setEnabled(idx > 0)
        self._act_down.setEnabled(0 <= idx < len(siblings) - 1)

    def _update_undo_actions(self):
        self._act_undo.setEnabled(self._undo_stack.canUndo())
        self._act_redo.setEnabled(self._undo_stack.canRedo())

    def _on_undo_stack_changed(self, index: int):
        """
        QUndoStack 索引变化：push / undo / redo 都会触发。
        - 编辑类命令（EditFieldCommand）：UI 已由 notify_callback 处理，不再全量刷新
        - 结构类命令：全量重建树
        """
        self._update_undo_actions()
        if self._tree is None:
            return

        self._modified = True

        if self._is_recent_edit_command(index):
            # 编辑命令自己会刷新 UI，这里不再重建树
            self._log.debug(f"undo stack index -> {index}（编辑类，跳过全量刷新）")
            return

        remember_name = None
        if self._selected_node is not None:
            remember_name = self._selected_node.control_name

        self.tree_panel.load_tree(self._tree)

        if remember_name and self._tree.find(remember_name) is not None:
            self.tree_panel.select_by_control_name(remember_name)

        self._refresh_status()
        self._update_node_action_states()
        self._log.debug(f"undo stack index -> {index}，已重建树")

    def _is_recent_edit_command(self, index: int) -> bool:
        """
        判断刚执行/撤销的命令是不是 EditFieldCommand。
        - undo 之后：index 位置是新暴露出来的命令（就是刚被撤销的）
        - push / redo 之后：index - 1 位置是刚执行的命令
        """
        count = self._undo_stack.count()
        # 检查 index 位置（覆盖 undo 场景）
        if 0 <= index < count:
            cmd = self._undo_stack.command(index)
            if isinstance(cmd, EditFieldCommand):
                return True
        # 检查 index - 1 位置（覆盖 push / redo 场景）
        if 0 < index <= count:
            cmd = self._undo_stack.command(index - 1)
            if isinstance(cmd, EditFieldCommand):
                return True
        return False

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

    # ------------------------------------------------------------------
    # 节点操作
    # ------------------------------------------------------------------
    def action_add_node(self):
        """工具栏按钮：在选中节点之后插入同级控件。"""
        node = self._selected_node
        if node is None:
            parent = None
            index = len(self._tree.roots()) if self._tree else 0
        else:
            parent = node.parent
            siblings = parent.children if parent is not None else self._tree.roots()
            try:
                index = siblings.index(node) + 1
            except ValueError:
                index = len(siblings)
        self._add_node_at(parent, index)

    def action_remove_node(self):
        node = self._selected_node
        if node is None or self._tree is None:
            return

        subtree_size = sum(1 for _ in node.iter_subtree())
        msg = f"确认删除控件 '{node.control_name}'？"
        if subtree_size > 1:
            msg += f"\n\n将同时删除其 {subtree_size - 1} 个子控件。"

        if QMessageBox.question(self, "删除确认", msg) != QMessageBox.Yes:
            return

        try:
            cmd = RemoveNodeCommand(self._tree, node)
            self._undo_stack.push(cmd)
        except Exception as e:
            QMessageBox.warning(self, "删除失败", str(e))
            return

        self._log.info(f"删除控件: {node.control_name}")

    def action_undo(self):
        if not self._undo_stack.canUndo():
            return
        text = self._undo_stack.undoText()
        self._undo_stack.undo()
        self._log.info(f"撤销: {text}")

    def action_redo(self):
        if not self._undo_stack.canRedo():
            return
        text = self._undo_stack.redoText()
        self._undo_stack.redo()
        self._log.info(f"重做: {text}")

    def action_move_up(self):
        self._move_selected(-1)

    def action_move_down(self):
        self._move_selected(+1)

    def action_open_settings(self):
        dlg = SettingsDialog(self._editor_settings, self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._editor_settings = dlg.result_settings()
        save_settings(self._editor_settings)
        apply_to_app(QApplication.instance(), self._editor_settings)
        self._log.info(f"编辑器设置已更新: theme={self._editor_settings.theme}")

    def _move_selected(self, delta: int):
        node = self._selected_node
        if node is None or self._tree is None:
            return

        parent = node.parent
        siblings = parent.children if parent is not None else self._tree.roots()
        try:
            idx = siblings.index(node)
        except ValueError:
            return

        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(siblings):
            return

        try:
            cmd = MoveNodeCommand(self._tree, node, parent, new_idx)
            self._undo_stack.push(cmd)
        except Exception as e:
            QMessageBox.warning(self, "移动失败", str(e))
            return

        self._log.info(
            f"移动控件: {node.control_name} -> {parent.control_name if parent else '(root)'} "
            f"index={new_idx}"
        )

    def _on_node_move_requested(self, source_node, new_parent, new_index):
        if self._tree is None:
            return
        old_props = source_node.props_name
        try:
            cmd = MoveNodeCommand(self._tree, source_node, new_parent, new_index)
            self._undo_stack.push(cmd)
        except Exception as e:
            log_exception(self._log, "拖放移动失败", e)
            return
        self._log.info(
            f"拖放移动: {source_node.control_name} "
            f"props_name={old_props} -> {source_node.props_name}, "
            f"new_parent={new_parent.control_name if new_parent else '(root)'}, "
            f"index={new_index}"
        )

    # ------------------------------------------------------------------
    # 右键菜单响应
    # ------------------------------------------------------------------
    def _on_context_add(self, node):
        """
        在指定节点之后插入同级控件。
        node=None 表示在根末尾追加。
        """
        if self._tree is None:
            return

        if node is None:
            parent = None
            index = len(self._tree.roots())
        else:
            parent = node.parent
            siblings = parent.children if parent is not None else self._tree.roots()
            try:
                index = siblings.index(node) + 1
            except ValueError:
                index = len(siblings)

        self._add_node_at(parent, index)

    def _on_context_add_child(self, parent_node):
        """在分组下追加一个子控件。"""
        if self._tree is None or parent_node is None or not parent_node.is_group:
            return
        if not parent_node.group_props_name:
            QMessageBox.warning(
                self, "提示",
                f"分组 '{parent_node.control_name}' 没有 group_props_name，"
                f"请先在属性面板中设置。"
            )
            return
        self._add_node_at(parent_node, len(parent_node.children))

    def _on_context_remove(self, node):
        """右键删除指定节点。"""
        if node is None or self._tree is None:
            return
        # 让选中状态与 node 对齐（右键已经在 TreePanel 里设过 setCurrentIndex，
        # 但为了保险起见再走一次 _selected_node 逻辑）
        self._selected_node = node
        self.action_remove_node()

    def _on_context_move_up(self, node):
        if node is None or self._tree is None:
            return
        self._selected_node = node
        self._move_selected(-1)

    def _on_context_move_down(self, node):
        if node is None or self._tree is None:
            return
        self._selected_node = node
        self._move_selected(+1)

    def _add_node_at(self, parent, index):
        """在 (parent, index) 处新建节点。parent=None 表示根级。"""
        dlg = NewNodeDialog(self, self._tree)
        if dlg.exec() != QDialog.Accepted:
            return
        new_node = dlg.result_node()
        try:
            cmd = AddNodeCommand(self._tree, new_node, parent, index)
            self._undo_stack.push(cmd)
        except ValueError as e:
            QMessageBox.warning(self, "新建失败", str(e))
            return
        self._log.info(
            f"新建控件: {new_node.control_name} ({new_node.widget_category}) "
            f"parent={parent.control_name if parent else '(root)'} index={index}"
        )