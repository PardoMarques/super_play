"""
Artifact and run directory management.
Gerenciamento de artefatos e diretorios de execucao.
"""

import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict


def generate_run_id() -> str:
    """
    Generates a unique execution ID.
    Gera um ID unico de execucao.
    
    Format: YYYYMMDD_HHMMSS_<6hex>
    
    Returns:
        Unique string identifier for the execution.
        String identificadora unica da execucao.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hex_suffix = secrets.token_hex(3)  # 6 hex characters (16M combinations)
    return f"{timestamp}_{hex_suffix}"


def create_run_dirs(artifacts_dir: Path | str, run_id: str) -> Dict[str, Path]:
    """
    Creates directory structure for a run.
    
    Creates:
        artifacts/runs/<run_id>/
            - logs/
            - food/
            - html/
            - screenshots/
    
    Args:
        artifacts_dir: Base artifacts directory (str or Path).
        run_id: Unique execution identifier.
    
    Returns:
        Dictionary with paths to each subdirectory.
    """
    # Ensure artifacts_dir is Path
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
    
    # Create all directories
    for path in subdirs.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return subdirs
