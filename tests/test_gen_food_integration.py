"""
Integration tests for gen_food.py

Validates complete collection flow in snapshot mode.
"""

import pytest
import json
import subprocess
import sys
from pathlib import Path


class TestGenFoodSnapshot:
    """PT: Testes de integração para modo snapshot"""
    """EN: Integration tests for snapshot mode"""
    
    @pytest.fixture
    def run_snapshot(self, temp_artifacts_dir):
        """PT: Executa gen_food no modo snapshot e retorna o resultado"""
        """EN: Executes gen_food in snapshot mode and returns result"""
        # Uses a simple and reliable page for testing
        test_url = "data:text/html,<html><head><title>Test</title></head><body><button id='btn'>Click</button></body></html>"
        
        result = subprocess.run(
            [
                sys.executable,
                "gen_food.py",
                "--url", test_url,
                "--mode", "snapshot",
                "--headless",
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            env={
                **dict(__import__("os").environ),
                "ARTIFACTS_DIR": str(temp_artifacts_dir),
            },
            timeout=60,
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "artifacts_dir": temp_artifacts_dir,
        }
    
    def test_snapshot_exits_successfully(self, run_snapshot):
        """PT: gen_food --mode snapshot deve retornar código 0"""
        """EN: gen_food --mode snapshot must return code 0"""
        assert run_snapshot["returncode"] == 0, \
            f"Error: {run_snapshot['stderr']}"
    
    def test_snapshot_creates_run_directory(self, run_snapshot):
        """PT: Deve criar diretório run em artifacts/runs/"""
        """EN: Must create run directory in artifacts/runs/"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        
        assert runs_dir.exists(), "Directory runs/ must exist"
        
        run_dirs = list(runs_dir.iterdir())
        assert len(run_dirs) >= 1, "Must have at least 1 run directory"
    
    def test_snapshot_creates_food_json(self, run_snapshot):
        """PT: Deve criar arquivo food.json com estrutura válida"""
        """EN: Must create food.json with valid structure"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        run_dir = list(runs_dir.iterdir())[0]
        food_path = run_dir / "food" / "food.json"
        
        assert food_path.exists(), "food.json must exist"
        
        with open(food_path, encoding="utf-8") as f:
            food = json.load(f)
        
        assert "schema_version" in food
        assert "url" in food
        assert "elements" in food
        assert "page_signals" in food
    
    def test_snapshot_creates_meta_json(self, run_snapshot):
        """PT: Deve criar arquivo meta.json com metadados"""
        """EN: Must create meta.json with metadata"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        run_dir = list(runs_dir.iterdir())[0]
        meta_path = run_dir / "meta.json"
        
        assert meta_path.exists(), "meta.json must exist"
        
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        
        assert "run_id" in meta
        assert "started_at" in meta
        assert "mode" in meta
        assert meta["mode"] == "snapshot"
    
    def test_snapshot_creates_html_file(self, run_snapshot):
        """PT: Deve criar arquivo HTML"""
        """EN: Must create HTML file"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        run_dir = list(runs_dir.iterdir())[0]
        html_dir = run_dir / "html"
        
        assert html_dir.exists(), "Directory html/ must exist"
        
        html_files = list(html_dir.glob("*.html"))
        assert len(html_files) >= 1, "Must have at least 1 HTML file"
    
    def test_snapshot_creates_screenshot(self, run_snapshot):
        """PT: Deve criar screenshot PNG"""
        """EN: Must create PNG screenshot"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        run_dir = list(runs_dir.iterdir())[0]
        screenshots_dir = run_dir / "screenshots"
        
        assert screenshots_dir.exists(), "Directory screenshots/ must exist"
        
        png_files = list(screenshots_dir.glob("*.png"))
        assert len(png_files) >= 1, "Must have at least 1 screenshot"
    
    def test_snapshot_creates_session_log(self, run_snapshot):
        """PT: Deve criar log de sessão"""
        """EN: Must create session log"""
        runs_dir = run_snapshot["artifacts_dir"] / "runs"
        run_dir = list(runs_dir.iterdir())[0]
        log_path = run_dir / "logs" / "session.log"
        
        assert log_path.exists(), "session.log must exist"
        assert log_path.stat().st_size > 0, "Log must not be empty"
