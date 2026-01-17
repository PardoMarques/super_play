# 🔮 Funcionalidade Futura: Visual Regression + OCR

> **Status:** Planejado

## Conceito

Comparação visual entre execuções com **análise OCR integrada** para:
- Identificar e correlacionar elementos por texto visível
- Avaliar aspectos de **UX/UI**
- Aplicar **Heurísticas de Nielsen** automaticamente

## Uso Esperado

```powershell
python gen_diff.py --base artifacts/runs/golden --target artifacts/runs/current --ocr --nielsen
```

## Funcionalidades

### 1. Diff Visual (Pixel-by-Pixel)

Compara screenshots e gera mapa de calor das diferenças:
- Mudanças de layout
- Cores alteradas
- Elementos desaparecidos

### 2. OCR para Correlação de Elementos

Ao invés de depender apenas de seletores, o OCR lê o texto visível:

| Elemento | Seletor | Texto OCR |
|----------|---------|-----------|
| Botão | `#btn-submit` | "Enviar" |
| Campo | `#email` | "E-mail:" (label adjacente) |

**Benefício:** Se o seletor mudar mas o texto continuar, o sistema identifica como o mesmo elemento.

### 3. Análise UX/UI

Métricas extraídas automaticamente:

| Métrica | O que Mede |
|---------|------------|
| Contraste | Texto legível sobre fundo? |
| Espaçamento | Elementos muito próximos? |
| Alinhamento | Elementos alinhados corretamente? |
| Densidade | Tela sobrecarregada? |

### 4. Heurísticas de Nielsen (Automação)

Avaliação automática baseada nas 10 heurísticas:

| Heurística | Verificação Automática |
|------------|------------------------|
| Visibilidade do status | Existe feedback visual após ações? |
| Correspondência com mundo real | Linguagem comum ou técnica? (OCR) |
| Controle do usuário | Botões de cancelar/voltar existem? |
| Consistência | Mesmos elementos em posições similares entre telas? |
| Prevenção de erros | Campos obrigatórios marcados? |
| Reconhecimento | Labels claros vs campos sem identificação? |
| Flexibilidade | Atalhos visíveis? |
| Design minimalista | Informações irrelevantes na tela? |
| Ajuda ao usuário | Mensagens de erro claras? |
| Documentação | Links de ajuda disponíveis? |

## Saída

Relatório HTML/PDF com:
1. **Diff visual** (antes/depois)
2. **Score UX** (0-100)
3. **Violações de Nielsen** identificadas
4. **Sugestões de melhoria**
5. **Atributos visuais por elemento** (para feedback ao Chaplin)

---

## Atributos Visuais para Elementos Funcionais

O Visual Regression extrai **atributos-chave** de cada elemento interativo, servindo de insumo para o Chaplin.

### Legibilidade

| Problema | Como Detecta | Exemplo |
|----------|--------------|---------|
| Texto ilegível | Contraste texto/fundo < 4.5:1 (WCAG AA) | Letra branca em botão cinza claro |
| Texto cortado | OCR detecta truncamento (...) ou overflow | "Adicionar ao carr..." |
| Fonte muito pequena | Tamanho < 12px | Termos de uso em 8px |

### Semântica de Cores

| Problema | Como Detecta | Exemplo |
|----------|--------------|---------|
| Cores invertidas | Botão "Voltar" verde, "Avançar" vermelho | Confunde usuário |
| Cores sem significado | Botões importantes sem destaque | Todos cinzas iguais |
| Daltonismo | Depende só de cor para diferenciar | Vermelho/verde sem ícone |

### Ajuste de Conteúdo

| Problema | Como Detecta | Exemplo |
|----------|--------------|---------|
| Texto desalinhado | Bounding box do texto vs container | Texto encostado na borda |
| Imagem esticada | Aspect ratio diferente do original | Logo distorcida |
| Espaçamento irregular | Padding assimétrico | Botão com texto colado à esquerda |
| Overflow | Conteúdo vazando do container | Texto saindo do card |

### Saída por Elemento (JSON)

```json
{
  "selector": "#btn-voltar",
  "text_ocr": "Voltar",
  "issues": [
    {
      "type": "semantic_color",
      "severity": "high",
      "detail": "Botão 'Voltar' com cor verde (#22c55e). Esperado: neutro ou vermelho."
    },
    {
      "type": "text_alignment",
      "severity": "medium",
      "detail": "Texto desalinhado 8px à esquerda do centro."
    }
  ],
  "contrast_ratio": 3.2,
  "font_size_px": 14,
  "bounding_box": {"x": 120, "y": 450, "w": 100, "h": 40}
}
```

---

## Integração com Chaplin

Os atributos visuais alimentam a base de conhecimento do Chaplin:

```
Visual Regression → element_issues.json → Chaplin RAG
                                              ↓
                    Dicas: "Botão 'Voltar' com cor verde pode confundir usuários"
```

O Chaplin usa essas informações para:
- Gerar **docstrings de alerta** nos Page Objects
- Incluir **warnings** no relatório de riscos
- Sugerir **melhorias de acessibilidade** no código gerado

---

## Tecnologia

- **OCR:** Tesseract ou Cloud Vision API
- **Diff:** OpenCV / pixelmatch
- **Análise de Cor:** colormath (contraste WCAG)
- **Bounding Boxes:** Playwright `element.bounding_box()`

---

*Visual Regression que vai além do pixel: entende o significado da interface e alimenta a inteligência do Chaplin.*

