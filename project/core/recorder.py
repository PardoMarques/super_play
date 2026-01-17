"""Gravador de ações do usuário via hooks JavaScript."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Callable
from playwright.sync_api import Page, BrowserContext

from .log import get_logger

logger = get_logger(__name__)

# Script JavaScript para capturar eventos do usuário
RECORDER_SCRIPT = """
(() => {
    // Evita injeção dupla
    if (window.__superPlayRecorder) return;
    window.__superPlayRecorder = true;
    
    // Configuração de mascaramento
    const SENSITIVE_TYPES = ['password'];
    const SENSITIVE_AUTOCOMPLETE = ['password', 'current-password', 'new-password'];
    
    // Função para verificar se input é sensível
    function isSensitiveInput(el) {
        if (!el) return false;
        const type = (el.type || '').toLowerCase();
        const autocomplete = (el.autocomplete || '').toLowerCase();
        return SENSITIVE_TYPES.includes(type) || 
               SENSITIVE_AUTOCOMPLETE.some(s => autocomplete.includes(s));
    }
    
    // Função para gerar candidatos de seletores
    function getCandidates(el) {
        const candidates = [];
        const tag = el.tagName.toLowerCase();
        
        // 1. data-testid
        const testid = el.getAttribute('data-testid') || 
                       el.getAttribute('data-test-id') || 
                       el.getAttribute('data-test');
        if (testid) {
            candidates.push({
                strategy: 'data-testid',
                selector: `[data-testid="${testid}"]`
            });
        }
        
        // 2. id
        if (el.id) {
            candidates.push({
                strategy: 'id',
                selector: `#${el.id}`
            });
        }
        
        // 3. name
        if (el.name) {
            candidates.push({
                strategy: 'name',
                selector: `${tag}[name="${el.name}"]`
            });
        }
        
        // 4. aria-label
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) {
            candidates.push({
                strategy: 'aria-label',
                selector: `${tag}[aria-label="${ariaLabel}"]`
            });
        }
        
        // 5. role + text
        const role = el.getAttribute('role');
        const text = (el.textContent || '').trim().substring(0, 30);
        if (role && text) {
            candidates.push({
                strategy: 'role+name',
                selector: `getByRole('${role}', {name: '${text}'})`,
                notes: 'Playwright getByRole'
            });
        }
        
        // 6. placeholder
        if (el.placeholder) {
            candidates.push({
                strategy: 'placeholder',
                selector: `${tag}[placeholder="${el.placeholder}"]`
            });
        }
        
        // 7. css path curto (fallback)
        if (candidates.length === 0) {
            let path = [];
            let current = el;
            let depth = 0;
            while (current && current !== document.body && depth < 3) {
                let selector = current.tagName.toLowerCase();
                if (current.id) {
                    path.unshift('#' + current.id);
                    break;
                }
                const parent = current.parentElement;
                if (parent) {
                    const siblings = Array.from(parent.children).filter(
                        c => c.tagName === current.tagName
                    );
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        selector += `:nth-child(${index})`;
                    }
                }
                path.unshift(selector);
                current = parent;
                depth++;
            }
            candidates.push({
                strategy: 'css-path',
                selector: path.join(' > '),
                notes: 'Fallback'
            });
        }
        
        return candidates;
    }
    
    // Função para extrair info do elemento
    function getElementInfo(el) {
        if (!el || !el.tagName) return null;
        
        return {
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            name: el.name || null,
            type: el.type || null,
            textPreview: (el.textContent || '').trim().substring(0, 50),
            placeholder: el.placeholder || null,
            href: el.href || null,
            candidates: getCandidates(el)
        };
    }
    
    // Envia evento para Python
    function sendEvent(type, el, extra = {}) {
        const element = getElementInfo(el);
        const event = {
            ts: new Date().toISOString(),
            type: type,
            url: window.location.href,
            element: element,
            ...extra
        };
        
        // Envia via binding exposto pelo Playwright
        if (window.__recordAction) {
            window.__recordAction(JSON.stringify(event));
        }
    }
    
    // Listener de click
    document.addEventListener('click', (e) => {
        const el = e.target;
        sendEvent('click', el);
    }, true);
    
    // Listener de input (com debounce)
    let inputTimeout = null;
    document.addEventListener('input', (e) => {
        const el = e.target;
        clearTimeout(inputTimeout);
        inputTimeout = setTimeout(() => {
            const isSensitive = isSensitiveInput(el);
            const value = isSensitive ? '***' : (el.value || '').substring(0, 100);
            sendEvent('input', el, { 
                value: value,
                masked: isSensitive
            });
        }, 300);
    }, true);
    
    // Listener de change (selects, checkboxes, etc)
    document.addEventListener('change', (e) => {
        const el = e.target;
        const isSensitive = isSensitiveInput(el);
        let value = null;
        
        if (el.type === 'checkbox' || el.type === 'radio') {
            value = el.checked;
        } else if (el.tagName.toLowerCase() === 'select') {
            value = el.options[el.selectedIndex]?.text || el.value;
        } else if (!isSensitive) {
            value = (el.value || '').substring(0, 100);
        } else {
            value = '***';
        }
        
        sendEvent('change', el, { value: value, masked: isSensitive });
    }, true);
    
    // Listener de submit
    document.addEventListener('submit', (e) => {
        const el = e.target;
        sendEvent('submit', el);
    }, true);
    
    // Listener de keydown (Enter, Escape)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === 'Escape') {
            sendEvent('keydown', e.target, { key: e.key });
        }
    }, true);
    
    console.log('[SuperPlay] Recorder ativo');
})();
"""


class ActionRecorder:
    """Gravador de ações do usuário."""
    
    def __init__(self, output_path: Path, mask_sensitive: bool = True):
        """
        Inicializa o gravador.
        
        Args:
            output_path: Caminho para salvar actions.ndjson
            mask_sensitive: Se True, mascara dados sensíveis.
        """
        self.output_path = output_path
        self.mask_sensitive = mask_sensitive
        self.actions: List[Dict[str, Any]] = []
        self._file = None
    
    def start(self) -> None:
        """Inicia gravação, abrindo arquivo para escrita."""
        self._file = open(self.output_path, "w", encoding="utf-8")
        logger.info(f"Gravação iniciada: {self.output_path}")
    
    def record_action(self, action_json: str) -> None:
        """
        Grava uma ação recebida do browser.
        
        Args:
            action_json: JSON string com dados da ação.
        """
        try:
            action = json.loads(action_json)
            self.actions.append(action)
            
            # Escreve imediatamente no arquivo (ndjson)
            if self._file:
                self._file.write(json.dumps(action, ensure_ascii=False) + "\n")
                self._file.flush()
            
            # Log resumido
            action_type = action.get("type", "?")
            element = action.get("element", {})
            tag = element.get("tag", "?") if element else "?"
            selector = ""
            candidates = element.get("candidates", []) if element else []
            if candidates:
                selector = candidates[0].get("selector", "")[:40]
            
            logger.info(f"[{action_type}] {tag} → {selector}")
            
        except Exception as e:
            logger.warning(f"Erro ao gravar ação: {e}")
    
    def stop(self) -> List[Dict[str, Any]]:
        """
        Para gravação e retorna ações.
        
        Returns:
            Lista de ações gravadas.
        """
        if self._file:
            self._file.close()
            self._file = None
        
        logger.info(f"Gravação finalizada: {len(self.actions)} ações")
        return self.actions
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo das ações gravadas.
        
        Returns:
            Dicionário com resumo.
        """
        action_types = {}
        urls_visited = set()
        
        for action in self.actions:
            action_type = action.get("type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1
            urls_visited.add(action.get("url", ""))
        
        return {
            "total_actions": len(self.actions),
            "action_types": action_types,
            "urls_visited": list(urls_visited),
        }


def setup_recorder(context: BrowserContext, page: Page, recorder: ActionRecorder) -> None:
    """
    Configura gravador de ações no browser.
    
    Args:
        context: Contexto do browser.
        page: Página inicial.
        recorder: Instância do ActionRecorder.
    """
    # Expõe função Python para o JavaScript chamar
    context.expose_binding(
        "__recordAction",
        lambda source, action_json: recorder.record_action(action_json)
    )
    
    # Injeta script em todas as páginas (atuais e futuras)
    context.add_init_script(RECORDER_SCRIPT)
    
    # Injeta na página atual também
    page.evaluate(RECORDER_SCRIPT)
    
    logger.info("Recorder configurado no browser")
