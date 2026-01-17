"""
Configuração de fixtures para testes do Gen Food.

Define fixtures reutilizáveis para:
- Diretório de evidências (1 por sessão pytest)
- Dados de teste
"""

import pytest
from pathlib import Path
from datetime import datetime


# Diretório base de evidências
EVIDENCE_DIR = Path(__file__).parent / "evidence"


def pytest_configure(config):
    """Cria diretório de evidências no início da sessão."""
    EVIDENCE_DIR.mkdir(exist_ok=True)


# Variável global para manter a mesma pasta durante toda a sessão
_session_evidence_dir = None


@pytest.fixture(scope="session")
def session_evidence_dir():
    """
    Cria UM diretório de evidências para toda a sessão pytest.
    Todos os testes da sessão usam o mesmo diretório.
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
    Cria subdiretório para cada teste dentro da pasta da sessão.
    Estrutura: evidence/run_<timestamp>/<nome_do_teste>/
    """
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    test_dir = session_evidence_dir / test_name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def temp_run_dirs(temp_artifacts_dir):
    """
    Cria estrutura completa de diretórios de run para testes.
    """
    from project.core.artifacts import create_run_dirs, generate_run_id
    
    run_id = generate_run_id()
    dirs = create_run_dirs(str(temp_artifacts_dir), run_id)
    return dirs


@pytest.fixture
def sample_html():
    """HTML de exemplo para testes de extração."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Página de Teste</title></head>
    <body>
        <form id="login-form">
            <input type="text" id="username" name="username" placeholder="Usuário">
            <input type="password" id="password" name="password" placeholder="Senha">
            <button type="submit" id="submit-btn" data-testid="login-button">Entrar</button>
        </form>
        <a href="/dashboard" aria-label="Ir para Dashboard">Dashboard</a>
    </body>
    </html>
    """
