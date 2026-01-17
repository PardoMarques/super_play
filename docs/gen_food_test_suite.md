# 🧪 Gen Food - Suíte de Testes

Este projeto tem **15 testes automatizados** que validam as funcionalidades principais.

```powershell
pytest tests/
```

---

## Evidências

Após cada execução, as evidências são salvas em:

```
tests/evidence/run_<timestamp>/
├── test_creates_all_directories/
├── test_extraction_via_subprocess/
├── test_snapshot_creates_food_json/
│   └── runs/<run_id>/
│       ├── food/food.json
│       ├── html/page.html
│       ├── screenshots/page.png
│       └── logs/session.log
└── ...
```

Cada `pytest tests/` gera **1 pasta** (`run_<timestamp>`), com subpastas por teste.

---

## O que cada teste prova

### `test_artifacts.py`

| Teste | Valida |
|-------|--------|
| `test_run_id_format` | ID de execução segue padrão `YYYYMMDD_HHMMSS_XXXX` |
| `test_run_id_unique` | 10 IDs gerados consecutivamente são todos diferentes |
| `test_creates_all_directories` | Pastas `html/`, `screenshots/`, `food/`, `logs/` são criadas |
| `test_directories_structure` | Caminhos retornados são válidos e acessíveis |

**Se falhar:** Estrutura de artefatos quebrada.

---

### `test_browser.py`

| Teste | Valida |
|-------|--------|
| `test_browser_module_imports` | Playwright está instalado e configurado |
| `test_create_browser_and_close_via_subprocess` | Browser abre, navega e fecha sem vazamento |

**Se falhar:** Motor de automação não funciona.

---

### `test_elements.py`

| Teste | Valida |
|-------|--------|
| `test_extraction_via_subprocess` | Extrai elementos de HTML real (mínimo 3) |
| `test_element_has_candidates` | Cada elemento retorna candidatos de seletores |

**Se falhar:** Gen Food não está gerando dados úteis.

---

### `test_gen_food_integration.py`

| Teste | Valida |
|-------|--------|
| `test_snapshot_exits_successfully` | `gen_food.py` roda sem erro (exit code 0) |
| `test_snapshot_creates_run_directory` | Diretório de execução é criado |
| `test_snapshot_creates_food_json` | `food.json` existe e tem estrutura válida |
| `test_snapshot_creates_meta_json` | `meta.json` existe com metadados corretos |
| `test_snapshot_creates_html_file` | HTML foi salvo |
| `test_snapshot_creates_screenshot` | Screenshot PNG foi gerado |
| `test_snapshot_creates_session_log` | Log de sessão existe e tem conteúdo |

**Se falhar:** Fluxo principal do projeto quebrado.

---

## Resumo

Se os 15 testes passam:
- ✅ Estrutura de diretórios funciona
- ✅ Browser abre e fecha corretamente
- ✅ Extração de elementos gera seletores
- ✅ Todos os artefatos são gerados

Se algum falhar, o projeto não está pronto para uso.
