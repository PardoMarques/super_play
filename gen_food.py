#!/usr/bin/env python3
"""
Gen Food - Automation data collector.
Coletor de dados para automacao.

Collects page snapshot, interactive element inventory
and selector candidates to improve PageObjects.
Coleta snapshot da pagina, inventario de elementos interativos
e candidatos de seletores para melhorar PageObjects.

Interact mode: records user actions in real time.
Modo interact: grava acoes do usuario em tempo real.

Does NOT generate replay scripts or automatic PageObjects.
NAO gera scripts de replay ou PageObjects automaticos.
"""


import argparse
import json
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from project.core import (
    get_config,
    create_run_dirs,
    generate_run_id,
    get_logger,
    create_browser_context,
    close_browser,
    extract_elements,
    capture_snapshot,
    ActionRecorder,
    setup_recorder,
)
from project.core.log import setup_file_logging, close_file_logging

logger = get_logger("gen_food")

SCHEMA_VERSION = "1.0"


def run_snapshot(
    url: str,
    dirs: dict,
    run_id: str,
    headless: bool,
    mask_sensitive: bool,
) -> dict:
    """
    Executes collection in snapshot mode.
    Executa coleta em modo snapshot.
    
    Args:
        url: URL to collect. / URL para coletar.
        dirs: Run directories dictionary. / Dicionario de diretorios do run.
        run_id: Execution ID. / ID da execucao.
        headless: If True, runs without window. / Se True, roda sem janela.
        mask_sensitive: If True, masks sensitive data. / Se True, mascara dados sensiveis.
    
    Returns:
        Dictionary with collection results. / Dicionario com resultados da coleta.
    """
    logger.info(f"Starting snapshot of: {url}")
    
    # Create browser
    browser, context, page = create_browser_context(
        headless=headless,
    )
    
    try:
        # Navigate to URL
        page.goto(url, wait_until="networkidle", timeout=30000)
        logger.info(f"Page loaded: {page.title()}")
        
        # Wait a bit for JS to load
        page.wait_for_timeout(2000)
        
        # Capture snapshot
        html_path = dirs["html"] / "page.html"
        screenshot_path = dirs["screenshots"] / "page.png"
        capture_snapshot(page, str(html_path), str(screenshot_path))
        
        # Extract elements
        extraction = extract_elements(page, mask_sensitive=mask_sensitive)
        
        # Build food.json
        timestamp = datetime.now(timezone.utc).isoformat()
        food_data = {
            "schema_version": SCHEMA_VERSION,
            "url": url,
            "run_id": run_id,
            "timestamp": timestamp,
            "page_signals": extraction["page_signals"],
            "elements": extraction["elements"],
        }
        
        # Save food.json
        food_path = dirs["food"] / "food.json"
        with open(food_path, "w", encoding="utf-8") as f:
            json.dump(food_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Food saved: {food_path}")
        
        return {
            "success": True,
            "elements_count": len(extraction["elements"]),
            "page_signals": extraction["page_signals"],
        }
        
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
        
    finally:
        close_browser(browser, context)


def run_interact(
    url: str,
    dirs: dict,
    run_id: str,
    headless: bool,
    mask_sensitive: bool,
) -> dict:
    """
    Interact mode - records user actions.
    Modo interact - grava acoes do usuario.
    
    Opens browser for manual interaction, records all actions,
    and finishes when browser closes or Ctrl+C is pressed.
    Abre browser para interacao manual, grava todas as acoes,
    e finaliza ao fechar o browser ou pressionar Ctrl+C.
    
    Args:
        url: URL to navigate. / URL para navegar.
        dirs: Run directories dictionary. / Dicionario de diretorios do run.
        run_id: Execution ID. / ID da execucao.
        headless: Ignored - interact always uses headed. / Ignorado - interact sempre usa headed.
        mask_sensitive: If True, masks sensitive data. / Se True, mascara dados sensiveis.
    
    Returns:
        Dictionary with collection results. / Dicionario com resultados da coleta.
    """
    # Interact always uses headed (needs window for interaction)
    if headless:
        logger.warning("Interact mode ignores --headless (needs window)")
    
    logger.info(f"Starting INTERACT mode for: {url}")
    logger.info("=" * 60)
    logger.info("RECORDING ACTIVE")
    logger.info("Interact with the page normally.")
    logger.info("To finish: close the browser or press Ctrl+C")
    logger.info("=" * 60)
    
    # Create action recorder
    actions_path = dirs["food"] / "actions.ndjson"
    recorder = ActionRecorder(actions_path, mask_sensitive=mask_sensitive)
    recorder.start()
    
    # Create browser (always headed)
    browser, context, page = create_browser_context(
        headless=False,  # Always headed
    )
    
    # Flag for interrupt control
    interrupted = False
    
    def handle_interrupt(sig, frame):
        nonlocal interrupted
        interrupted = True
        logger.info("\nCtrl+C detected. Finishing...")
    
    # Register Ctrl+C handler
    original_handler = signal.signal(signal.SIGINT, handle_interrupt)
    
    # pageId system - maps normalized URL to pageId
    pages_visited: dict = {}  # {normalized_url: {"pageId": int, "title": str, "first_visit": str}}
    next_page_id = 1
    current_url = ""
    
    def normalize_url(raw_url: str) -> str:
        """Normalizes URL removing query strings and fragments for comparison."""
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(raw_url)
        # Keep scheme, netloc, path - remove query and fragment
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    
    def get_or_create_page_id(raw_url: str, title: str = "") -> tuple:
        """
        Returns (pageId, is_new) for the URL.
        If URL was already visited, returns existing pageId and is_new=False.
        """
        nonlocal next_page_id
        normalized = normalize_url(raw_url)
        
        if normalized in pages_visited:
            return pages_visited[normalized]["pageId"], False
        
        # New page
        page_id = next_page_id
        next_page_id += 1
        pages_visited[normalized] = {
            "pageId": page_id,
            "url": raw_url,
            "title": title,
            "first_visit": datetime.now(timezone.utc).isoformat(),
        }
        return page_id, True
    
    def capture_page_snapshot(page_obj, page_id: int, is_new: bool) -> None:
        """
        Captures screenshot (always) and HTML (only if new page).
        Screenshot: <timestamp>_page_<pageId>.png
        HTML: page_<pageId>.html (only if is_new)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Screenshot always with timestamp
        screenshot_name = f"{timestamp}_page_{page_id}.png"
        screenshot_path = dirs["screenshots"] / screenshot_name
        try:
            page_obj.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path.name}")
        except Exception as e:
            logger.warning(f"Error saving screenshot: {e}")
        
        # HTML only if new page (not repeated)
        if is_new:
            html_name = f"page_{page_id}.html"
            html_path = dirs["html"] / html_name
            try:
                html_content = page_obj.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"HTML saved: {html_path.name}")
            except Exception as e:
                logger.warning(f"Error saving HTML: {e}")
    
    try:
        # Configure recorder in browser
        setup_recorder(context, page, recorder)
        
        # Navigate to URL (uses 'load' instead of 'networkidle' for SPAs)
        page.goto(url, wait_until="load", timeout=30000)
        title = page.title()
        logger.info(f"Page loaded: {title}")
        
        # Register initial page
        current_url = page.url
        page_id, is_new = get_or_create_page_id(current_url, title)
        logger.info(f"Page ID: {page_id} (new: {is_new})")
        
        # Initial capture
        capture_page_snapshot(page, page_id, is_new)
        
        # Loop waiting for close or interrupt
        logger.info("Waiting for interactions...")
        
        while not interrupted:
            try:
                # Check if there are still pages open in context
                if not context.pages:
                    logger.info("Browser closed by user.")
                    break
                
                # Get current active page (may change during SPA navigation)
                current_page = context.pages[-1]
                
                # Check if page responds
                current_page.evaluate("1")
                
                # Check if URL changed (navigation)
                new_url = current_page.url
                if new_url != current_url:
                    current_url = new_url
                    page = current_page
                    title = page.title()
                    
                    page_id, is_new = get_or_create_page_id(current_url, title)
                    logger.info(f"Navigation detected: {current_url[:50]}... -> Page ID: {page_id}")
                    
                    # Capture screenshot (always) and HTML (only if new)
                    capture_page_snapshot(page, page_id, is_new)
                
                current_page.wait_for_timeout(500)
                    
            except Exception as e:
                # Check if it's really closing or just temporary error
                try:
                    if not context.pages:
                        logger.info("Browser closed by user.")
                        break
                    # If there are still pages, might be navigation - try to continue
                    page = context.pages[-1]
                    continue
                except Exception:
                    logger.info("Browser closed by user.")
                    break
        
        # Try final capture
        try:
            if context.pages:
                page = context.pages[-1]
                page_id, is_new = get_or_create_page_id(page.url, page.title())
                capture_page_snapshot(page, page_id, is_new)
        except Exception:
            logger.info("Using last capture (browser already closed).")
        
        # Extract elements from last page
        extraction = {"page_signals": {}, "elements": []}
        try:
            if context.pages:
                extraction = extract_elements(page, mask_sensitive=mask_sensitive)
        except Exception as e:
            logger.warning(f"Could not extract elements: {e}")
        
        # Stop recording
        actions = recorder.stop()
        summary = recorder.get_summary()
        
        # Build list of visited pages with pageId
        urls_visited_with_id = [
            {
                "pageId": info["pageId"],
                "url": info["url"],
                "title": info["title"],
                "first_visit": info["first_visit"],
            }
            for info in pages_visited.values()
        ]
        
        # Build food.json
        timestamp = datetime.now(timezone.utc).isoformat()
        food_data = {
            "schema_version": SCHEMA_VERSION,
            "url": url,
            "run_id": run_id,
            "timestamp": timestamp,
            "mode": "interact",
            "pages_visited": urls_visited_with_id,
            "page_signals": extraction["page_signals"],
            "elements": extraction["elements"],
            "action_summary": {
                **summary,
                "total_pages": len(pages_visited),
            },
        }
        
        # Save food.json
        food_path = dirs["food"] / "food.json"
        with open(food_path, "w", encoding="utf-8") as f:
            json.dump(food_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Food saved: {food_path}")
        
        return {
            "success": True,
            "elements_count": len(extraction["elements"]),
            "actions_count": summary["total_actions"],
            "pages_count": len(pages_visited),
            "action_types": summary["action_types"],
            "page_signals": extraction["page_signals"],
        }
        
    except Exception as e:
        logger.error(f"Interact error: {e}")
        
        # Try to save what was captured even with error
        try:
            actions = recorder.stop()
            summary = recorder.get_summary()
            
            # If we have actions, consider partial success
            if summary["total_actions"] > 0:
                # Save food.json with what we have
                food_data = {
                    "schema_version": SCHEMA_VERSION,
                    "url": url,
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "mode": "interact",
                    "page_signals": {},
                    "elements": [],
                    "action_summary": summary,
                    "error": str(e),
                }
                food_path = dirs["food"] / "food.json"
                with open(food_path, "w", encoding="utf-8") as f:
                    json.dump(food_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Food saved (partial): {food_path}")
                
                return {
                    "success": True,
                    "partial": True,
                    "elements_count": 0,
                    "actions_count": summary["total_actions"],
                    "action_types": summary["action_types"],
                    "page_signals": {},
                    "warning": str(e),
                }
        except Exception:
            pass
        
        return {
            "success": False,
            "error": str(e),
        }
        
    finally:
        # Restore original handler
        signal.signal(signal.SIGINT, original_handler)
        close_browser(browser, context)


def main():
    parser = argparse.ArgumentParser(
        description="Gen Food - Automation data collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick snapshot
  python gen_food.py --url https://example.com
  
  # Interactive mode (records your actions)
  python gen_food.py --url https://example.com --mode interact
        """,
    )
    
    parser.add_argument(
        "--url",
        type=str,
        required=False,
        help="Target URL to collect data from",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        default="snapshot",
        choices=["snapshot", "interact"],
        help="Collection mode: snapshot (quick) or interact (records actions)",
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser without visible window (snapshot only)",
    )
    
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="WARNING: Disables masking of sensitive data (passwords)",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    url = args.url or config.base_url
    
    if not url:
        logger.error("No URL provided. Use --url or set BASE_URL in .env")
        return 1
    
    # Warning if masking disabled
    mask_sensitive = not args.no_mask
    if not mask_sensitive:
        logger.warning("=" * 60)
        logger.warning("MASKING DISABLED!")
        logger.warning("Sensitive data (passwords) will be saved in plain text!")
        logger.warning("Use only for debugging in safe environment.")
        logger.warning("=" * 60)
    
    # Generate run ID and create directories
    run_id = generate_run_id()
    dirs = create_run_dirs(config.artifacts_dir, run_id)
    
    # Configure file logging
    log_path = dirs["logs"] / "session.log"
    setup_file_logging(log_path)
    
    started_at = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"Run ID: {run_id}")
    logger.info(f"URL: {url}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Headless: {args.headless}")
    logger.info(f"Run dir: {dirs['run']}")
    logger.info(f"Log: {log_path}")
    
    # Execute selected mode
    if args.mode == "snapshot":
        result = run_snapshot(
            url=url,
            dirs=dirs,
            run_id=run_id,
            headless=args.headless,
            mask_sensitive=mask_sensitive,
        )
    else:
        result = run_interact(
            url=url,
            dirs=dirs,
            run_id=run_id,
            headless=args.headless,
            mask_sensitive=mask_sensitive,
        )
    
    # Save meta.json
    meta = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": started_at,
        "url": url,
        "mode": args.mode,
        "headless": args.headless if args.mode == "snapshot" else False,
        "mask_sensitive": mask_sensitive,
        "result": result,
    }
    
    meta_path = dirs["run"] / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Meta saved: {meta_path}")
    
    if result.get("success"):
        elements = result.get('elements_count', 0)
        actions = result.get('actions_count', 0)
        pages = result.get('pages_count', 1)
        if args.mode == "interact":
            logger.info(f"Collection complete! {elements} elements, {actions} actions, {pages} pages.")
        else:
            logger.info(f"Collection complete! {elements} elements extracted.")
        close_file_logging()
        return 0
    else:
        logger.error(f"Collection failed: {result.get('error', 'unknown error')}")
        close_file_logging()
        return 1


if __name__ == "__main__":
    sys.exit(main())
