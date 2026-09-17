# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件 —— 无控制台版本。
用法：
    pyinstaller editor_silent.spec --noconfirm
生成：
    dist/OBS脚本编辑器_silent.exe
"""
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules("PySide6.QtCore")
hiddenimports += collect_submodules("PySide6.QtGui")
hiddenimports += collect_submodules("PySide6.QtWidgets")

hiddenimports += [
    "editor",
    "editor._bootstrap",
    "editor.logging_config",
    "editor.session_manager",
    "editor.settings_manager",
    "editor.model",
    "editor.model.csv_io",
    "editor.model.diff",
    "editor.model.function_editor",
    "editor.model.function_registry",
    "editor.model.props_utils",
    "editor.model.template_generator",
    "editor.model.validator",
    "editor.model.value_resolver",
    "editor.model.variant_registry",
    "editor.model.widget_node",
    "editor.model.widget_tree",
    "editor.ui",
    "editor.ui.main_window",
    "editor.ui.tree_panel",
    "editor.ui.preview_panel",
    "editor.ui.property_panel",
    "editor.ui.commands",
    "editor.ui.collapsible_section",
    "editor.ui.diff_dialog",
    "editor.ui.export_dialog",
    "editor.ui.function_editor_dialog",
    "editor.ui.new_node_dialog",
    "editor.ui.settings_dialog",
    "editor.ui.style_utils",
]

a = Analysis(
    ['editor_main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "PIL",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtMultimedia",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="OBS脚本编辑器_silent",   # 名字带 _silent 后缀
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # 关键：无控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)