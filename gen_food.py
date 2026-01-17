#!/usr/bin/env python3
"""
Gen Food - Coletor de dados para automação.

Coleta snapshot da página, inventário de elementos interativos
e candidatos de seletores para melhorar PageObjects.

Modo interact: grava ações do usuário em tempo real.

NÃO gera scripts de replay ou PageObjects automáticos.
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
    profile_dir: str | None,
    mask_sensitive: bool,
) -> dict:
    """
    Executa coleta em modo snapshot.
    
    Args:
        url: URL para coletar.
        dirs: Dicionário de diretórios do run.
        run_id: ID da execução.
        headless: Se True, roda sem janela.
        profile_dir: Diretório de perfil para sessão persistente.
        mask_sensitive: Se True, mascara dados sensíveis.
    
    Returns:
        Dicionário com resultados da coleta.
    """
    logger.info(f"Iniciando snapshot de: {url}")
    
    # Cria browser
    browser, context, page = create_browser_context(
        headless=headless,
        profile_dir=profile_dir,
    )
    
    try:
        # Navega para URL
        page.goto(url, wait_until="networkidle", timeout=30000)
        logger.info(f"Página carregada: {page.title()}")
        
        # Aguarda um pouco para JS carregar
        page.wait_for_timeout(2000)
        
        # Captura snapshot
        html_path = dirs["html"] / "page.html"
        screenshot_path = dirs["screenshots"] / "page.png"
        capture_snapshot(page, str(html_path), str(screenshot_path))
        
        # Extrai elementos
        extraction = extract_elements(page, mask_sensitive=mask_sensitive)
        
        # Monta food.json
        timestamp = datetime.now(timezone.utc).isoformat()
        food_data = {
            "schema_version": SCHEMA_VERSION,
            "url": url,
            "run_id": run_id,
            "timestamp": timestamp,
            "page_signals": extraction["page_signals"],
            "elements": extraction["elements"],
        }
        
        # Salva food.json
        food_path = dirs["food"] / "food.json"
        with open(food_path, "w", encoding="utf-8") as f:
            json.dump(food_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Food salvo: {food_path}")
        
        return {
            "success": True,
            "elements_count": len(extraction["elements"]),
            "page_signals": extraction["page_signals"],
        }
        
    except Exception as e:
        logger.error(f"Erro no snapshot: {e}")
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
    profile_dir: str | None,
    mask_sensitive: bool,
) -> dict:
    """
    Modo interact - grava ações do usuário.
    
    Abre browser para interação manual, grava todas as ações,
    e finaliza ao fechar o browser ou pressionar Ctrl+C.
    
    Args:
        url: URL para navegar.
        dirs: Dicionário de diretórios do run.
        run_id: ID da execução.
        headless: Ignorado - interact sempre usa headed.
        profile_dir: Diretório de perfil para sessão persistente.
        mask_sensitive: Se True, mascara dados sensíveis.
    
    Returns:
        Dicionário com resultados da coleta.
    """
    # Interact sempre usa headed (precisa de janela para interação)
    if headless:
        logger.warning("Modo interact ignora --headless (precisa de janela)")
    
    logger.info(f"Iniciando modo INTERACT para: {url}")
    logger.info("=" * 60)
    logger.info("🎬 GRAVAÇÃO ATIVA")
    logger.info("Interaja com a página normalmente.")
    logger.info("Para finalizar: feche o browser ou pressione Ctrl+C")
    logger.info("=" * 60)
    
    # Cria gravador de ações
    actions_path = dirs["food"] / "actions.ndjson"
    recorder = ActionRecorder(actions_path, mask_sensitive=mask_sensitive)
    recorder.start()
    
    # Cria browser (sempre headed)
    browser, context, page = create_browser_context(
        headless=False,  # Sempre headed
        profile_dir=profile_dir,
    )
    
    # Flag para controle de interrupção
    interrupted = False
    
    def handle_interrupt(sig, frame):
        nonlocal interrupted
        interrupted = True
        logger.info("\n🛑 Ctrl+C detectado. Finalizando...")
    
    # Registra handler de Ctrl+C
    original_handler = signal.signal(signal.SIGINT, handle_interrupt)
    
    # Sistema de pageId - mapeia URL normalizada para pageId
    pages_visited: dict = {}  # {url_normalizada: {"pageId": int, "title": str, "first_visit": str}}
    next_page_id = 1
    current_url = ""
    
    def normalize_url(raw_url: str) -> str:
        """Normaliza URL removendo query strings e fragments para comparação."""
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(raw_url)
        # Mantém scheme, netloc, path - remove query e fragment
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    
    def get_or_create_page_id(raw_url: str, title: str = "") -> tuple:
        """
        Retorna (pageId, is_new) para a URL.
        Se URL já foi visitada, retorna pageId existente e is_new=False.
        """
        nonlocal next_page_id
        normalized = normalize_url(raw_url)
        
        if normalized in pages_visited:
            return pages_visited[normalized]["pageId"], False
        
        # Nova página
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
        Captura screenshot (sempre) e HTML (só se página nova).
        Screenshot: <timestamp>_page_<pageId>.png
        HTML: page_<pageId>.html (só se is_new)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Screenshot sempre com timestamp
        screenshot_name = f"{timestamp}_page_{page_id}.png"
        screenshot_path = dirs["screenshots"] / screenshot_name
        try:
            page_obj.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot salvo: {screenshot_path.name}")
        except Exception as e:
            logger.warning(f"Erro ao salvar screenshot: {e}")
        
        # HTML só se página nova (não repetida)
        if is_new:
            html_name = f"page_{page_id}.html"
            html_path = dirs["html"] / html_name
            try:
                html_content = page_obj.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"HTML salvo: {html_path.name}")
            except Exception as e:
                logger.warning(f"Erro ao salvar HTML: {e}")
    
    try:
        # Configura gravador no browser
        setup_recorder(context, page, recorder)
        
        # Navega para URL (usa 'load' ao invés de 'networkidle' para SPAs)
        page.goto(url, wait_until="load", timeout=30000)
        title = page.title()
        logger.info(f"Página carregada: {title}")
        
        # Registra página inicial
        current_url = page.url
        page_id, is_new = get_or_create_page_id(current_url, title)
        logger.info(f"Página ID: {page_id} (nova: {is_new})")
        
        # Captura inicial
        capture_page_snapshot(page, page_id, is_new)
        
        # Loop aguardando fechamento ou interrupção
        logger.info("Aguardando interações...")
        
        while not interrupted:
            try:
                # Verifica se ainda há páginas abertas no contexto
                if not context.pages:
                    logger.info("Browser fechado pelo usuário.")
                    break
                
                # Pega a página ativa atual (pode mudar durante navegação SPA)
                current_page = context.pages[-1]
                
                # Verifica se a página responde
                current_page.evaluate("1")
                
                # Verifica se a URL mudou (navegação)
                new_url = current_page.url
                if new_url != current_url:
                    current_url = new_url
                    page = current_page
                    title = page.title()
                    
                    page_id, is_new = get_or_create_page_id(current_url, title)
                    logger.info(f"Navegação detectada: {current_url[:50]}... → Page ID: {page_id}")
                    
                    # Captura screenshot (sempre) e HTML (só se nova)
                    capture_page_snapshot(page, page_id, is_new)
                
                current_page.wait_for_timeout(500)
                    
            except Exception as e:
                # Verifica se é realmente fechamento ou só erro temporário
                try:
                    if not context.pages:
                        logger.info("Browser fechado pelo usuário.")
                        break
                    # Se ainda há páginas, pode ser navegação - tenta continuar
                    page = context.pages[-1]
                    continue
                except Exception:
                    logger.info("Browser fechado pelo usuário.")
                    break
        
        # Tenta captura final
        try:
            if context.pages:
                page = context.pages[-1]
                page_id, is_new = get_or_create_page_id(page.url, page.title())
                capture_page_snapshot(page, page_id, is_new)
        except Exception:
            logger.info("Usando última captura (browser já fechado).")
        
        # Extrai elementos da última página
        extraction = {"page_signals": {}, "elements": []}
        try:
            if context.pages:
                extraction = extract_elements(page, mask_sensitive=mask_sensitive)
        except Exception as e:
            logger.warning(f"Não foi possível extrair elementos: {e}")
        
        # Para gravação
        actions = recorder.stop()
        summary = recorder.get_summary()
        
        # Monta lista de páginas visitadas com pageId
        urls_visited_with_id = [
            {
                "pageId": info["pageId"],
                "url": info["url"],
                "title": info["title"],
                "first_visit": info["first_visit"],
            }
            for info in pages_visited.values()
        ]
        
        # Monta food.json
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
        
        # Salva food.json
        food_path = dirs["food"] / "food.json"
        with open(food_path, "w", encoding="utf-8") as f:
            json.dump(food_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Food salvo: {food_path}")
        
        return {
            "success": True,
            "elements_count": len(extraction["elements"]),
            "actions_count": summary["total_actions"],
            "pages_count": len(pages_visited),
            "action_types": summary["action_types"],
            "page_signals": extraction["page_signals"],
        }
        
    except Exception as e:
        logger.error(f"Erro no interact: {e}")
        
        # Tenta salvar o que foi capturado mesmo com erro
        try:
            actions = recorder.stop()
            summary = recorder.get_summary()
            
            # Se temos ações, considera parcialmente sucesso
            if summary["total_actions"] > 0:
                # Salva food.json com o que temos
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
                logger.info(f"Food salvo (parcial): {food_path}")
                
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
        # Restaura handler original
        signal.signal(signal.SIGINT, original_handler)
        close_browser(browser, context)


def main():
    parser = argparse.ArgumentParser(
        description="Gen Food - Coletor de dados para automação",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Snapshot rápido
  python gen_food.py --url https://example.com
  
  # Modo interativo (grava suas ações)
  python gen_food.py --url https://example.com --mode interact
  
  # Com sessão persistente (mantém login)
  python gen_food.py --url https://example.com --profile-dir ./profile
        """,
    )
    
    parser.add_argument(
        "--url",
        type=str,
        required=False,
        help="URL alvo para coletar dados",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        default="snapshot",
        choices=["snapshot", "interact"],
        help="Modo de coleta: snapshot (rápido) ou interact (grava ações)",
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Rodar browser sem janela visível (apenas snapshot)",
    )
    
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=None,
        help="Diretório de perfil para manter sessão/login entre execuções",
    )
    
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="⚠️  ATENÇÃO: Desabilita mascaramento de dados sensíveis (passwords)",
    )
    
    args = parser.parse_args()
    
    # Carrega configuração
    config = get_config()
    url = args.url or config.base_url
    
    if not url:
        logger.error("Nenhuma URL fornecida. Use --url ou defina BASE_URL no .env")
        return 1
    
    # Warning se mascaramento desabilitado
    mask_sensitive = not args.no_mask
    if not mask_sensitive:
        logger.warning("=" * 60)
        logger.warning("⚠️  MASCARAMENTO DESABILITADO!")
        logger.warning("Dados sensíveis (passwords) serão salvos em texto claro!")
        logger.warning("Use apenas para debugging em ambiente seguro.")
        logger.warning("=" * 60)
    
    # Gera run ID e cria diretórios
    run_id = generate_run_id()
    dirs = create_run_dirs(config.artifacts_dir, run_id)
    
    # Configura logging para arquivo
    log_path = dirs["logs"] / "session.log"
    setup_file_logging(log_path)
    
    started_at = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"Run ID: {run_id}")
    logger.info(f"URL: {url}")
    logger.info(f"Modo: {args.mode}")
    logger.info(f"Headless: {args.headless}")
    logger.info(f"Profile dir: {args.profile_dir or '(nenhum)'}")
    logger.info(f"Run dir: {dirs['run']}")
    logger.info(f"Log: {log_path}")
    
    # Executa modo selecionado
    if args.mode == "snapshot":
        result = run_snapshot(
            url=url,
            dirs=dirs,
            run_id=run_id,
            headless=args.headless,
            profile_dir=args.profile_dir,
            mask_sensitive=mask_sensitive,
        )
    else:
        result = run_interact(
            url=url,
            dirs=dirs,
            run_id=run_id,
            headless=args.headless,
            profile_dir=args.profile_dir,
            mask_sensitive=mask_sensitive,
        )
    
    # Salva meta.json
    meta = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": started_at,
        "url": url,
        "mode": args.mode,
        "headless": args.headless if args.mode == "snapshot" else False,
        "profile_dir_used": args.profile_dir is not None,
        "mask_sensitive": mask_sensitive,
        "result": result,
    }
    
    meta_path = dirs["run"] / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Meta salvo: {meta_path}")
    
    if result.get("success"):
        elements = result.get('elements_count', 0)
        actions = result.get('actions_count', 0)
        pages = result.get('pages_count', 1)
        if args.mode == "interact":
            logger.info(f"✅ Coleta concluída! {elements} elementos, {actions} ações, {pages} páginas.")
        else:
            logger.info(f"✅ Coleta concluída! {elements} elementos extraídos.")
        close_file_logging()
        return 0
    else:
        logger.error(f"❌ Coleta falhou: {result.get('error', 'erro desconhecido')}")
        close_file_logging()
        return 1


if __name__ == "__main__":
    sys.exit(main())
