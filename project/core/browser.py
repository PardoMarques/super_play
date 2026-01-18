"""
Playwright browser management.
Gerenciamento de browser Playwright.
"""

from typing import Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from .log import get_logger

logger = get_logger(__name__)


def create_browser_context(
    headless: bool = False,
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Creates Playwright browser context.
    
    Args:
        headless: If True, runs without visible window.
    
    Returns:
        Tuple (browser, context, page).
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
    Safely closes browser and context.
    
    Args:
        browser: Browser instance.
        context: Browser context.
    """
    try:
        context.close()
        if browser:
            browser.close()
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")
