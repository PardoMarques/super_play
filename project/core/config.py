"""
Configuration loader with .env support.
Carregador de configuracao com suporte a .env.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Try loading dotenv, fallback if not installed
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False


@dataclass
class Config:
    """Application configuration."""
    
    base_url: Optional[str]
    artifacts_dir: Path
    
    def __post_init__(self):
        # Ensure artifacts_dir is a Path
        if isinstance(self.artifacts_dir, str):
            self.artifacts_dir = Path(self.artifacts_dir)


def get_config(env_path: Optional[str] = None) -> Config:
    """
    Loads configuration from environment variables.
    
    Loads .env file if python-dotenv is installed.
    
    Args:
        env_path: Optional path to .env file. Default: .env in cwd.
    
    Returns:
        Config object with loaded values.
    """
    # Load .env if available
    if _HAS_DOTENV:
        env_file = Path(env_path) if env_path else Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
    
    # Get values with defaults
    base_url = os.getenv("BASE_URL")
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "./artifacts")
    
    return Config(
        base_url=base_url,
        artifacts_dir=Path(artifacts_dir)
    )
