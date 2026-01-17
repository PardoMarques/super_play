"""Utilitários principais do Super Play."""

from .config import get_config
from .artifacts import create_run_dirs, generate_run_id
from .log import get_logger
from .browser import create_browser_context, close_browser
from .elements import extract_elements, capture_snapshot
from .recorder import ActionRecorder, setup_recorder

__all__ = [
    "get_config",
    "create_run_dirs",
    "generate_run_id",
    "get_logger",
    "create_browser_context",
    "close_browser",
    "extract_elements",
    "capture_snapshot",
    "ActionRecorder",
    "setup_recorder",
]


