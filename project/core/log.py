"""Utilitários de logging."""

import logging
import sys
from typing import Optional


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
