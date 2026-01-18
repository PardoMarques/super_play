"""
English:
Tests for project/core/browser.py
Validates browser context creation.
Note: Uses subprocess to avoid Sync/Async conflict with pytest-playwright.

Português:
Testes para project/core/browser.py
Valida criação de contexto do navegador.
Nota: Usa subprocess para evitar conflito Sync/Async com pytest-playwright.
"""

import pytest
import subprocess
import sys


class TestBrowserModule:
    """PT: Testes para browser.py module"""
    """EN: Tests for browser.py module"""
    
    def test_browser_module_imports(self):
        """PT: Módulo browser.py deve ser importável"""
        """EN: Browser module must be importable"""
        from project.core.browser import create_browser_context, close_browser
        assert callable(create_browser_context)
        assert callable(close_browser)
    
    def test_create_browser_and_close_via_subprocess(self):
        """
        PT: Testa criação e fechamento do navegador via subprocess.
        EN: Tests browser creation and closing via subprocess.
        Avoids conflict with pytest-playwright asyncio.
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
        
        assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
        assert "SUCCESS" in result.stdout, f"Output: {result.stdout}"
