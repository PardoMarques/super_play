"""
English:
Tests for project/core/artifacts.py
Validates directory creation and run_id generation.

Português:
Testes para project/core/artifacts.py
Valida criação de diretórios e geração de run_id.
"""

import pytest
from pathlib import Path

from project.core.artifacts import generate_run_id, create_run_dirs


class TestGenerateRunId:
    """PT: Testes para generate_run_id()"""
    """EN: Tests for generate_run_id()"""
    
    def test_run_id_format(self):
        """PT: Run ID deve ter formato YYYYMMDD_HHMMSS_XXXX"""
        """EN: Run ID must have format YYYYMMDD_HHMMSS_XXXX"""
        run_id = generate_run_id()
        
        parts = run_id.split("_")
        assert len(parts) == 3, "Run ID must have 3 parts separated by _"
        assert len(parts[0]) == 8, "Date must have 8 characters (YYYYMMDD)"
        assert len(parts[1]) == 6, "Time must have 6 characters (HHMMSS)"
        assert len(parts[2]) == 6, "Suffix must have 6 characters"
    
    def test_run_id_unique(self):
        """PT: IDs gerados em sequência devem ser únicos"""
        """EN: Run IDs generated in sequence must be unique"""
        ids = [generate_run_id() for _ in range(10)]
        assert len(set(ids)) == 10, "All IDs must be unique"


class TestCreateRunDirs:
    """PT: Testes para create_run_dirs()"""
    """EN: Tests for create_run_dirs()"""
    
    def test_creates_all_directories(self, temp_artifacts_dir):
        """PT: Deve criar todas as subdiretórios esperados"""
        """EN: Must create all expected subdirectories"""
        run_id = "20260117_120000_test"
        dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
        
        # Verify return
        assert "run" in dirs
        assert "html" in dirs
        assert "screenshots" in dirs
        assert "food" in dirs
        assert "logs" in dirs
        
        # Verify existence (convert to Path if needed)
        for key, value in dirs.items():
            path = Path(value) if isinstance(value, str) else value
            assert path.exists(), f"Directory {key} must exist"
    
    def test_directories_structure(self, temp_artifacts_dir):
        """PT: Deve criar estrutura de diretórios correta"""
        """EN: Must create correct directory structure"""
        run_id = "20260117_120000_test"
        dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
        
        # Verify all values are accessible as paths
        for key, value in dirs.items():
            path = Path(value) if isinstance(value, str) else value
            assert path.is_dir(), f"{key} must be a directory"
