"""编辑器入口。"""
import sys
from pathlib import Path

# 先把父目录加入 sys.path，否则 import editor 会失败
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from editor._bootstrap import bootstrap
bootstrap()

from editor.logging_config import setup_logging
log = setup_logging()

from PySide6.QtWidgets import QApplication
from editor.ui.main_window import MainWindow


def main():
    log.info("编辑器启动")
    app = QApplication(sys.argv)
    app.setApplicationName("OBS Script Framework Editor")

    from editor.settings_manager import load_settings
    from editor.ui.style_utils import apply_to_app
    apply_to_app(app, load_settings())

    try:
        window = MainWindow()
        window.show()
        exit_code = app.exec()
        log.info(f"编辑器退出，exit_code={exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        from editor.logging_config import log_exception
        log_exception(log, "编辑器主循环异常", e)
        raise


if __name__ == "__main__":
    main()