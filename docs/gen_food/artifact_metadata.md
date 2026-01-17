# 📄 Artifact: Meta (`meta.json`)

Arquivo raiz que descreve **COMO** a coleta foi realizada e o resultado geral de alto nível.

## Importância

### 1. Reprodutibilidade
Informa exatamente quais parâmetros foram usados (`headless`, `mask_sensitive`), permitindo reproduzir a execução nas mesmas condições.

### 2. Resumo Executivo
Fornece métricas rápidas sem precisar ler os arquivos pesados:
- Sucesso ou Falha?
- Total de elementos coletados.
- Total de páginas visitadas.
- Total de ações gravadas.

### 3. Rastreabilidade
O `run_id` conecta este metadado a todos os outros artefatos da pasta `artifacts/runs/<run_id>/`.

**Exemplo:**
```json
{
  "run_id": "20260117_XXXX",
  "started_at": "...",
  "url": "https://deepai.org",
  "mode": "interact",
  "result": {
    "success": true,
    "elements_count": 150,
    "pages_count": 3
  }
}
```
