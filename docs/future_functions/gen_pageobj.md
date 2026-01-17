# 🔮 Funcionalidade Futura: `gen_pageobj`

> **Status:** Planejado

## Conceito

Comando CLI que transforma artefatos do `gen_food` em Page Objects prontos para uso.

## Uso Esperado

```powershell
python gen_pageobj.py --artifact artifacts/runs/20260117_XXXX
```

**Saída:** Arquivo Python com classe Page Object gerada.

## Entrada

Lê o `food.json` do artefato especificado:
- `elements[]` → Propriedades da classe
- `candidates[]` → Seletores (usa o mais robusto como padrão)
- `page_signals.title` → Nome da classe

## Saída Esperada

```python
# Gerado automaticamente por gen_pageobj
# Artifact: 20260117_XXXX
# URL: https://exemplo.com/login

from project.pages.base_page import BasePage

class LoginPage(BasePage):
    """Page Object para tela de login."""
    
    # Seletores
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    SUBMIT_BTN = "[data-testid='login-button']"
    
    def fill_username(self, value: str):
        self.fill(self.USERNAME_INPUT, value)
    
    def fill_password(self, value: str):
        self.fill(self.PASSWORD_INPUT, value)
    
    def click_submit(self):
        self.click(self.SUBMIT_BTN)
```

## Lógica de Seleção de Seletor

Prioridade dos candidatos (do mais robusto ao menos):
1. `data-testid`
2. `id`
3. `aria-label`
4. `name`
5. `css-path`

## Opções Planejadas

| Flag | Descrição |
|------|-----------|
| `--artifact` | Caminho do diretório de artefatos |
| `--output` | Caminho do arquivo de saída (default: `pages/<PageName>.py`) |
| `--class-name` | Nome da classe (default: baseado no título da página) |

---

*Esta funcionalidade ainda não está implementada.*
