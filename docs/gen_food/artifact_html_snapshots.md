# 📁 Artifact: HTML (`html/`)

Este diretório armazena os snapshots do código-fonte (DOM) das páginas visitadas.

## Arquivos Gerados

- `page_1.html`
- `page_2.html`
- ...

Onde o número corresponde ao `pageId` gerado (veja `food.json`).

## Importância

### 1. Fonte da Verdade para Seletores
Se um seletor falha no futuro, podemos abrir este HTML localmente e testar o seletor nele. Isso elimina a dúvida "será que o site mudou?" pois temos a cópia exata do momento da coleta.

### 2. Debugging Offline
Permite inspecionar a estrutura da página exatamente como ela estava, sem precisar acessar o site novamente (que pode ter mudado ou estar fora do ar).

### 3. Evidência de Conteúdo
Serve como prova do texto e dados que estavam visíveis na tela no momento da execução.

## Comportamento
- O HTML é salvo apenas na **primeira visita** a uma URL única (para economizar espaço).
- Se você voltar para a mesma página, o `gen_food` reutiliza o mesmo ID e não duplica o arquivo.
