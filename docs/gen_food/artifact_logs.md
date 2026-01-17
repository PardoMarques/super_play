# 📁 Artifact: Logs (`logs/`)

Este diretório contém os registros técnicos da execução.

## Arquivos Gerados

- `session.log`

## Importância

### 1. Diagnóstico de Erros
Se o `gen_food` falhar ou fechar inesperadamente, o log detalha exatamente qual linha de código, exceção ou timeout ocorreu.

### 2. Auditoria de Execução
Registra:
- Horário de início e fim.
- Parâmetros usados (URL, headless, profile).
- Detecções de navegação e mudança de URL.
- Warnings sobre elementos não encontrados ou erros de permissão.

### 3. Performance
Permite analisar quanto tempo cada etapa (carregamento, extração de elementos) demorou através dos timestamps de cada linha.

**Exemplo:**
```
2026-01-17 01:00:00 | INFO     | gen_food | Navegação detectada: https://exemplo.com/home...
2026-01-17 01:00:05 | WARNING  | project.core.elements | Seletor instável detectado...
```
