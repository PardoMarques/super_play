# 🔮 Funcionalidade Futura: Auto Docs (Relatório PDF)

> **Status:** Planejado

## Conceito

Gerar um **relatório PDF detalhado** de uma sessão de automação, concatenando:
- Screenshots de cada passo executado
- Descrição das ações (click, fill, navigate)
- Timestamps e seletores utilizados

## Uso Esperado

### 1. Coleta com flag `--autodoc`

```powershell
python gen_food.py --url https://app.exemplo.com --mode interact --autodoc
```

Quando `--autodoc` está ativo:
- Cada ação (click, fill, etc.) gera um screenshot em `steps_screenshots/`
- Formato: `001_click_btn-login.png`, `002_fill_username.png`, etc.

### 2. Geração do PDF

```powershell
python gen_autodoc.py --run artifacts/runs/20260117_XXXX --output evidencia_sessao.pdf
```

## Estrutura de Artefatos (com --autodoc)

```
artifacts/runs/20260117_XXXX/
├── food/
│   ├── food.json
│   └── actions.ndjson
├── screenshots/              # Captura por NAVEGAÇÃO (sempre existe)
├── steps_screenshots/        # Captura por AÇÃO (só com --autodoc)
│   ├── 001_click_btn-login.png
│   ├── 002_fill_username.png
│   ├── 003_fill_password.png
│   └── 004_click_submit.png
├── html/
├── logs/
└── meta.json
```

> **⚠️ Importante:** As pastas `screenshots/` e `steps_screenshots/` são **independentes**:
> - `screenshots/` → Captura automática a cada **navegação** (mudança de URL). Sempre ativa.
> - `steps_screenshots/` → Captura a cada **ação** (click, fill). Só existe se `--autodoc` for usado.

**Se `--autodoc` NÃO for usado:** a pasta `steps_screenshots/` não existe, mas `screenshots/` continua funcionando normalmente.

## Saída: PDF

O PDF gerado conterá:

1. **Capa:** URL, data/hora, run_id
2. **Para cada ação:**
   - Screenshot do momento
   - Tipo de ação (click, fill, navigate)
   - Seletor usado
   - Valor (se aplicável, mascarado para passwords)
   - Timestamp
3. **Resumo final:** Total de ações, páginas visitadas, duração

## Implementação no BasePage

O `base_page.py` precisará de um toggle interno:

```python
class BasePage:
    def __init__(self, page, autodoc: bool = False, steps_dir: Path = None):
        self.autodoc = autodoc
        self.steps_dir = steps_dir
        self.step_counter = 0
    
    def _capture_step(self, action: str, target: str):
        """Captura screenshot do passo se autodoc estiver ativo."""
        if not self.autodoc:
            return
        
        self.step_counter += 1
        filename = f"{self.step_counter:03d}_{action}_{self._safe_name(target)}.png"
        self.page.screenshot(path=self.steps_dir / filename)
    
    def click(self, selector: str):
        super().click(selector)
        self._capture_step("click", selector)
    
    def fill(self, selector: str, value: str):
        super().fill(selector, value)
        self._capture_step("fill", selector)
```

## Vantagens

- **Evidência completa:** Cada passo tem prova visual
- **Auditoria:** PDF serve como documento oficial de execução
- **Reprodutibilidade:** Sabemos exatamente o que aconteceu
- **Opcional:** Não impacta performance quando desativado

---

*Esta funcionalidade ainda não está implementada.*
