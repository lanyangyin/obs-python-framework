"""
可折叠的 section 控件。
- 顶部是标题栏（三角形图标 + 标题 + 计数），点击切换展开/折叠
- 主体是 QWidget，内容由调用方通过 set_content() 提供
- 折叠状态可序列化（供 SessionManager 记住）
"""
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton,
    QFrame, QSizePolicy,
)


class CollapsibleSection(QWidget):
    """可折叠的分组区域。"""

    toggled = Signal(bool)   # True=展开，False=折叠

    def __init__(self, title: str, expanded: bool = True,
                 color_hint: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._expanded = expanded

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- 标题栏 ---
        header = QFrame()
        header.setFrameShape(QFrame.NoFrame)
        header.setCursor(Qt.PointingHandCursor)
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(6, 4, 6, 4)
        header_layout.setSpacing(6)

        self._arrow = QToolButton()
        self._arrow.setAutoRaise(True)
        self._arrow.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self._arrow.setFixedSize(16, 16)
        self._arrow.setStyleSheet("QToolButton { border: none; }")
        self._arrow.clicked.connect(self.toggle)
        header_layout.addWidget(self._arrow)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-weight: 600;")
        if color_hint:
            self._title_label.setStyleSheet(
                f"font-weight: 600; color: {color_hint};"
            )
        header_layout.addWidget(self._title_label)

        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        outer.addWidget(header)

        # 点击 header 本身也触发 toggle（除了点箭头时不重复触发）
        header.mousePressEvent = lambda ev, self=self: self.toggle()

        # --- 内容 ---
        self._content_host = QWidget()
        self._content_layout = QVBoxLayout(self._content_host)
        self._content_layout.setContentsMargins(16, 4, 6, 6)
        self._content_layout.setSpacing(4)

        outer.addWidget(self._content_host)

        # 应用初始折叠状态
        self._apply_state()

    # ------------------------------------------------------------------
    # 对外
    # ------------------------------------------------------------------
    def set_title(self, title: str):
        self._title_label.setText(title)

    def set_count(self, n: int):
        if n <= 0:
            self._count_label.setText("")
        else:
            self._count_label.setText(f"({n})")

    def set_content(self, widget: QWidget):
        """替换主体内容（widget 会被自动 reparent）。"""
        # 清空旧内容
        while self._content_layout.count() > 0:
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        widget.setParent(self._content_host)
        self._content_layout.addWidget(widget)

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, value: bool):
        if self._expanded == value:
            return
        self._expanded = value
        self._apply_state()
        self.toggled.emit(self._expanded)

    def toggle(self):
        self.set_expanded(not self._expanded)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _apply_state(self):
        self._content_host.setVisible(self._expanded)
        self._arrow.setArrowType(Qt.DownArrow if self._expanded else Qt.RightArrow)