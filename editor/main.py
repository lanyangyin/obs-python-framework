"""编辑器入口。"""
import sys
from pathlib import Path

# 先把父目录加入 sys.path，否则 import editor 会失败
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from editor._bootstrap import bootstrap
bootstrap()

from PySide6.QtWidgets import QApplication
from editor.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OBS Script Framework Editor")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()