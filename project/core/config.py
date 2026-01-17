"""Carregador de configuração com suporte a .env."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Tenta carregar dotenv, faz fallback se não estiver instalado
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False


@dataclass
class Config:
    """Configuração da aplicação."""
    
    base_url: Optional[str]
    artifacts_dir: Path
    
    def __post_init__(self):
        # Garante que artifacts_dir seja um Path
        if isinstance(self.artifacts_dir, str):
            self.artifacts_dir = Path(self.artifacts_dir)


def get_config(env_path: Optional[str] = None) -> Config:
    """
    Carrega configuração das variáveis de ambiente.
    
    Carrega arquivo .env se python-dotenv estiver instalado.
    
    Args:
        env_path: Caminho opcional para arquivo .env. Padrão: .env no cwd.
    
    Returns:
        Objeto Config com os valores carregados.
    """
    # Carrega .env se disponível
    if _HAS_DOTENV:
        env_file = Path(env_path) if env_path else Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
    
    # Obtém valores com defaults
    base_url = os.getenv("BASE_URL")
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "./artifacts")
    
    return Config(
        base_url=base_url,
        artifacts_dir=Path(artifacts_dir)
    )
