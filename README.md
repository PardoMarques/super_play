# Super Play

> **Autoria:** Caio Marques ([@pardomarques](https://github.com/pardomarques)) & **CyFive**  
> **Status:** Ativo / Desenvolvimento  
> **Licença:** [Certificado Anti-Cópia (Restrito)](LICENSE) 🛑

Automation framework robusto com Playwright, pytest-bdd e Scrapy, focado em resiliência e coleta inteligente de dados.

---

## 🚀 Funcionalidades

### Gen Food (`gen_food.py`)
Coletor de dados inteligente para QA e Automação e geração de Page Objects.

- **Modo Snapshot:** Captura HTML, screenshot e inventário de elementos de uma única página.
- **Modo Interact:** Navegador visível para interação humana, gravando ações (clicks, inputs, navegações) em tempo real.
- **Page Objects Inteligentes:** Gera seletores robustos (data-testid, aria-label, etc) e mascaramento automático de dados sensíveis (passwords).
- **Session Replay:** Histórico completo de navegação com screenshots e HTML de cada página visitada.

### Browser Core
- **Persistent Context:** Mantém sessões (cookies/localStorage) entre execuções.
- **Resiliência:** Utilitários de retry avançados para redes e elementos instáveis.

---

## 🛠️ Setup

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers do Playwright
playwright install
```

---

## 💻 Como Usar

### 1. Snapshot Rápido
Coleta dados de uma única URL e fecha.

```powershell
python gen_food.py --url https://deepai.org
```

### 2. Modo Interativo (Interact)
Abre o navegador para você navegar. O sistema grava cliques, textos digitados e tira prints de cada tela acessada. Use **Ctrl+C** para finalizar.

```powershell
python gen_food.py --url https://deepai.org --mode interact
```

### 3. Manter Sessão (Login)
Para não precisar logar toda vez, use `--profile-dir`:

```powershell
python gen_food.py --url https://painel.exemplo.com --profile-dir ./perfis/admin
```

---

## 📂 Estrutura de Artefatos

Cada execução gera uma pasta única em `artifacts/runs/<id>/`:

```
artifacts/runs/20260117_XXXX/
├── meta.json             # Metadados da execução e páginas visitadas
├── logs/
│   └── session.log       # Log técnico completo
├── food/
│   ├── food.json         # Elementos extraídos e mapa da sessão
│   └── actions.ndjson    # Log de ações (clicks, inputs)
├── html/
│   ├── page_1.html       # HTML da primeira página
│   └── page_2.html       # HTML da segunda...
└── screenshots/
    ├── <ts>_page_1.png   # Screenshot página 1
    └── <ts>_page_2.png   # Screenshot página 2
```

---

## 🤝 Contribuições

Contribuições são **muito bem-vindas**! O espírito deste projeto é colaborativo.
Sinta-se à vontade para abrir **Issues** relatando problemas ou **Pull Requests (PRs)** com melhorias, refatorações ou novas features.

1. Fork o projeto
2. Crie sua Feature Branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## © Direitos Autorais e Licença

Este projeto é desenvolvido por **Caio Marques (CyFive)**.

- ✅ **Estudo:** Você pode clonar, estudar e usar como referência.
- ✅ **Contribuição:** PRs são aceitos e encorajados!
- 🚫 **Comercial:** Venda ou redistribuição como produto próprio requer autorização.

Consulte o arquivo [LICENSE](LICENSE) para detalhes completos.

**CyFive © 2026**
