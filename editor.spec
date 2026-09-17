# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件。
用法：
    pyinstaller editor.spec --noconfirm
生成：
    dist/OBS脚本编辑器.exe
"""
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# 收集 PySide6 相关子模块（PyInstaller 有时会漏掉）
hiddenimports = []
hiddenimports += collect_submodules("PySide6.QtCore")
hiddenimports += collect_submodules("PySide6.QtGui")
hiddenimports += collect_submodules("PySide6.QtWidgets")

# 编辑器自己的模块
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
        # 排除明显用不到的大模块
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
    name="OBS脚本编辑器",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # 保留控制台，方便看日志；改成 False 则完全无窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="editor/icon.ico",  # 有图标时启用
)