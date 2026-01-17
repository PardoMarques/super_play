# 📁 Artifact: Food (`food/`)

Este diretório contém os dados estruturados mais importantes ("o alimento") para o processo de automação.

## Arquivos Gerados

### 1. `food.json`
É o inventário completo da sessão de coleta.

**Importância:**
- **Mapa da Sessão:** Contém a lista `pages_visited` mapeando cada URL acessada a um `pageId` único.
- **Análise de Seletores:** Para cada elemento interativo encontrado, lista múltiplos candidatos de seletores (ID, data-testid, texto, CSS path, etc.), ordenados por robustez.
- **Mascaramento:** Dados sensíveis são identificados e mascarados na fonte.

**Estrutura principal:**
```json
{
  "pages_visited": [
    {"pageId": 1, "url": "...", "title": "..."}
  ],
  "elements": [
    {
      "tag": "button",
      "textPreview": "Enviar",
      "candidates": [
        {"strategy": "id", "selector": "#submit-btn"},
        {"strategy": "css-path", "selector": "form > button"}
      ]
    }
  ],
  "action_summary": {...}
}
```

---

### 2. `actions.ndjson`
(Apenas modo `interact`)
Log de eventos em tempo real, gravando cada interação do usuário no formato NDJSON (Newline Delimited JSON).

**Importância:**
- **Rastrabilidade:** Sabemos exatamente onde o usuário clicou, o que digitou e em qual ordem.
- **Base para Replay:** Serve como roteiro para futuramente gerar testes automatizados que replicam o comportamento humano.
- **Debug:** Se algo quebrou, sabemos qual foi a última ação realizada.

**Exemplo de linha:**
```json
{"ts": "...", "type": "click", "element": {"tag": "button", "text": "OK"}, "url": "..."}
```
