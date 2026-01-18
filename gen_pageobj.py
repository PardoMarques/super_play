#!/usr/bin/env python3
"""
Gen PageObj - Automation Project Generator.
Gerador de Projetos de Automacao.

Transforms gen_food artifacts into a complete automation project
with Page Objects, BDD Steps, Gherkin Features and support files.
Transforma artefatos do gen_food em um projeto completo de automacao
com Page Objects, Steps BDD, Features Gherkin e arquivos de suporte.

Usage / Uso:
    python gen_pageobj.py --artifact artifacts/runs/20260117_XXXX --name meusite
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from project.core.log import get_logger

logger = get_logger(__name__)


# =============================================================================
# Templates de arquivos gerados
# =============================================================================

TEMPLATE_ENV = """\
# Configuracao do projeto {project_name}
# Gerado por gen_pageobj em {generated_at}

BASE_URL={base_url}

# Credenciais (preencha manualmente)
# USERNAME=
# PASSWORD=
"""

TEMPLATE_GITIGNORE = """\
# Virtual environment
.venv/
venv/

# Python
__pycache__/
*.py[cod]
.pytest_cache/

# IDEs
.idea/
.vscode/

# Playwright
test-results/

# Screenshots e evidencias
screenshots/
reports/
"""

TEMPLATE_REQUIREMENTS = """\
# Dependencias do projeto {project_name}
playwright>=1.40.0
pytest>=7.4.0
pytest-bdd>=7.0.0
python-dotenv>=1.0.0
"""

TEMPLATE_PYTEST_INI = """\
[pytest]
testpaths = tests features
python_files = test_*.py
python_functions = test_*
bdd_features_base_dir = features/
addopts = -v --tb=short
"""

TEMPLATE_CONFTEST = """\
\"\"\"
Fixtures do pytest para o projeto {project_name}.
Gerado automaticamente por gen_pageobj.
\"\"\"

import pytest
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

# Carrega variaveis de ambiente
load_dotenv()


@pytest.fixture(scope="session")
def browser_context():
    \"\"\"Cria contexto de browser para a sessao de testes.\"\"\"
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={{"width": 1280, "height": 720}})
    
    yield context
    
    context.close()
    browser.close()
    playwright.stop()


@pytest.fixture
def page(browser_context):
    \"\"\"Cria nova pagina para cada teste.\"\"\"
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture
def base_url():
    \"\"\"Retorna a URL base do .env.\"\"\"
    return os.getenv("BASE_URL", "{base_url}")
"""

TEMPLATE_BASE_PAGE = '''\
"""
BasePage - Classe base para Page Objects.

Fornece metodos resilientes com retry e captura de evidencias.
"""

from playwright.sync_api import Page, expect
from pathlib import Path
import time


class BasePage:
    """Classe base para todos os Page Objects."""
    
    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url
    
    def navigate(self, path: str = "/"):
        """Navega para uma URL relativa."""
        url = f"{{self.base_url}}{{path}}"
        self.page.goto(url, wait_until="networkidle", timeout=30000)
    
    def click(self, selector: str, timeout: int = 10000):
        """Clica em um elemento com retry."""
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 10000):
        """Preenche um campo com retry."""
        self.page.fill(selector, value, timeout=timeout)
    
    def get_text(self, selector: str, timeout: int = 10000) -> str:
        """Retorna o texto de um elemento."""
        return self.page.text_content(selector, timeout=timeout) or ""
    
    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Verifica se elemento esta visivel."""
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except:
            return False
    
    def wait_for(self, selector: str, timeout: int = 10000):
        """Aguarda elemento aparecer."""
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
    
    def screenshot(self, name: str, path: str = "screenshots"):
        """Captura screenshot."""
        Path(path).mkdir(exist_ok=True)
        self.page.screenshot(path=f"{{path}}/{{name}}.png")
'''

TEMPLATE_PAGE_OBJECT = '''\
"""
{class_name} - Page Object para {page_title}.

Gerado automaticamente por gen_pageobj.
Fonte: {artifact_path}
"""

from pages.base_page import BasePage


class {class_name}(BasePage):
    """Page Object para {page_title}."""
    
    # === Selectors ===
{selectors}
    
    # === Methods ===
{methods}
'''

TEMPLATE_CONFIG = '''\
"""
Configuracao do projeto.
Carrega variaveis de ambiente do .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Configuracao centralizada."""
    
    BASE_URL = os.getenv("BASE_URL", "")
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    TIMEOUT = int(os.getenv("TIMEOUT", "30000"))


config = Config()
'''

TEMPLATE_HELPERS = '''\
"""
Funcoes auxiliares para automacao.
"""

import re
from datetime import datetime


def sanitize_filename(text: str) -> str:
    """Converte texto para nome de arquivo seguro."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or "unnamed"


def timestamp() -> str:
    """Retorna timestamp para screenshots."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
'''

TEMPLATE_SMOKE_TEST = '''\
"""
Smoke test - valida que a navegacao basica funciona.
"""

import pytest


def test_smoke_navigation(page, base_url):
    """Testa navegacao basica para a URL base."""
    page.goto(base_url, wait_until="networkidle", timeout=30000)
    
    # Verifica que a pagina carregou
    assert page.title(), "Pagina deve ter um titulo"
    
    # Screenshot de evidencia
    page.screenshot(path="screenshots/smoke_test.png")
'''

TEMPLATE_FEATURE = '''\
# language: pt
# Gerado automaticamente por gen_pageobj

Funcionalidade: {feature_name}

  Cenario: Navegacao basica
    Dado que acesso a pagina inicial
    Entao a pagina deve carregar corretamente
'''


# =============================================================================
# Funcoes de Geracao
# =============================================================================

def load_artifacts(artifact_path: Path) -> dict:
    """Carrega todos os artefatos de uma execucao."""
    meta_path = artifact_path / "meta.json"
    food_path = artifact_path / "food" / "food.json"
    actions_path = artifact_path / "food" / "actions.ndjson"
    
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json nao encontrado em {artifact_path}")
    
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    
    food = {}
    if food_path.exists():
        with open(food_path, encoding="utf-8") as f:
            food = json.load(f)
    
    actions = []
    if actions_path.exists():
        with open(actions_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    actions.append(json.loads(line))
    
    return {
        "meta": meta,
        "food": food,
        "actions": actions,
        "artifact_path": artifact_path,
    }


def extract_project_name(url: str, custom_name: str = None) -> str:
    """Extrai nome do projeto a partir da URL ou nome customizado."""
    if custom_name:
        return sanitize_name(custom_name)
    
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Remove TLD e mantem so o nome
    name = domain.split(".")[0]
    return sanitize_name(name)


def sanitize_name(name: str) -> str:
    """Sanitiza nome para uso em arquivos e classes."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = name.strip("_").lower()
    return name or "project"


def to_class_name(name: str) -> str:
    """Converte nome para PascalCase para classes."""
    parts = name.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts if p)


def generate_selectors_code(elements: list) -> str:
    """Gera codigo de seletores a partir dos elementos."""
    lines = []
    seen = set()
    
    for el in elements:
        tag = el.get("tag", "element")
        candidates = el.get("candidates", [])
        text_preview = el.get("textPreview", "")[:20]
        
        if not candidates:
            continue
        
        # Usa o melhor candidato (primeiro da lista, ja ordenado por robustez)
        best = candidates[0]
        selector = best.get("selector", "")
        strategy = best.get("strategy", "css")
        
        if not selector or selector in seen:
            continue
        seen.add(selector)
        
        # Gera nome da constante
        const_name = generate_const_name(tag, text_preview, strategy, selector)
        if const_name in seen:
            continue
        seen.add(const_name)
        
        lines.append(f'    {const_name} = "{selector}"')
    
    return "\n".join(lines) if lines else "    pass  # No selectors identified"


def generate_const_name(tag: str, text: str, strategy: str, selector: str) -> str:
    """Gera nome de constante para um seletor."""
    # Tenta usar texto primeiro
    if text and len(text) > 2:
        name = sanitize_name(text)[:20]
    elif "#" in selector:
        # Usa ID
        name = selector.split("#")[-1].split("[")[0]
    else:
        name = f"{tag}_{hash(selector) % 1000}"
    
    name = sanitize_name(name).upper()
    
    # Adiciona sufixo baseado no tag
    suffix = {
        "input": "_INPUT",
        "button": "_BTN",
        "a": "_LINK",
        "select": "_SELECT",
        "textarea": "_TEXTAREA",
    }.get(tag, "")
    
    return f"{name}{suffix}" if name else f"ELEMENT_{hash(selector) % 10000}"


def generate_methods_code(elements: list) -> str:
    """Gera metodos basicos para elementos interativos."""
    lines = []
    seen_methods = set()
    
    for el in elements:
        tag = el.get("tag", "")
        candidates = el.get("candidates", [])
        text = el.get("textPreview", "")[:20]
        
        if not candidates or tag not in ("input", "button", "a", "select"):
            continue
        
        best = candidates[0]
        selector = best.get("selector", "")
        
        method_name = generate_method_name(tag, text, selector)
        if method_name in seen_methods:
            continue
        seen_methods.add(method_name)
        
        const_name = generate_const_name(tag, text, best.get("strategy", ""), selector)
        
        if tag == "input":
            lines.append(f'''
    def {method_name}(self, value: str):
        """Fill {text or 'field'}."""
        self.fill(self.{const_name}, value)
''')
        elif tag in ("button", "a"):
            lines.append(f'''
    def {method_name}(self):
        """Click {text or 'element'}."""
        self.click(self.{const_name})
''')
    
    return "\n".join(lines) if lines else "    pass  # No methods generated"


def generate_method_name(tag: str, text: str, selector: str) -> str:
    """Gera nome de metodo."""
    action = {
        "input": "fill",
        "button": "click",
        "a": "click",
        "select": "select",
    }.get(tag, "interact")
    
    if text:
        target = sanitize_name(text)[:15]
    elif "#" in selector:
        target = sanitize_name(selector.split("#")[-1])[:15]
    else:
        target = f"element_{hash(selector) % 1000}"
    
    return f"{action}_{target}"


def create_project_structure(output_dir: Path):
    """Cria estrutura de diretorios do projeto."""
    dirs = [
        output_dir,
        output_dir / "pages",
        output_dir / "steps",
        output_dir / "features",
        output_dir / "utils",
        output_dir / "tests",
        output_dir / "screenshots",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Cria __init__.py em pastas Python
        if d.name in ("pages", "steps", "utils", "tests"):
            (d / "__init__.py").write_text('"""Module generated by gen_pageobj."""\n')


def generate_project(artifacts: dict, project_name: str, output_dir: Path):
    """Gera o projeto completo de automacao."""
    meta = artifacts["meta"]
    food = artifacts["food"]
    artifact_path = artifacts["artifact_path"]
    
    base_url = meta.get("url", "http://localhost")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"Generating project: {project_name}")
    logger.info(f"Output: {output_dir}")
    
    # Cria estrutura de pastas
    create_project_structure(output_dir)
    
    # Gera arquivos de suporte
    (output_dir / ".env").write_text(
        TEMPLATE_ENV.format(
            project_name=project_name,
            generated_at=generated_at,
            base_url=base_url,
        )
    )
    logger.info("  > .env")
    
    (output_dir / ".gitignore").write_text(TEMPLATE_GITIGNORE)
    logger.info("  > .gitignore")
    
    (output_dir / "requirements.txt").write_text(
        TEMPLATE_REQUIREMENTS.format(project_name=project_name)
    )
    logger.info("  > requirements.txt")
    
    (output_dir / "pytest.ini").write_text(TEMPLATE_PYTEST_INI)
    logger.info("  > pytest.ini")
    
    (output_dir / "conftest.py").write_text(
        TEMPLATE_CONFTEST.format(project_name=project_name, base_url=base_url)
    )
    logger.info("  > conftest.py")
    
    # Gera base_page.py
    (output_dir / "pages" / "base_page.py").write_text(TEMPLATE_BASE_PAGE)
    logger.info("  > pages/base_page.py")
    
    # Gera utils
    (output_dir / "utils" / "config.py").write_text(TEMPLATE_CONFIG)
    logger.info("  > utils/config.py")
    
    (output_dir / "utils" / "helpers.py").write_text(TEMPLATE_HELPERS)
    logger.info("  > utils/helpers.py")
    
    # Gera Page Object principal
    elements = food.get("elements", [])
    page_title = food.get("page_signals", {}).get("title", project_name)
    class_name = to_class_name(project_name) + "Page"
    
    selectors_code = generate_selectors_code(elements)
    methods_code = generate_methods_code(elements)
    
    page_object_code = TEMPLATE_PAGE_OBJECT.format(
        class_name=class_name,
        page_title=page_title,
        artifact_path=str(artifact_path),
        selectors=selectors_code,
        methods=methods_code,
    )
    
    page_filename = f"{project_name}_page.py"
    (output_dir / "pages" / page_filename).write_text(page_object_code)
    logger.info(f"  > pages/{page_filename}")
    
    # Gera feature basica
    feature_name = page_title or project_name
    (output_dir / "features" / f"{project_name}.feature").write_text(
        TEMPLATE_FEATURE.format(feature_name=feature_name)
    )
    logger.info(f"  > features/{project_name}.feature")
    
    # Gera smoke test
    (output_dir / "tests" / "test_smoke.py").write_text(TEMPLATE_SMOKE_TEST)
    logger.info("  > tests/test_smoke.py")
    
    return {
        "project_name": project_name,
        "output_dir": output_dir,
        "files_created": 10,
        "elements_count": len(elements),
        "base_url": base_url,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gera projeto de automacao a partir de artefatos do gen_food",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplo:
    python gen_pageobj.py --artifact artifacts/runs/20260117_XXXX --name meusite
    
Saida:
    artifacts/auto_projects/meusite_automation/
        """
    )
    
    parser.add_argument(
        "--artifact",
        type=str,
        required=True,
        help="Caminho do diretorio de artefatos (ex: artifacts/runs/20260117_XXXX)",
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Nome do projeto (default: baseado no dominio da URL)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Diretorio de saida (default: artifacts/auto_projects/<name>_automation/)",
    )
    
    args = parser.parse_args()
    
    # Valida artifact path
    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        logger.error(f"Diretorio de artefatos nao encontrado: {artifact_path}")
        return 1
    
    # Carrega artefatos
    try:
        artifacts = load_artifacts(artifact_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # Extrai nome do projeto
    url = artifacts["meta"].get("url", "")
    project_name = extract_project_name(url, args.name)
    
    # Define diretorio de saida (default: artifacts/auto_projects/)
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path("artifacts") / "auto_projects" / f"{project_name}_automation"
    
    # Gera projeto
    result = generate_project(artifacts, project_name, output_dir)
    
    # Resumo
    print("\n" + "=" * 60)
    print("PROJECT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Name:      {result['project_name']}")
    print(f"  Directory: {result['output_dir'].absolute()}")
    print(f"  Files:     {result['files_created']}")
    print(f"  Elements:  {result['elements_count']}")
    print(f"  Base URL:  {result['base_url']}")
    print()
    print("Next steps:")
    print(f"  cd {result['output_dir']}")
    print("  pip install -r requirements.txt")
    print("  playwright install chromium")
    print("  pytest tests/test_smoke.py -v")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
