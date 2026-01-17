"""
Testes para project/core/artifacts.py

Valida criação de diretórios e geração de run_id.
"""

import pytest
from pathlib import Path

from project.core.artifacts import generate_run_id, create_run_dirs


class TestGenerateRunId:
    """Testes para generate_run_id()"""
    
    def test_run_id_format(self):
        """Run ID deve ter formato YYYYMMDD_HHMMSS_XXXX"""
        run_id = generate_run_id()
        
        parts = run_id.split("_")
        assert len(parts) == 3, "Run ID deve ter 3 partes separadas por _"
        assert len(parts[0]) == 8, "Data deve ter 8 caracteres (YYYYMMDD)"
        assert len(parts[1]) == 6, "Hora deve ter 6 caracteres (HHMMSS)"
        assert len(parts[2]) == 4, "Sufixo deve ter 4 caracteres"
    
    def test_run_id_unique(self):
        """Run IDs gerados em sequência devem ser únicos"""
        ids = [generate_run_id() for _ in range(10)]
        assert len(set(ids)) == 10, "Todos os IDs devem ser únicos"


class TestCreateRunDirs:
    """Testes para create_run_dirs()"""
    
    def test_creates_all_directories(self, temp_artifacts_dir):
        """Deve criar todos os subdiretórios esperados"""
        run_id = "20260117_120000_test"
        dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
        
        # Verifica retorno
        assert "run" in dirs
        assert "html" in dirs
        assert "screenshots" in dirs
        assert "food" in dirs
        assert "logs" in dirs
        
        # Verifica existência (converte para Path se necessário)
        for key, value in dirs.items():
            path = Path(value) if isinstance(value, str) else value
            assert path.exists(), f"Diretório {key} deve existir"
    
    def test_directories_structure(self, temp_artifacts_dir):
        """Deve criar estrutura correta de diretórios"""
        run_id = "20260117_120000_test"
        dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
        
        # Verifica que todos os valores são acessíveis como paths
        for key, value in dirs.items():
            path = Path(value) if isinstance(value, str) else value
            assert path.is_dir(), f"{key} deve ser um diretório"
