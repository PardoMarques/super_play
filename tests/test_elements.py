"""
Testes para project/core/elements.py

Valida extração de elementos e geração de candidatos de seletores.
Usa subprocess para evitar conflito Sync/Async com pytest-playwright.
"""

import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestExtractElements:
    """Testes para extract_elements()"""
    
    def test_extraction_via_subprocess(self, temp_artifacts_dir):
        """Testa extração de elementos via subprocess"""
        html_path = temp_artifacts_dir / "test.html"
        output_path = temp_artifacts_dir / "output.json"
        
        # Cria HTML de teste
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Página de Teste</title></head>
        <body>
            <form id="login-form">
                <input type="text" id="username" name="username" placeholder="Usuário">
                <input type="password" id="password" name="password" placeholder="Senha">
                <button type="submit" id="submit-btn" data-testid="login-button">Entrar</button>
            </form>
        </body>
        </html>
        """
        html_path.write_text(html_content, encoding="utf-8")
        
        code = f"""
import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from project.core.elements import extract_elements

try:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    html_content = Path(r"{html_path}").read_text(encoding="utf-8")
    page.set_content(html_content)
    
    result = extract_elements(page, mask_sensitive=True)
    
    context.close()
    browser.close()
    playwright.stop()
    
    with open(r"{output_path}", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {{e}}")
    sys.exit(1)
"""
        proc_result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert proc_result.returncode == 0, f"Subprocess falhou: {proc_result.stderr}"
        assert "SUCCESS" in proc_result.stdout
        
        # Valida output
        with open(output_path, encoding="utf-8") as f:
            result = json.load(f)
        
        assert "elements" in result
        assert "page_signals" in result
        assert len(result["elements"]) >= 3, "Deve ter pelo menos 3 elementos (2 inputs + 1 button)"
    
    def test_element_has_candidates(self, temp_artifacts_dir):
        """Verifica que elementos têm candidatos de seletores"""
        html_path = temp_artifacts_dir / "test2.html"
        output_path = temp_artifacts_dir / "output2.json"
        
        html_content = """
        <html><body>
            <button id="my-btn" data-testid="test-button">Click Me</button>
        </body></html>
        """
        html_path.write_text(html_content, encoding="utf-8")
        
        code = f"""
import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from project.core.elements import extract_elements

try:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    html_content = Path(r"{html_path}").read_text(encoding="utf-8")
    page.set_content(html_content)
    
    result = extract_elements(page)
    
    browser.close()
    playwright.stop()
    
    with open(r"{output_path}", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {{e}}")
    sys.exit(1)
"""
        proc_result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert proc_result.returncode == 0, f"Subprocess falhou: {proc_result.stderr}"
        
        with open(output_path, encoding="utf-8") as f:
            result = json.load(f)
        
        buttons = [e for e in result["elements"] if e["tag"] == "button"]
        assert len(buttons) >= 1
        
        for btn in buttons:
            assert "candidates" in btn, "Elemento deve ter candidates"
            assert len(btn["candidates"]) > 0, "Deve ter pelo menos 1 candidato"
