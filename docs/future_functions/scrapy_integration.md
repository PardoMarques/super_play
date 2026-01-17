# 🔮 Funcionalidade Futura: Scrapy Integration

> **Status:** Planejado

## Conceito

Integrar Scrapy ao projeto para habilitar **web scraping em escala** e **pipelines de dados** (ETL/ELT).

## Por que Scrapy?

| Problema | Solução Scrapy |
|----------|----------------|
| Playwright é lento para muitas páginas | Scrapy usa requests HTTP diretas (10x+ mais rápido) |
| Dados precisam ir para banco/API | Pipelines nativos para transformação e exportação |
| Sites bloqueiam por rate-limit | Middlewares de delay, rotação de User-Agent, proxies |

## Arquitetura Planejada

```
project/
├── scrapy/
│   ├── spiders/          # Spiders por domínio/funcionalidade
│   │   └── exemplo_spider.py
│   ├── pipelines/        # Transformação e destino dos dados
│   │   ├── clean_pipeline.py      # Limpeza/normalização
│   │   ├── database_pipeline.py   # Salva em banco
│   │   └── api_pipeline.py        # Envia para API
│   ├── middlewares/      # Interceptadores de request/response
│   └── settings.py       # Configuração global
```

## Pipeline ETL vs ELT

### ETL (Extract → Transform → Load)
```
Scrapy Spider → Clean Pipeline → Database Pipeline
```
- Transforma os dados **antes** de salvar
- Bom para bancos relacionais com schema rígido

### ELT (Extract → Load → Transform)
```
Scrapy Spider → Raw Storage → DBT/SQL Transforms
```
- Salva dados brutos, transforma depois
- Bom para Data Lakes e análises flexíveis

## Integração com Gen Food

O `gen_food` identifica os elementos. O Scrapy usa esses seletores para extrair dados em escala:

```python
# Spider usando seletores do food.json
class ExemploSpider(scrapy.Spider):
    def parse(self, response):
        # Seletores vieram do food.json
        yield {
            "titulo": response.css("#titulo::text").get(),
            "preco": response.css("[data-testid='preco']::text").get(),
        }
```

## Próximos Passos

1. Adicionar `scrapy` ao `requirements.txt`
2. Criar estrutura de pastas `project/scrapy/`
3. Implementar spider de exemplo
4. Documentar pipelines disponíveis

---

*Esta funcionalidade ainda não está implementada.*
