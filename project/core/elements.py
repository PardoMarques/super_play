"""Extração e análise de elementos DOM."""

from typing import List, Dict, Any, Optional
from playwright.sync_api import Page

from .log import get_logger

logger = get_logger(__name__)

# Atributos sensíveis que devem ser mascarados
SENSITIVE_TYPES = {"password"}
SENSITIVE_AUTOCOMPLETE = {"password", "current-password", "new-password"}


def extract_elements(page: Page, mask_sensitive: bool = True) -> Dict[str, Any]:
    """
    Extrai elementos interativos da página com candidatos de seletores.
    
    Args:
        page: Página Playwright.
        mask_sensitive: Se True, mascara valores de inputs sensíveis.
    
    Returns:
        Dicionário com page_signals e lista de elements.
    """
    # Script JavaScript para extrair elementos
    js_script = """
    () => {
        // Elementos interativos para extrair
        const interactiveSelectors = [
            'a[href]',
            'button',
            'input',
            'select',
            'textarea',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="switch"]',
            '[role="tab"]',
            '[role="menuitem"]',
            '[onclick]',
            '[data-testid]',
            '[data-test-id]',
            '[data-test]',
        ];
        
        const allElements = document.querySelectorAll(interactiveSelectors.join(','));
        const elements = [];
        const seen = new Set();
        
        // Sinais da página
        const pageSignals = {
            has_data_testid: document.querySelector('[data-testid], [data-test-id], [data-test]') !== null,
            has_aria_roles: document.querySelector('[role]') !== null,
            likely_spa: !!(window.React || window.Vue || window.angular || window.__NUXT__ || window.__NEXT_DATA__),
        };
        
        // Função para gerar css path curto
        function getCssPath(el, maxDepth = 3) {
            const path = [];
            let current = el;
            let depth = 0;
            
            while (current && current !== document.body && depth < maxDepth) {
                let selector = current.tagName.toLowerCase();
                
                if (current.id) {
                    selector = '#' + current.id;
                    path.unshift(selector);
                    break;
                }
                
                const parent = current.parentElement;
                if (parent) {
                    const siblings = Array.from(parent.children).filter(
                        c => c.tagName === current.tagName
                    );
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        selector += ':nth-child(' + index + ')';
                    }
                }
                
                path.unshift(selector);
                current = parent;
                depth++;
            }
            
            return path.join(' > ');
        }
        
        // Função para gerar xpath curto
        function getXPath(el, maxDepth = 3) {
            const path = [];
            let current = el;
            let depth = 0;
            
            while (current && current !== document.body && depth < maxDepth) {
                let selector = current.tagName.toLowerCase();
                
                if (current.id) {
                    return '//' + selector + '[@id="' + current.id + '"]';
                }
                
                const parent = current.parentElement;
                if (parent) {
                    const siblings = Array.from(parent.children).filter(
                        c => c.tagName === current.tagName
                    );
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        selector += '[' + index + ']';
                    }
                }
                
                path.unshift(selector);
                current = parent;
                depth++;
            }
            
            return '//' + path.join('/');
        }
        
        // Função para obter texto do label associado
        function getLabelText(el) {
            if (el.id) {
                const label = document.querySelector('label[for="' + el.id + '"]');
                if (label) return label.textContent.trim().substring(0, 50);
            }
            // Label pai
            const parentLabel = el.closest('label');
            if (parentLabel) return parentLabel.textContent.trim().substring(0, 50);
            return null;
        }
        
        allElements.forEach(el => {
            // Evita duplicatas
            const key = el.tagName + '_' + (el.id || el.name || Math.random());
            if (seen.has(key)) return;
            seen.add(key);
            
            const tag = el.tagName.toLowerCase();
            const textContent = (el.textContent || el.innerText || '').trim().substring(0, 50);
            const inputValue = el.value || '';
            
            // Atributos relevantes
            const attrs = {};
            ['id', 'name', 'placeholder', 'type', 'href', 'role', 'aria-label'].forEach(attr => {
                const val = el.getAttribute(attr);
                if (val) attrs[attr] = val;
            });
            
            // Data-testid (várias variações)
            ['data-testid', 'data-test-id', 'data-test'].forEach(attr => {
                const val = el.getAttribute(attr);
                if (val) attrs[attr] = val;
            });
            
            // Verifica se é input sensível
            const isSensitive = 
                attrs.type === 'password' ||
                (el.getAttribute('autocomplete') || '').toLowerCase().includes('password');
            
            // Gera candidatos de seletores (ordem de prioridade)
            const candidates = [];
            
            // 1. data-testid
            if (attrs['data-testid']) {
                candidates.push({
                    strategy: 'data-testid',
                    selector: '[data-testid="' + attrs['data-testid'] + '"]',
                });
            }
            if (attrs['data-test-id']) {
                candidates.push({
                    strategy: 'data-test-id',
                    selector: '[data-test-id="' + attrs['data-test-id'] + '"]',
                });
            }
            if (attrs['data-test']) {
                candidates.push({
                    strategy: 'data-test',
                    selector: '[data-test="' + attrs['data-test'] + '"]',
                });
            }
            
            // 2. id
            if (attrs.id) {
                candidates.push({
                    strategy: 'id',
                    selector: '#' + attrs.id,
                });
            }
            
            // 3. name
            if (attrs.name) {
                candidates.push({
                    strategy: 'name',
                    selector: tag + '[name="' + attrs.name + '"]',
                });
            }
            
            // 4. aria-label
            if (attrs['aria-label']) {
                candidates.push({
                    strategy: 'aria-label',
                    selector: tag + '[aria-label="' + attrs['aria-label'] + '"]',
                });
            }
            
            // 5. role + accessible name
            if (attrs.role && textContent) {
                candidates.push({
                    strategy: 'role+name',
                    selector: "getByRole('" + attrs.role + "', {name: '" + textContent.substring(0, 30) + "'})",
                    notes: 'Playwright getByRole',
                });
            }
            
            // 6. label-for
            const labelText = getLabelText(el);
            if (labelText) {
                candidates.push({
                    strategy: 'label-for',
                    selector: "getByLabel('" + labelText.substring(0, 30) + "')",
                    notes: 'Playwright getByLabel',
                });
            }
            
            // 7. placeholder
            if (attrs.placeholder) {
                candidates.push({
                    strategy: 'placeholder',
                    selector: tag + '[placeholder="' + attrs.placeholder + '"]',
                });
            }
            
            // 8. css-path (fallback)
            const cssPath = getCssPath(el);
            if (cssPath && candidates.length < 5) {
                candidates.push({
                    strategy: 'css-path',
                    selector: cssPath,
                    notes: 'Fallback - pode ser frágil',
                });
            }
            
            // 9. xpath (último recurso)
            if (candidates.length === 0) {
                const xpath = getXPath(el);
                candidates.push({
                    strategy: 'xpath',
                    selector: xpath,
                    notes: 'Último recurso - muito frágil',
                });
            }
            
            elements.push({
                tag,
                textPreview: textContent || null,
                attrs,
                isSensitive,
                candidates,
            });
        });
        
        return { pageSignals, elements };
    }
    """;
    
    try:
        result = page.evaluate(js_script)
        
        elements = result.get("elements", [])
        page_signals = result.get("pageSignals", {})
        
        # Processa mascaramento se necessário
        if mask_sensitive:
            for el in elements:
                if el.get("isSensitive"):
                    el["textPreview"] = "***"
                    if "value" in el:
                        el["value"] = "***"
        
        # Remove flag interna
        for el in elements:
            el.pop("isSensitive", None)
        
        logger.info(f"Extraídos {len(elements)} elementos interativos")
        
        return {
            "page_signals": page_signals,
            "elements": elements,
        }
        
    except Exception as e:
        logger.error(f"Erro ao extrair elementos: {e}")
        return {
            "page_signals": {},
            "elements": [],
        }


def capture_snapshot(
    page: Page,
    html_path: str,
    screenshot_path: str,
) -> None:
    """
    Captura HTML e screenshot da página.
    
    Args:
        page: Página Playwright.
        html_path: Caminho para salvar HTML.
        screenshot_path: Caminho para salvar screenshot.
    """
    # Captura HTML
    html_content = page.content()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"HTML salvo: {html_path}")
    
    # Captura screenshot
    page.screenshot(path=screenshot_path, full_page=True)
    logger.info(f"Screenshot salvo: {screenshot_path}")
