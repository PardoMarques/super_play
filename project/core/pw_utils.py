# super_play/project/core/pw_utils.py
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, Type

try:
    # Playwright (sync)
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except Exception:  # pragma: no cover
    PlaywrightError = Exception  # type: ignore
    PlaywrightTimeoutError = TimeoutError  # type: ignore

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryPolicy:
    """
    Política genérica de retry para operações instáveis.
    - attempts: total de tentativas (>=1)
    - base_delay_s: atraso inicial
    - backoff: multiplicador exponencial
    - max_delay_s: teto do atraso
    - jitter_s: jitter uniforme [0, jitter_s]
    - retry_on: tipos de exceção que disparam retry
    - retry_if_message_contains: substrings que, se presentes na mensagem, disparam retry
    """
    attempts: int = 3
    base_delay_s: float = 0.35
    backoff: float = 1.8
    max_delay_s: float = 4.0
    jitter_s: float = 0.15
    retry_on: Tuple[Type[BaseException], ...] = (PlaywrightTimeoutError, PlaywrightError)
    retry_if_message_contains: Tuple[str, ...] = (
        # falhas comuns/transientes (rede, navegação, alvo sumindo, etc.)
        "net::ERR_ABORTED",
        "net::ERR_CONNECTION_RESET",
        "net::ERR_CONNECTION_CLOSED",
        "net::ERR_NAME_NOT_RESOLVED",
        "net::ERR_INTERNET_DISCONNECTED",
        "Navigation failed",
        "Target closed",
        "Execution context was destroyed",
        "Protocol error",
        "Timeout",
        "has been closed",
        "page.goto",
    )
    # opcional: função custom para decidir retry
    retry_predicate: Optional[Callable[[BaseException], bool]] = None


def _sleep_backoff(attempt_index: int, policy: RetryPolicy) -> None:
    delay = policy.base_delay_s * (policy.backoff ** max(0, attempt_index - 1))
    delay = min(delay, policy.max_delay_s)
    delay += random.uniform(0, policy.jitter_s)
    time.sleep(max(0.0, delay))


def is_transient_error(exc: BaseException, policy: RetryPolicy) -> bool:
    if policy.retry_predicate:
        try:
            return bool(policy.retry_predicate(exc))
        except Exception:
            # se o predicate falhar, não bloqueie retries básicos
            pass

    msg = str(exc) or ""
    msg_l = msg.lower()

    for s in policy.retry_if_message_contains:
        if s.lower() in msg_l:
            return True

    return isinstance(exc, policy.retry_on)


def run_with_retry(
    fn: Callable[[], Any],
    *,
    action_name: str = "operation",
    policy: RetryPolicy = RetryPolicy(),
    on_retry: Optional[Callable[[int, BaseException], None]] = None,
    on_fail: Optional[Callable[[BaseException], None]] = None,
) -> Any:
    """
    Executa fn() com retry para falhas transientes.

    - on_retry(attempt, exc): chamado antes de dormir e repetir
    - on_fail(exc): chamado antes de levantar a exceção final
    """
    if policy.attempts < 1:
        raise ValueError("RetryPolicy.attempts deve ser >= 1")

    last_exc: Optional[BaseException] = None

    for attempt in range(1, policy.attempts + 1):
        try:
            return fn()
        except BaseException as exc:
            last_exc = exc
            should_retry = (attempt < policy.attempts) and is_transient_error(exc, policy)

            if not should_retry:
                if on_fail:
                    try:
                        on_fail(exc)
                    except Exception:
                        pass
                raise

            log.warning(
                "[retry] %s falhou (tentativa %s/%s): %s",
                action_name, attempt, policy.attempts, exc,
            )
            if on_retry:
                try:
                    on_retry(attempt, exc)
                except Exception:
                    pass

            _sleep_backoff(attempt, policy)

    # teoricamente não chega aqui
    if last_exc:
        raise last_exc
    raise RuntimeError(f"{action_name} falhou sem exceção (estado inválido)")


def clamp_timeout_ms(timeout_ms: Optional[int], default_ms: int) -> int:
    if timeout_ms is None:
        return int(default_ms)
    return max(1, int(timeout_ms))


def now_ts_compact() -> str:
    # timestamp compacto para nomes de arquivo
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())
