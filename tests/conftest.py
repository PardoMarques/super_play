"""
English:
Fixtures configuration for Gen Food tests.
Defines reusable fixtures for:
- Evidence directory (1 per pytest session)
- Test data

Português:
Configuração de fixtures para testes do Gen Food.
Define fixtures reutilizáveis para:
- Diretório de evidências (1 por sessão do pytest)
- Dados de teste
"""

import pytest
from pathlib import Path
from datetime import datetime


# Base evidence directory
EVIDENCE_DIR = Path(__file__).parent / "evidence"


def pytest_configure(config):
    """PT: Cria diretório de evidências no início da sessão."""
    """EN: Creates evidence directory at session start."""
    EVIDENCE_DIR.mkdir(exist_ok=True)


# Global variable to keep same folder during entire session
_session_evidence_dir = None


@pytest.fixture(scope="session")
def session_evidence_dir():
    """
    PT: Cria UM diretório de evidências para toda a sessão do pytest.
    EN: Creates ONE evidence directory for entire pytest session.
    All tests in session use the same directory.
    """
    global _session_evidence_dir
    
    if _session_evidence_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _session_evidence_dir = EVIDENCE_DIR / f"run_{timestamp}"
        _session_evidence_dir.mkdir(parents=True, exist_ok=True)
    
    return _session_evidence_dir


@pytest.fixture
def temp_artifacts_dir(session_evidence_dir, request):
    """
    PT: Cria subdiretório para cada teste dentro da pasta da sessão.
    EN: Creates subdirectory for each test inside session folder.
    Structure: evidence/run_<timestamp>/<test_name>/
    """
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    test_dir = session_evidence_dir / test_name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def temp_run_dirs(temp_artifacts_dir):
    """
    PT: Cria estrutura completa de diretórios para os testes.
    EN: Creates complete run directory structure for tests.
    """
    from project.core.artifacts import create_run_dirs, generate_run_id
    
    run_id = generate_run_id()
    dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
    return dirs


@pytest.fixture
def sample_html():
    """
    PT: HTML de exemplo para testes de extração.
    EN: Sample HTML for extraction tests.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <form id="login-form">
            <input type="text" id="username" name="username" placeholder="User">
            <input type="password" id="password" name="password" placeholder="Password">
            <button type="submit" id="submit-btn" data-testid="login-button">Enter</button>
        </form>
        <a href="/dashboard" aria-label="Go to Dashboard">Dashboard</a>
    </body>
    </html>
    """
