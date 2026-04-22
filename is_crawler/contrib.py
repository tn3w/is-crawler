from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from . import crawler_has_tag, crawler_name, is_crawler
from .ip import verify_crawler_ip

__all__ = [
    "CrawlerMiddlewareResult",
    "WSGICrawlerMiddleware",
    "ASGICrawlerMiddleware",
]

_HEADERS = [(b"content-type", b"text/plain; charset=utf-8")]


@dataclass(frozen=True)
class CrawlerMiddlewareResult:
    user_agent: str
    ip: str | None
    is_crawler: bool
    name: str | None
    verified: bool


def _blocked(
    user_agent: str,
    ip: str | None,
    verify_ip: bool,
) -> CrawlerMiddlewareResult:
    detected = is_crawler(user_agent)
    verified = False
    if verify_ip and detected and ip:
        verified = verify_crawler_ip(user_agent, ip)

    name = crawler_name(user_agent) if detected else None
    return CrawlerMiddlewareResult(
        user_agent=user_agent,
        ip=ip,
        is_crawler=detected,
        name=name,
        verified=bool(verified),
    )


def _should_block(result: CrawlerMiddlewareResult, tags: tuple[str, ...]) -> bool:
    if not result.is_crawler:
        return False
    if not tags:
        return True
    return crawler_has_tag(result.user_agent, tags)


def _to_tags(tags: str | Iterable[str] | None) -> tuple[str, ...]:
    if tags is None:
        return ()
    if isinstance(tags, str):
        return (tags,)
    return tuple(tags)


def _first_forwarded_ip(value: str | None) -> str | None:
    if not value:
        return None
    ip = value.split(",", 1)[0].strip()
    return ip or None


def _wsgi_ip(environ: dict[str, Any], trust_forwarded: bool) -> str | None:
    if trust_forwarded:
        ip = _first_forwarded_ip(environ.get("HTTP_X_FORWARDED_FOR"))
        if ip:
            return ip
    return environ.get("REMOTE_ADDR") or None


def _scope_header(scope: dict[str, Any], name: bytes) -> str:
    headers = scope.get("headers") or ()
    target = name.lower()
    for key, value in headers:
        if key.lower() == target:
            return value.decode("latin1")
    return ""


def _scope_ip(scope: dict[str, Any], trust_forwarded: bool) -> str | None:
    if trust_forwarded:
        ip = _first_forwarded_ip(_scope_header(scope, b"x-forwarded-for"))
        if ip:
            return ip

    client = scope.get("client")
    if not client:
        return None
    return client[0]


class WSGICrawlerMiddleware:
    def __init__(
        self,
        app: Callable[..., Any],
        *,
        block: bool = False,
        block_tags: str | Iterable[str] | None = None,
        verify_ip: bool = False,
        trust_forwarded: bool = False,
        environ_key: str = "is_crawler",
        status: str = "403 Forbidden",
        body: bytes = b"Forbidden",
    ) -> None:
        self.app = app
        self.block = block
        self.block_tags = _to_tags(block_tags)
        self.verify_ip = verify_ip
        self.trust_forwarded = trust_forwarded
        self.environ_key = environ_key
        self.status = status
        self.body = body

    def __call__(
        self,
        environ: dict[str, Any],
        start_response: Callable[[str, list[tuple[str, str]]], Any],
    ) -> Any:
        user_agent = environ.get("HTTP_USER_AGENT", "")
        ip = _wsgi_ip(environ, self.trust_forwarded)
        result = _blocked(user_agent, ip, self.verify_ip)
        environ[self.environ_key] = result

        if self.block and _should_block(result, self.block_tags):
            start_response(
                self.status,
                [("Content-Type", "text/plain; charset=utf-8")],
            )
            return [self.body]

        return self.app(environ, start_response)


class ASGICrawlerMiddleware:
    def __init__(
        self,
        app: Callable[..., Any],
        *,
        block: bool = False,
        block_tags: str | Iterable[str] | None = None,
        verify_ip: bool = False,
        trust_forwarded: bool = False,
        scope_key: str = "is_crawler",
        state_key: str = "crawler",
        status_code: int = 403,
        body: bytes = b"Forbidden",
    ) -> None:
        self.app = app
        self.block = block
        self.block_tags = _to_tags(block_tags)
        self.verify_ip = verify_ip
        self.trust_forwarded = trust_forwarded
        self.scope_key = scope_key
        self.state_key = state_key
        self.status_code = status_code
        self.body = body

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        user_agent = _scope_header(scope, b"user-agent")
        ip = _scope_ip(scope, self.trust_forwarded)
        result = _blocked(user_agent, ip, self.verify_ip)
        scope[self.scope_key] = result

        state = scope.setdefault("state", {})
        if isinstance(state, dict):
            state[self.state_key] = result

        if self.block and _should_block(result, self.block_tags):
            await send(
                {
                    "type": "http.response.start",
                    "status": self.status_code,
                    "headers": _HEADERS,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": self.body,
                }
            )
            return

        await self.app(scope, receive, send)
