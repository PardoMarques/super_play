# 🔮 Funcionalidade Futura: `--prefixo`

> **Status:** Planejado (não implementado)

## Conceito

O parâmetro `--prefixo` permitirá executar uma **sequência de automações pré-definidas** antes de iniciar a coleta/interação principal.

## Motivação

Em sistemas que requerem autenticação ou passos iniciais complexos (logins com 2FA, navegação em menus, aceite de termos), o usuário precisa repetir esses passos manualmente a cada execução.

Com o `--prefixo`, será possível:

1. Definir um script Python de "setup" que executa antes do modo principal.
2. O script coloca a aplicação em um estado específico (ex: logado, em determinada página).
3. O modo principal (snapshot/interact) assume a partir dali.

## Exemplo de Uso Futuro

```powershell
# Roda o prefixo "login_admin" antes de iniciar interact
python gen_food.py --url https://app.exemplo.com --prefixo login_admin --mode interact
```

Onde `login_admin` seria um arquivo Python em `prefixos/login_admin.py`:

```python
# prefixos/login_admin.py
"""Prefixo para autenticação como admin."""

import os

def run(page):
    """
    Executa o fluxo de login no sistema.
    
    Args:
        page: Instância da página Playwright.
    """
    # Preenche credenciais
    page.fill("#email", "admin@empresa.com")
    page.fill("#password", os.environ.get("ADMIN_PASSWORD", ""))
    
    # Submete formulário
    page.click("#submit-login")
    
    # Aguarda dashboard carregar
    page.wait_for_selector("#dashboard", timeout=10000)
```

## Vantagens

- **Flexibilidade Total:** Python permite lógica condicional, loops, tratamento de erros.
- **Reutilização:** Crie uma vez, use em múltiplas execuções.
- **Segurança:** Credenciais vêm de variáveis de ambiente (`os.environ`).
- **Desacoplamento:** O pré-requisito (login) fica separado do teste/coleta.
- **Debugável:** É código Python comum, fácil de testar e depurar isoladamente.

---

*Esta funcionalidade ainda não está implementada. Contribuições são bem-vindas!*
