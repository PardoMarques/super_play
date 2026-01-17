# 🔮 Funcionalidade Futura: Request Crawler

> **Status:** Planejado

## Conceito

Interceptar e registrar **todas as requisições HTTP** feitas pelo browser durante uma sessão `gen_food --mode interact`.

## Por que isso importa?

| Cenário | Benefício |
|---------|-----------|
| Site carrega dados via API | Captura endpoints ocultos (mais rápidos que scraping HTML) |
| Autenticação complexa | Entende fluxo de tokens, cookies, headers |
| Debug de falhas | Vê exatamente o que o browser requisitou |
| Documentação de APIs internas | Gera especificação a partir do tráfego real |

## Saída Esperada

Novo arquivo no artefato: `food/requests.ndjson`

```json
{"ts": "...", "method": "GET", "url": "https://api.exemplo.com/users", "status": 200, "type": "xhr"}
{"ts": "...", "method": "POST", "url": "https://api.exemplo.com/auth", "status": 200, "type": "fetch"}
```

## Implementação Técnica

Playwright permite interceptar via `page.on("request")` e `page.on("response")`:

```python
def on_request(request):
    log_request({
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "post_data": request.post_data,
    })

def on_response(response):
    log_response({
        "url": response.url,
        "status": response.status,
        "headers": dict(response.headers),
    })

page.on("request", on_request)
page.on("response", on_response)
```

## Filtros Planejados

| Flag | Descrição |
|------|-----------|
| `--capture-requests` | Habilita captura (default: off) |
| `--filter-type` | Filtra por tipo (xhr, fetch, document, etc) |
| `--filter-domain` | Captura apenas domínios específicos |
| `--include-body` | Inclui corpo da resposta (cuidado com tamanho) |

## Uso com Scrapy

Os endpoints descobertos podem alimentar spiders:

```
gen_food (descobre API) → requests.ndjson → Scrapy Spider (extrai dados em escala)
```

---

*Esta funcionalidade ainda não está implementada.*
