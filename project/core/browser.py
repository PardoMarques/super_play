"""Gerenciamento de browser Playwright."""

from typing import Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from .log import get_logger

logger = get_logger(__name__)


def create_browser_context(
    headless: bool = False,
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Cria contexto de browser Playwright.
    
    Args:
        headless: Se True, roda sem janela visível.
    
    Returns:
        Tupla (browser, context, page).
    """
    playwright = sync_playwright().start()
    
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()
    
    return browser, context, page


def close_browser(browser: Browser, context: BrowserContext) -> None:
    """
    Fecha browser e contexto de forma segura.
    
    Args:
        browser: Instância do browser.
        context: Contexto do browser.
    """
    try:
        context.close()
        if browser:
            browser.close()
    except Exception as e:
        logger.warning(f"Erro ao fechar browser: {e}")
