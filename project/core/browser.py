"""Gerenciamento de browser Playwright."""

from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from .log import get_logger

logger = get_logger(__name__)


def create_browser_context(
    headless: bool = False,
    profile_dir: Optional[str] = None,
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Cria contexto de browser Playwright.
    
    Args:
        headless: Se True, roda sem janela visível.
        profile_dir: Diretório para persistent context (mantém sessão/login).
    
    Returns:
        Tupla (browser, context, page).
    """
    playwright = sync_playwright().start()
    
    if profile_dir:
        # Persistent context mantém cookies, localStorage, etc.
        profile_path = Path(profile_dir).absolute()
        profile_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Usando persistent context: {profile_path}")
        
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=headless,
            viewport={"width": 1280, "height": 720},
        )
        browser = None  # Persistent context não tem browser separado
        
        # Usa página existente ou cria nova
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()
    else:
        # Contexto normal (sem persistência)
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()
    
    return browser, context, page


def close_browser(browser: Optional[Browser], context: BrowserContext) -> None:
    """
    Fecha browser e contexto de forma segura.
    
    Args:
        browser: Instância do browser (pode ser None para persistent context).
        context: Contexto do browser.
    """
    try:
        context.close()
        if browser:
            browser.close()
    except Exception as e:
        logger.warning(f"Erro ao fechar browser: {e}")
