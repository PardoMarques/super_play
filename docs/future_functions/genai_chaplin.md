# 🎬 GenAI Chaplin — Engine de Otimização

> **Status:** Planejado (Longo Prazo)

## Visão Geral

**GenAI Chaplin** é uma **engine de background** que otimiza automaticamente os geradores de projetos de QA/RPA/Webscraping.

**Não é um chatbot.** É um módulo silencioso que:

1. **Analisa os insumos** coletados pelo `gen_food`
2. **Consulta uma base de conhecimento (RAG)** sobre usabilidade, RPA e scraping
3. **Injeta feedbacks e otimizações** diretamente nos artefatos gerados

O nome "Chaplin" é uma homenagem ao ator Charlie Chaplin que protagonizou o filme "Modern Times" que retrata a vida de um trabalhador em uma fábrica de canivetes. Isso marcou muito minha infância e é minha referência sobre processos de automação...

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      GenAI Chaplin                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│   │ actions.    │    │ food.json   │    │ screenshots │     │
│   │ ndjson      │    │             │    │             │     │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│          │                  │                  │            │
│          └──────────────────┼──────────────────┘            │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │  Contexto da    │                      │
│                    │   Execução      │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│           ┌─────────────────┼─────────────────┐             │
│           ▼                 ▼                 ▼             │
│    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│    │ RAG:        │   │ RAG:        │   │ RAG:        │      │
│    │ Usabilidade │   │ RPA Patterns│   │ Scraping    │      │
│    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘      │
│           │                 │                 │             │
│           └─────────────────┼─────────────────┘             │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │      LLM        │                      │
│                    │ (Ollama/Gemini) │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│           ┌─────────────────┼─────────────────┐             │
│           ▼                 ▼                 ▼             │
│    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      |
│    │ Métodos     │   │ Dicas de    │   │ Alertas de  │      |
│    │ Semânticos  │   │ Otimização  │   │ Problemas   │      |
│    └─────────────┘   └─────────────┘   └─────────────┘      |
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Base de Conhecimento (RAG)

O Chaplin consulta três domínios de conhecimento:

### 1. Usabilidade Web

Documentos indexados:
- **Heurísticas de Nielsen** (10 princípios fundamentais)
- **WCAG 2.1** (acessibilidade)
- **Material Design Guidelines**
- **Apple Human Interface Guidelines**
- **Padrões de formulários** (validação, feedback, progressão)
- **Padrões de navegação** (breadcrumbs, menus, paginação)

**Exemplo de consulta:**
> "O usuário preencheu 15 campos em sequência sem feedback. Isso viola a heurística de 'Visibilidade do status do sistema'?"

### 2. RPA (Robotic Process Automation)

Documentos indexados:
- **UiPath Best Practices**
- **Automation Anywhere Patterns**
- **Blue Prism Design Patterns**
- **Selector Stability Guidelines**
- **Exception Handling Patterns**
- **Credential Management**

**Exemplo de consulta:**
> "Este fluxo tem 3 pontos onde pode falhar por timeout. Qual padrão de retry é recomendado?"

### 3. Web Scraping

Documentos indexados:
- **Scrapy Documentation**
- **Playwright Anti-Detection**
- **Rate Limiting Strategies**
- **robots.txt Compliance**
- **Data Extraction Patterns**
- **Pagination Handling**

**Exemplo de consulta:**
> "O site carrega dados via infinite scroll. Como estruturar o spider para capturar tudo?"

---

## Funcionalidades Detalhadas

### 1. Identificação de Padrões Comportamentais

O Chaplin lê o `actions.ndjson` e agrupa ações relacionadas:

**Entrada (ações brutas):**
```json
{"type": "click", "selector": "#email"}
{"type": "fill", "selector": "#email", "value": "user@ex.com"}
{"type": "click", "selector": "#password"}
{"type": "fill", "selector": "#password", "value": "***"}
{"type": "click", "selector": "#btn-login"}
```

**Saída (padrão identificado):**
```python
def autenticacao_login(self, email: str, senha: str):
    """
    Padrão: Fluxo de Login
    Confiança: 95%
    Ações: 5
    """
    self.fill("#email", email)
    self.fill("#password", senha)
    self.click("#btn-login")
```

### 2. Dicas Contextuais

Baseado na análise, o Chaplin gera recomendações:

```markdown
## 💡 Dicas do Chaplin

### Usabilidade
- ⚠️ O formulário de cadastro tem 12 campos sem agrupamento visual.
  **Sugestão:** Divida em etapas ou agrupe por categoria (dados pessoais, endereço, etc.)

### RPA
- ⚠️ O seletor `#btn-submit` é genérico e pode existir em múltiplas páginas.
  **Sugestão:** Prefira `[data-testid="login-submit"]` ou combine com contexto pai.

### Scraping
- ⚠️ A página usa lazy loading para produtos.
  **Sugestão:** Implemente scroll automático ou intercepte a API de paginação.
```

### 3. Análise de Riscos

O Chaplin identifica pontos frágeis na automação:

| Risco | Descrição | Mitigação |
|-------|-----------|-----------|
| 🔴 Alto | Seletor `div > div > span` é muito frágil | Use ID ou data-testid |
| 🟡 Médio | Tempo entre ações < 100ms pode parecer bot | Adicione delays humanizados |
| 🟢 Baixo | Login pode expirar após 30min | Implemente refresh de sessão |

### 4. Geração de Artefatos

```powershell
python gen_chaplin.py --run artifacts/runs/20260117_XXXX
```

**Saída:**
```
outputs/chaplin_analysis/
├── suggested_methods.py      # Código Python com métodos agrupados
├── tips_report.md            # Relatório de dicas e alertas
├── risk_assessment.json      # Análise de riscos estruturada
└── rag_references.md         # Fontes consultadas na base de conhecimento
```

---

## Integração com Outras Features

| Feature | Como Integra |
|---------|--------------|
| `gen_pageobj` | Usa métodos do Chaplin ao invés de ações brutas |
| `auto_docs` | Inclui dicas e riscos no PDF de evidência |
| `prefixo` | Fluxos identificados viram scripts `.py` prontos |
| `visual_regression` | Combina análise visual com dicas de usabilidade |

---

## Configuração do RAG

```yaml
# config/chaplin_rag.yaml
knowledge_bases:
  usability:
    source: ./knowledge/usability/*.md
    embeddings: sentence-transformers/all-MiniLM-L6-v2
  
  rpa:
    source: ./knowledge/rpa/*.md
    embeddings: sentence-transformers/all-MiniLM-L6-v2
  
  scraping:
    source: ./knowledge/scraping/*.md
    embeddings: sentence-transformers/all-MiniLM-L6-v2

llm:
  provider: gemini  # ou claude, openai, ollama
  model: gemini-pro
  temperature: 0.3
```

---

## Exemplo de Fluxo Completo

```
1. Usuário roda: python gen_food.py --url https://loja.com --mode interact
2. Interage: navega, adiciona produto, preenche checkout
3. Roda: python gen_chaplin.py --run artifacts/runs/20260117_XXXX

Saída:
- Métodos identificados: adicionar_produto(), preencher_endereco(), finalizar_compra()
- Dicas: "O campo CEP não valida formato. Considere máscara."
- Riscos: "Botão de pagamento muda de ID conforme método selecionado."
```

---

## Modo de Operação

O Chaplin **não é interativo**. Ele roda em background durante a geração de artefatos:

```python
# Dentro do gen_pageobj.py
from chaplin import ChaplinEngine

chaplin = ChaplinEngine(rag_config="config/chaplin_rag.yaml")

# Ao gerar Page Object, o Chaplin otimiza automaticamente
page_obj = chaplin.optimize(
    raw_actions=load("actions.ndjson"),
    elements=load("food.json"),
)
# page_obj já vem com métodos semânticos, dicas em docstrings, etc.
```

**Integração transparente:** Quem usa `gen_pageobj`, `auto_docs` ou `prefixo` recebe otimizações do Chaplin sem precisar chamá-lo explicitamente.

---

*O Chaplin trabalha nos bastidores. Você recebe o resultado polido.*

