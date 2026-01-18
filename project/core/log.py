"""
Logging utilities with file support.
Utilitarios de logging com suporte a arquivo.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# Global file handler for session
_file_handler: Optional[logging.FileHandler] = None


def setup_file_logging(log_path: Path, level: Optional[int] = None) -> None:
    """
    Configures file logging.
    
    Args:
        log_path: Path to log file.
        level: Log level. Default: INFO.
    """
    global _file_handler
    
    level = level or logging.INFO
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    _file_handler = logging.FileHandler(log_path, encoding="utf-8")
    _file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _file_handler.setFormatter(formatter)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(_file_handler)
    root_logger.setLevel(level)


def close_file_logging() -> None:
    """Closes file handler."""
    global _file_handler
    
    if _file_handler:
        _file_handler.close()
        root_logger = logging.getLogger()
        root_logger.removeHandler(_file_handler)
        _file_handler = None


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Gets a configured logger instance.
    
    Creates logger with stream handler and basic formatter.
    
    Args:
        name: Logger name (typically __name__).
        level: Optional log level. Default: INFO.
    
    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist
    if not logger.handlers:
        level = level or logging.INFO
        logger.setLevel(level)
        
        # Stream handler for stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Basic formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
