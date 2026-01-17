"""
Testes para project/core/browser.py

Valida criação de contexto de browser.
Nota: Usamos subprocess para evitar conflito Sync/Async com pytest-playwright.
"""

import pytest
import subprocess
import sys


class TestBrowserModule:
    """Testes para módulo browser.py"""
    
    def test_browser_module_imports(self):
        """Módulo browser deve ser importável"""
        from project.core.browser import create_browser_context, close_browser
        assert callable(create_browser_context)
        assert callable(close_browser)
    
    def test_create_browser_and_close_via_subprocess(self):
        """
        Testa criação e fechamento de browser via subprocess.
        Evita conflito com asyncio do pytest-playwright.
        """
        code = """
import sys
from project.core.browser import create_browser_context, close_browser
try:
    browser, context, page = create_browser_context(headless=True)
    page.set_content("<html><body>Test</body></html>")
    assert "Test" in page.content()
    close_browser(browser, context)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert result.returncode == 0, f"Subprocess falhou: {result.stderr}"
        assert "SUCCESS" in result.stdout, f"Output: {result.stdout}"
