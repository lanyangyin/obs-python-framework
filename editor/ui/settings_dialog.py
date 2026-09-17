"""首选项 / 设置对话框。"""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QSpinBox, QPushButton,
    QDialogButtonBox, QLabel, QColorDialog, QFontDialog,
    QGroupBox, QWidget, QGridLayout,
)

from editor.settings_manager import (
    EditorSettings, preset, DARK_PRESET, LIGHT_PRESET,
)


# 每种颜色字段的显示名
COLOR_FIELDS = [
    ("foreground", "前景色"),
    ("background", "背景色"),
    ("accent", "强调色"),
    ("input_background", "输入框背景"),
    ("input_foreground", "输入框文字"),
    ("tree_background", "树背景"),
    ("tree_foreground", "树文字"),
    ("property_background", "属性面板背景"),
    ("property_foreground", "属性面板文字"),
    ("label_foreground", "标签文字"),
    ("preview_label_color", "预览控件标签"),
]


class _ColorButton(QPushButton):
    """一个显示颜色、点击弹出的按钮。"""

    def __init__(self, initial: str, parent=None):
        super().__init__(parent)
        self._color = initial or "#000000"
        self.setFixedSize(90, 24)
        self.clicked.connect(self._pick_color)
        self._refresh()

    def color(self) -> str:
        return self._color

    def set_color(self, value: str):
        self._color = value
        self._refresh()

    def _refresh(self):
        self.setText(self._color)
        # 前景色选择：深底用白字，浅底用黑字
        c = QColor(self._color)
        lightness = c.lightness()
        fg = "#ffffff" if lightness < 128 else "#000000"
        self.setStyleSheet(
            f"background-color: {self._color}; color: {fg};"
            "border: 1px solid #888; border-radius: 2px;"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, "选择颜色")
        if c.isValid():
            self.set_color(c.name())


class SettingsDialog(QDialog):
    """返回一个 EditorSettings（accept 后调用 result_settings()）。"""

    def __init__(self, current: EditorSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑器设置")
        self.resize(520, 600)

        self._settings = EditorSettings(**vars(current))
        self._color_buttons = {}

        layout = QVBoxLayout(self)

        # --- 主题预设 ---
        preset_group = QGroupBox("主题预设")
        preset_layout = QHBoxLayout(preset_group)
        self._preset_combo = QComboBox()
        self._preset_combo.addItem("浅色 (Light)", "light")
        self._preset_combo.addItem("深色 (Dark)", "dark")
        self._preset_combo.addItem("自定义 (Custom)", "custom")
        self._preset_combo.setCurrentIndex(
            {"light": 0, "dark": 1}.get(current.theme, 2)
        )
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._preset_combo)

        btn_reset = QPushButton("恢复默认")
        btn_reset.clicked.connect(self._on_reset)
        preset_layout.addWidget(btn_reset)
        preset_layout.addStretch()

        layout.addWidget(preset_group)

        # --- 字体 ---
        font_group = QGroupBox("字体")
        font_layout = QFormLayout(font_group)

        self._font_edit = QLineEdit(self._settings.font_family)
        self._font_edit.setPlaceholderText("留空 = 系统默认")
        font_layout.addRow("字体系列", self._font_edit)

        self._font_size = QSpinBox()
        self._font_size.setRange(0, 72)
        self._font_size.setValue(self._settings.font_size)
        self._font_size.setSpecialValueText("系统默认")
        font_layout.addRow("字号 (pt)", self._font_size)

        btn_pick_font = QPushButton("从系统字体选择...")
        btn_pick_font.clicked.connect(self._on_pick_font)
        font_layout.addRow("", btn_pick_font)

        layout.addWidget(font_group)

        # --- 颜色 ---
        color_group = QGroupBox("颜色")
        color_layout = QGridLayout(color_group)
        for i, (field_name, label) in enumerate(COLOR_FIELDS):
            row = i // 2
            col = (i % 2) * 2
            color_layout.addWidget(QLabel(label), row, col)
            btn = _ColorButton(getattr(self._settings, field_name))
            self._color_buttons[field_name] = btn
            color_layout.addWidget(btn, row, col + 1)
        layout.addWidget(color_group)

        layout.addStretch()

        # --- 底部按钮 ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _on_preset_changed(self, idx: int):
        theme = self._preset_combo.itemData(idx)
        if theme == "light":
            self._apply_preset(LIGHT_PRESET)
        elif theme == "dark":
            self._apply_preset(DARK_PRESET)
        # custom：不动颜色

    def _apply_preset(self, data: dict):
        self._font_edit.setText(data.get("font_family", ""))
        self._font_size.setValue(data.get("font_size", 0))
        for field_name, _ in COLOR_FIELDS:
            btn = self._color_buttons.get(field_name)
            if btn and field_name in data:
                btn.set_color(data[field_name])

    def _on_reset(self):
        self._preset_combo.setCurrentIndex(0)
        self._apply_preset(LIGHT_PRESET)

    def _on_pick_font(self):
        initial = QFont()
        if self._font_edit.text():
            initial.setFamily(self._font_edit.text())
        if self._font_size.value() > 0:
            initial.setPointSize(self._font_size.value())
        ok, font = QFontDialog.getFont(initial, self, "选择字体")
        if ok:
            self._font_edit.setText(font.family())
            if font.pointSize() > 0:
                self._font_size.setValue(font.pointSize())

    def _on_accept(self):
        self._settings.font_family = self._font_edit.text().strip()
        self._settings.font_size = self._font_size.value()
        for field_name, _ in COLOR_FIELDS:
            setattr(self._settings, field_name,
                    self._color_buttons[field_name].color())

        # 主题标记：如果当前颜色 == light 预设 → "light"，== dark → "dark"
        # 否则 "custom"
        current_data = vars(self._settings)
        def _match(preset_data: dict) -> bool:
            for field_name, _ in COLOR_FIELDS:
                if current_data.get(field_name) != preset_data.get(field_name):
                    return False
            return True

        if _match(LIGHT_PRESET):
            self._settings.theme = "light"
        elif _match(DARK_PRESET):
            self._settings.theme = "dark"
        else:
            self._settings.theme = "custom"

        self.accept()

    def result_settings(self) -> EditorSettings:
        return self._settings