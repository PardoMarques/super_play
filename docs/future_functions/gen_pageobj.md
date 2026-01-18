# 🔮 Funcionalidade: `gen_pageobj` — Gerador de Projetos de Automação

> **Status:** Implementação Planejada

## Conceito

Comando CLI que transforma artefatos do `gen_food` em um **projeto de automação completo e funcional**.

**Não gera apenas Page Objects.** Gera um **projeto inteiro** pronto para rodar.

## Uso

```powershell
python gen_pageobj.py --artifact artifacts/runs/20260117_XXXX --name meusite
```

**Saída:** Pasta `meusite_automation/` com estrutura completa.

## Estrutura Gerada

```
meusite_automation/
├── .env                      # Variáveis de ambiente (BASE_URL, credenciais)
├── .gitignore                # Ignora venv, cache, screenshots
├── requirements.txt          # Dependências (playwright, pytest-bdd, etc)
├── conftest.py               # Fixtures do pytest (browser, pages)
├── pytest.ini                # Configuração do pytest
│
├── pages/                    # Page Objects gerados
│   ├── __init__.py
│   ├── base_page.py          # Classe base com retry, screenshots
│   └── home_page.py          # Page Object da página coletada
│
├── steps/                    # Step definitions para BDD
│   ├── __init__.py
│   └── home_steps.py         # Steps gerados a partir das ações
│
├── features/                 # Arquivos .feature (Gherkin)
│   └── home.feature          # Cenários gerados das ações gravadas
│
├── utils/                    # Utilitários
│   ├── __init__.py
│   ├── config.py             # Carregador de configuração
│   └── helpers.py            # Funções auxiliares
│
└── tests/                    # Testes de smoke/sanity
    ├── __init__.py
    └── test_smoke.py         # Teste básico de navegação
```

## Entrada

Lê os artefatos do `gen_food`:

| Arquivo | Uso |
|---------|-----|
| `food.json` | Gera seletores, propriedades, métodos do Page Object |
| `actions.ndjson` | Gera steps BDD e cenários .feature |
| `meta.json` | Extrai URL base para .env |
| `html/*.html` | Referência para nomes de páginas (título) |

## Lógica de Geração

### 1. Page Objects

Para cada página visitada (`pageId`), gera um arquivo `pages/<nome>_page.py`:

```python
# Gerado automaticamente por gen_pageobj
# Fonte: artifacts/runs/20260117_XXXX
# Página: Login (page_1)

from pages.base_page import BasePage

class LoginPage(BasePage):
    """Page Object para tela de Login."""
    
    # Seletores (ordenados por robustez)
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    SUBMIT_BTN = "[data-testid='login-button']"
    
    def preencher_usuario(self, valor: str):
        """Preenche campo de usuário."""
        self.fill(self.USERNAME_INPUT, valor)
    
    def preencher_senha(self, valor: str):
        """Preenche campo de senha."""
        self.fill(self.PASSWORD_INPUT, valor)
    
    def clicar_entrar(self):
        """Clica no botão de login."""
        self.click(self.SUBMIT_BTN)
    
    def fazer_login(self, usuario: str, senha: str):
        """Fluxo completo de login."""
        self.preencher_usuario(usuario)
        self.preencher_senha(senha)
        self.clicar_entrar()
```

### 2. Steps BDD

Gera step definitions a partir das ações gravadas:

```python
# steps/login_steps.py

from behave import given, when, then
from pages.login_page import LoginPage

@when('preencho o usuário com "{valor}"')
def step_preencher_usuario(context, valor):
    context.login_page.preencher_usuario(valor)

@when('preencho a senha com "{valor}"')
def step_preencher_senha(context, valor):
    context.login_page.preencher_senha(valor)

@when('clico em Entrar')
def step_clicar_entrar(context):
    context.login_page.clicar_entrar()
```

### 3. Features Gherkin

Gera cenários a partir do fluxo gravado:

```gherkin
# features/login.feature

Funcionalidade: Login no Sistema

  Cenário: Login com credenciais válidas
    Dado que estou na página de login
    Quando preencho o usuário com "admin@exemplo.com"
    E preencho a senha com "***"
    E clico em Entrar
    Então devo ver a página Dashboard
```

### 4. Arquivos de Suporte

| Arquivo | Conteúdo |
|---------|----------|
| `.env` | `BASE_URL=https://site.com` (extraído do meta.json) |
| `requirements.txt` | playwright, pytest, pytest-bdd, python-dotenv |
| `conftest.py` | Fixtures para browser, pages, contexto BDD |
| `pytest.ini` | Configuração de markers, paths |
| `base_page.py` | Cópia do `project/pages/base_page.py` do super_play |

## Opções CLI

| Flag | Descrição |
|------|-----------|
| `--artifact` | Caminho do diretório de artefatos (obrigatório) |
| `--name` | Nome do projeto (default: baseado no domínio da URL) |
| `--output` | Diretório de saída (default: `./<name>_automation/`) |
| `--no-bdd` | Não gera features/steps (apenas Page Objects) |
| `--chaplin` | Ativa otimizações do GenAI Chaplin (se disponível) |

## Fluxo de Execução

```
1. Carrega meta.json → extrai URL, modo, run_id
2. Carrega food.json → extrai elementos por pageId
3. Carrega actions.ndjson → extrai sequência de ações
4. Para cada pageId:
   a. Gera page_<nome>.py com seletores e métodos
   b. Gera <nome>_steps.py com step definitions
   c. Gera <nome>.feature com cenários
5. Gera arquivos de suporte (.env, requirements, etc)
6. Exibe resumo de arquivos criados
```

## Validação Pós-Geração

```powershell
cd meusite_automation
pip install -r requirements.txt
playwright install chromium
pytest tests/test_smoke.py -v
```

Se o smoke test passar, o projeto está funcional.

---

*De coleta para projeto funcional em um comando.*
