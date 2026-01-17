# 📁 Artifact: Screenshots (`screenshots/`)

Este diretório contém evidências visuais capturadas durante a navegação.

## Arquivos Gerados

Formato: `<timestamp>_page_<pageId>.png`

Exemplo: `20260117_123045_page_1.png`

## Importância

### 1. Validação Visual
Confirmação instantânea de como a página estava renderizada. Essencial para verificar layouts quebrados, modais sobrepostos ou estados de erro.

### 2. Rastreamento de Estado
Ao contrário do HTML, capturamos um **novo screenshot** a cada navegação ou mudança relevante, mesmo se voltarmos para a mesma página. Isso cria uma linha do tempo visual da interação.

### 3. Auditoria
Em processos sensíveis, o screenshot serve como prova de que uma ação foi realizada ou uma mensagem foi exibida.

## Frequência de Captura
O `gen_food` captura screenshots:
- Automaticamente ao carregar uma nova página.
- Periodicamente a cada 5 segundos durante interações (modo interact).
- Imediatamente antes de fechar a sessão.
