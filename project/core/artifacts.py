"""Gerenciamento de artefatos e diretórios de execução."""

import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict


def generate_run_id() -> str:
    """
    Gera um ID único de execução.
    
    Formato: YYYYMMDD_HHMMSS_<4hex>
    
    Returns:
        String identificadora única da execução.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hex_suffix = secrets.token_hex(2)  # 4 caracteres hexadecimais
    return f"{timestamp}_{hex_suffix}"


def create_run_dirs(artifacts_dir: Path | str, run_id: str) -> Dict[str, Path]:
    """
    Cria a estrutura de diretórios para uma execução.
    
    Cria:
        artifacts/runs/<run_id>/
            ├── logs/
            ├── food/
            ├── html/
            └── screenshots/
    
    Args:
        artifacts_dir: Diretório base de artefatos (str ou Path).
        run_id: Identificador único da execução.
    
    Returns:
        Dicionário com os caminhos de cada subdiretório.
    """
    # Garante que artifacts_dir é Path
    if isinstance(artifacts_dir, str):
        artifacts_dir = Path(artifacts_dir)
    
    run_dir = artifacts_dir / "runs" / run_id
    
    subdirs = {
        "run": run_dir,
        "logs": run_dir / "logs",
        "food": run_dir / "food",
        "html": run_dir / "html",
        "screenshots": run_dir / "screenshots",
    }
    
    # Cria todos os diretórios
    for path in subdirs.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return subdirs
