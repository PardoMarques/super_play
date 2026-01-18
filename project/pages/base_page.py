# super_play/project/pages/base_page.py
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, Union

from playwright.sync_api import Locator, Page, Response, expect

from project.core.pw_utils import RetryPolicy, clamp_timeout_ms, now_ts_compact, run_with_retry

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BasePageConfig:
    base_url: str = ""
    default_timeout_ms: int = 15_000
    navigation_timeout_ms: int = 25_000
    artifact_dir: str = "artifacts/runs"
    # PT: política padrão para navegação (páginas “estranhamente” instáveis)
    # EN: default policy for navigation (pages that are "strangely" unstable)
    nav_retry_policy: RetryPolicy = RetryPolicy(attempts=3, base_delay_s=0.6, backoff=1.9, max_delay_s=6.0)
    # PT: política padrão para ações UI (click/fill/etc.)
    # EN: default policy for UI actions (click/fill/etc.)
    action_retry_policy: RetryPolicy = RetryPolicy(attempts=2, base_delay_s=0.25, backoff=1.6, max_delay_s=2.5)


LocatorLike = Union[Locator, str]


class BasePage:
    """
    PT: BasePage mestra para QA/RPA.
    Objetivo: padronizar navegação, ações, asserts e artefatos com tolerância a instabilidade.
    EN: Master BasePage for QA/RPA.
    Goal: standardize navigation, actions, asserts and artifacts with instability tolerance.
    """

    def __init__(self, page: Page, config: Optional[BasePageConfig] = None) -> None:
        self.page = page
        self.config = config or BasePageConfig()

        # PT: padroniza timeouts no Playwright (reduz ruído e "timeouts aleatórios")
        # EN: standardize timeouts in Playwright (reduces noise and "random timeouts")
        self.page.set_default_timeout(self.config.default_timeout_ms)
        self.page.set_default_navigation_timeout(self.config.navigation_timeout_ms)

        # PT: garante pasta de artefatos
        # EN: ensure artifacts folder
        os.makedirs(self.config.artifact_dir, exist_ok=True)

    # ---------------------------
    # Helpers (locators / artifacts)
    # ---------------------------

    def L(self, locator_or_selector: LocatorLike) -> Locator:
        """
        PT: Resolve um Locator a partir de Locator ou string.
        EN: Resolves a Locator from Locator or string.
        """
        if isinstance(locator_or_selector, Locator):
            return locator_or_selector
        return self.page.locator(locator_or_selector)

    def _artifact_path(self, name: str, ext: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name).strip("_")
        filename = f"{now_ts_compact()}__{safe}.{ext.lstrip('.')}"
        return os.path.join(self.config.artifact_dir, filename)

    def screenshot(self, name: str = "screenshot", full_page: bool = True) -> str:
        path = self._artifact_path(name, "png")
        try:
            self.page.screenshot(path=path, full_page=full_page)
        except Exception as e:
            log.warning("Failed to generate screenshot (%s): %s", path, e)
        return path

    def dump_html(self, name: str = "page") -> str:
        path = self._artifact_path(name, "html")
        try:
            html = self.page.content()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            log.warning("Failed to save HTML (%s): %s", path, e)
        return path

    def _on_fail_artifacts(self, action_name: str) -> None:
        # PT: artefatos mínimos, útil em QA e RPA
        # EN: minimal artifacts, useful in QA and RPA
        self.screenshot(f"FAIL__{action_name}")
        self.dump_html(f"FAIL__{action_name}")

    # ---------------------------
    # EN: Resilient navigation ("classic" retry)
    # ---------------------------

    def goto(
        self,
        path_or_url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout_ms: Optional[int] = None,
        ensure_ready: bool = True,
        ready_state: str = "complete",
        policy: Optional[RetryPolicy] = None,
    ) -> Optional[Response]:
        """
        PT: Navegação resiliente: útil para sites que “precisam de retry” para carregar.
        - wait_until: domcontentloaded|load|networkidle (networkidle pode travar em websockets)
        - ensure_ready: valida readyState e um loadState adicional
        - ready_state: 'interactive' ou 'complete'
        EN: Resilient navigation: useful for sites that "need retry" to load.
        - wait_until: domcontentloaded|load|networkidle (networkidle may hang on websockets)
        - ensure_ready: validates readyState and an additional loadState
        - ready_state: 'interactive' or 'complete'
        """
        url = self._resolve_url(path_or_url)
        nav_timeout = clamp_timeout_ms(timeout_ms, self.config.navigation_timeout_ms)
        pol = policy or self.config.nav_retry_policy

        def _do_goto() -> Optional[Response]:
            resp = self.page.goto(url, wait_until=wait_until, timeout=nav_timeout)
            # PT: bad status is strong "symptom" of instability. Prefer retry.
            # EN: bad status is strong "symptom" of instability. Prefer retry.
            if resp is not None and resp.status >= 500:
                raise RuntimeError(f"HTTP {resp.status} opening {url}")
            if ensure_ready:
                self.ensure_page_ready(ready_state=ready_state, timeout_ms=nav_timeout)
            return resp

        return run_with_retry(
            _do_goto,
            action_name=f"goto({url})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"goto_{self._short(url)}"),
        )

    def reload(
        self,
        *,
        wait_until: str = "domcontentloaded",
        timeout_ms: Optional[int] = None,
        ensure_ready: bool = True,
        ready_state: str = "complete",
        policy: Optional[RetryPolicy] = None,
    ) -> Optional[Response]:
        nav_timeout = clamp_timeout_ms(timeout_ms, self.config.navigation_timeout_ms)
        pol = policy or self.config.nav_retry_policy

        def _do_reload() -> Optional[Response]:
            resp = self.page.reload(wait_until=wait_until, timeout=nav_timeout)
            if ensure_ready:
                self.ensure_page_ready(ready_state=ready_state, timeout_ms=nav_timeout)
            return resp

        return run_with_retry(
            _do_reload,
            action_name="reload()",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts("reload"),
        )

    def ensure_page_ready(self, *, ready_state: str = "complete", timeout_ms: Optional[int] = None) -> None:
        """
        PT: "Belt and suspenders" for unstable pages:
        - Ensures document.readyState >= target
        - And executes additional wait_for_load_state (domcontentloaded + load)
        EN: "Belt and suspenders" for unstable pages:
        - Ensures document.readyState >= target
        - And executes additional wait_for_load_state (domcontentloaded + load)
        """
        to_ms = clamp_timeout_ms(timeout_ms, self.config.navigation_timeout_ms)

        # PT: 1) readyState por JS (muitos sites dão loadState “ok” mas o DOM ainda muda)
        # EN: 1) readyState via JS (many sites give loadState "ok" but DOM still changes)
        def _ready_ok() -> bool:
            try:
                state = self.page.evaluate("() => document.readyState")
                if ready_state == "interactive":
                    return state in ("interactive", "complete")
                return state == "complete"
            except Exception:
                return False

        self._wait_bool(_ready_ok, timeout_ms=to_ms, interval_ms=150, name=f"document.readyState({ready_state})")

        # PT: 2) load states: domcontentloaded é o "mais seguro"; load pode falhar em SPAs, mas é útil como extra
        # EN: 2) load states: domcontentloaded is the "safest"; load may fail in SPAs, but is useful as extra
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=to_ms)
        except Exception:
            # PT: não explode: SPAs às vezes já passaram esse ponto
            # EN: don't explode: SPAs sometimes have already passed this point
            pass
        try:
            self.page.wait_for_load_state("load", timeout=min(to_ms, 10_000))
        except Exception:
            # PT: não explode: SPAs às vezes já passaram esse ponto
            # EN: don't explode: SPAs sometimes have already passed this point
            pass

    # ---------------------------
    # PT: Ações resilientes (click/fill/etc.) com retry e waits padronizados
    # EN: Resilient actions (click/fill/etc.) with retry and standardized waits
    # ---------------------------

    def click(
        self,
        locator_or_selector: LocatorLike,
        *,
        timeout_ms: Optional[int] = None,
        force: bool = False,
        policy: Optional[RetryPolicy] = None,
        description: str = "click",
    ) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        pol = policy or self.config.action_retry_policy
        loc = self.L(locator_or_selector)

        def _do() -> None:
            # PT: codificáveis: minimiza "flakiness" e reduz custo de debug
            # EN: codifiable waits: minimizes "flakiness" and reduces debug cost
            loc.wait_for(state="visible", timeout=to_ms)
            try:
                loc.scroll_into_view_if_needed(timeout=to_ms)
            except Exception:
                pass
            loc.click(timeout=to_ms, force=force)

        run_with_retry(
            _do,
            action_name=f"{description}({self._describe(loc)})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"click_{description}"),
        )

    def fill(
        self,
        locator_or_selector: LocatorLike,
        value: str,
        *,
        timeout_ms: Optional[int] = None,
        clear_first: bool = True,
        policy: Optional[RetryPolicy] = None,
        description: str = "fill",
    ) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        pol = policy or self.config.action_retry_policy
        loc = self.L(locator_or_selector)

        def _do() -> None:
            loc.wait_for(state="visible", timeout=to_ms)
            try:
                loc.scroll_into_view_if_needed(timeout=to_ms)
            except Exception:
                pass
            if clear_first:
                # PT: "fill" já faz replace, mas em alguns inputs (máscara/JS) é mais seguro limpar explicitamente
                # EN: "fill" already replaces, but in some inputs (mask/JS) it's safer to clear explicitly
                try:
                    loc.fill("", timeout=to_ms)
                except Exception:
                    pass
            loc.fill(value, timeout=to_ms)

        run_with_retry(
            _do,
            action_name=f"{description}({self._describe(loc)})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"fill_{description}"),
        )

    def press(
        self,
        locator_or_selector: LocatorLike,
        key: str,
        *,
        timeout_ms: Optional[int] = None,
        policy: Optional[RetryPolicy] = None,
        description: str = "press",
    ) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        pol = policy or self.config.action_retry_policy
        loc = self.L(locator_or_selector)

        def _do() -> None:
            loc.wait_for(state="visible", timeout=to_ms)
            loc.press(key, timeout=to_ms)

        run_with_retry(
            _do,
            action_name=f"{description}({self._describe(loc)} -> {key})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"press_{description}"),
        )

    def select_option(
        self,
        locator_or_selector: LocatorLike,
        *,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout_ms: Optional[int] = None,
        policy: Optional[RetryPolicy] = None,
        description: str = "select",
    ) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        pol = policy or self.config.action_retry_policy
        loc = self.L(locator_or_selector)

        def _do() -> None:
            loc.wait_for(state="visible", timeout=to_ms)
            payload: dict[str, Any] = {}
            if value is not None:
                payload["value"] = value
            if label is not None:
                payload["label"] = label
            if index is not None:
                payload["index"] = index
            if not payload:
                raise ValueError("Provide at least one of value/label/index")
            loc.select_option(timeout=to_ms, **payload)

        run_with_retry(
            _do,
            action_name=f"{description}({self._describe(loc)})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"select_{description}"),
        )

    def check(
        self,
        locator_or_selector: LocatorLike,
        *,
        checked: bool = True,
        timeout_ms: Optional[int] = None,
        policy: Optional[RetryPolicy] = None,
        description: str = "check",
    ) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        pol = policy or self.config.action_retry_policy
        loc = self.L(locator_or_selector)

        def _do() -> None:
            loc.wait_for(state="visible", timeout=to_ms)
            if checked:
                loc.check(timeout=to_ms)
            else:
                loc.uncheck(timeout=to_ms)

        run_with_retry(
            _do,
            action_name=f"{description}({self._describe(loc)} -> {checked})",
            policy=pol,
            on_fail=lambda e: self._on_fail_artifacts(f"check_{description}"),
        )

    # ---------------------------
    # PT: Asserts (codificáveis; Playwright já tem auto-wait)
    # EN: Asserts (codifiable; Playwright already has auto-wait)
    # ---------------------------

    def expect_visible(self, locator_or_selector: LocatorLike, *, timeout_ms: Optional[int] = None) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        loc = self.L(locator_or_selector)
        expect(loc).to_be_visible(timeout=to_ms)

    def expect_text(self, locator_or_selector: LocatorLike, text: str, *, timeout_ms: Optional[int] = None) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        loc = self.L(locator_or_selector)
        expect(loc).to_have_text(text, timeout=to_ms)

    def expect_url_contains(self, fragment: str, *, timeout_ms: Optional[int] = None) -> None:
        to_ms = clamp_timeout_ms(timeout_ms, self.config.default_timeout_ms)
        expect(self.page).to_have_url(lambda url: fragment in url, timeout=to_ms)

    # ---------------------------
    # PT: Internos
    # EN: Internals
    # ---------------------------

    def _resolve_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        base = (self.config.base_url or "").rstrip("/")
        path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
        return f"{base}{path}" if base else path

    def _short(self, s: str, max_len: int = 70) -> str:
        return s if len(s) <= max_len else (s[:max_len] + "_etc")

    def _describe(self, loc: Locator) -> str:
        # PT: Locator.__str__ é usualmente útil para logs
        # EN: Locator.__str__ is usually useful for logs
        try:
            return str(loc)
        except Exception:
            return "Locator(?)"

    def _wait_bool(
        self,
        predicate,
        *,
        timeout_ms: int,
        interval_ms: int = 200,
        name: str = "condition",
    ) -> None:
        import time

        start = time.time()
        deadline = start + (timeout_ms / 1000.0)

        last_exc: Optional[Exception] = None
        while time.time() < deadline:
            try:
                if predicate():
                    return
            except Exception as e:
                last_exc = e
            time.sleep(max(0.01, interval_ms / 1000.0))

        msg = f"Timeout waiting for {name} in {timeout_ms}ms"
        if last_exc:
            msg += f" (last error: {last_exc})"
        raise TimeoutError(msg)
