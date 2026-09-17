"""
编辑器日志配置。

- 输出到 项目根/LOG/editor_YYYYMMDD_HHMMSS.log
- 同时输出到 stderr，方便开发时直接看
- 保留最多 MAX_LOG_FILES 个历史日志
"""
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

# editor/logging_config.py -> editor -> 项目根
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIR = _PROJECT_ROOT / "LOG"

MAX_LOG_FILES = 30
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    初始化根 logger。多次调用只生效一次。
    返回编辑器专用的 logger。
    """
    global _logger, _log_file_path

    if _logger is not None:
        return _logger

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = _LOG_DIR / f"editor_{timestamp}.log"
    _log_file_path = log_file

    root = logging.getLogger()
    root.setLevel(level)

    # 清理旧 handler
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 文件 handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 控制台 handler
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    _logger = logging.getLogger("editor")
    _logger.info(f"日志已初始化: {log_file}")

    _cleanup_old_logs()
    _install_global_excepthook()

    return _logger


def get_logger() -> logging.Logger:
    """获取编辑器 logger。未初始化时自动初始化。"""
    if _logger is None:
        return setup_logging()
    return _logger


def get_log_file_path() -> Optional[Path]:
    return _log_file_path


def get_log_dir() -> Path:
    return _LOG_DIR


def log_exception(logger: logging.Logger, context: str, exc: BaseException) -> None:
    """记录异常及其堆栈。"""
    logger.error(
        f"{context}: {type(exc).__name__}: {exc}\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )


# ----------------------------------------------------------------------
# 全局异常钩子
# ----------------------------------------------------------------------
def _install_global_excepthook() -> None:
    """捕获未处理异常，写入日志。"""
    original_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        logging.getLogger("editor").critical(
            "未捕获异常:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        # 保留默认行为（打印到 stderr）
        original_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def _cleanup_old_logs() -> None:
    """删除超出数量限制的旧日志。"""
    try:
        log_files = sorted(
            _LOG_DIR.glob("editor_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in log_files[MAX_LOG_FILES:]:
            try:
                old.unlink()
            except OSError:
                pass
    except Exception:
        pass