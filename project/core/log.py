"""Utilitários de logging com suporte a arquivo."""

import logging
import sys
from pathlib import Path
from typing import Optional


# Handler de arquivo global para sessão
_file_handler: Optional[logging.FileHandler] = None


def setup_file_logging(log_path: Path, level: Optional[int] = None) -> None:
    """
    Configura logging para arquivo.
    
    Args:
        log_path: Caminho para o arquivo de log.
        level: Nível de log. Padrão: INFO.
    """
    global _file_handler
    
    level = level or logging.INFO
    
    # Garante diretório existe
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Cria handler de arquivo
    _file_handler = logging.FileHandler(log_path, encoding="utf-8")
    _file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _file_handler.setFormatter(formatter)
    
    # Adiciona ao logger raiz
    root_logger = logging.getLogger()
    root_logger.addHandler(_file_handler)
    root_logger.setLevel(level)


def close_file_logging() -> None:
    """Fecha o handler de arquivo."""
    global _file_handler
    
    if _file_handler:
        _file_handler.close()
        root_logger = logging.getLogger()
        root_logger.removeHandler(_file_handler)
        _file_handler = None


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Obtém uma instância de logger configurada.
    
    Cria um logger com handler de stream e formatador básico.
    
    Args:
        name: Nome do logger (tipicamente __name__).
        level: Nível de log opcional. Padrão: INFO.
    
    Returns:
        Instância de Logger configurada.
    """
    logger = logging.getLogger(name)
    
    # Só configura se não houver handlers
    if not logger.handlers:
        level = level or logging.INFO
        logger.setLevel(level)
        
        # Handler de stream para stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Formatador básico
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
