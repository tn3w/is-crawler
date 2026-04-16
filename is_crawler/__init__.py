from __future__ import annotations

import json
import re
import sys
import types
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

__version__ = "1.3.1"
__all__ = [
    "is_crawler",
    "crawler_name",
    "crawler_version",
    "crawler_url",
    "crawler_signals",
    "crawler_info",
    "crawler_has_tag",
    "CrawlerInfo",
    "__version__",
]

_CACHE = 32768
_CHUNK = 48


class CrawlerInfo(NamedTuple):
    url: str
    description: str
    tags: tuple[str, ...]


_BOT_SIGNAL = (
    r"bot\b|crawl|spider|scrape|fetch(?![\w]*api)"
    r"|scan\b|index(?:er|ing)|preview|slurp|archiv|headless"
    r"|\+https?://|@[\w.-]+\.\w{2,}\b"
)
_KNOWN_TOOL = (
    r"lighthouse|playwright|selenium|wget[\s/]"
    r"|nikto|sqlmap|nmap\b|pingdom|httrack"
    r"|google[\s-](?:favicon|ads|safety|extended)"
    r"|\bby\s+\S+\.(?:com|org|net)\b"
    r"|^[\w.-]+\.(?:com|net|org|io|ai)[/\s]"
    r"|;\s*\w+-agent[);]"
)
_URL_IN_UA = r"(?:^|[+;]|\s-\s)https?://[^\s);,]+"
_BROWSER = (
    r"mozilla/|webkit|gecko|trident|presto|khtml"
    r"|opera[\s/]|links\s|lynx/|\((?:windows|macintosh|x11|linux)"
)

_I = re.IGNORECASE
_search_bot_signal = re.compile(_BOT_SIGNAL, _I).search
_search_known_tool = re.compile(_KNOWN_TOOL, _I).search
_search_url = re.compile(_URL_IN_UA).search
_search_browser = re.compile(_BROWSER, _I).search
_search_positive = re.compile(f"{_BOT_SIGNAL}|{_KNOWN_TOOL}|{_URL_IN_UA}", _I).search

_search_compat = re.compile(r"(?i)\(compatible;[^)]*\)").search
_reject_compat = re.compile(r"(?i)windows|mac|linux|msie|konqueror").search
_extract_url = re.compile(r"https?://[^\s);,]+").search

_search_compat_name = re.compile(
    r"(?i)\(compatible;\s*([A-Za-z][\w.-]*)(?:/[\w.-]+)?"
).search
_search_compat_version = re.compile(
    r"(?i)\(compatible;\s*[A-Za-z][\w.-]*/([\w.-]+)"
).search
_search_prefix_name = re.compile(
    r"^([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?(?:\s|$| - )"
).search
_find_name = re.compile(r"([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?").findall
_search_token_version = re.compile(r"/([\w.-]+)").search
_sub_comments = re.compile(r"\([^)]*\)").sub
_sub_browser_bits = re.compile(
    r"\b(?:Mozilla/\S+|AppleWebKit/\S+|KHTML,?|like|Gecko"
    r"|Chrome/\S+|Chromium/\S+|Safari/\S+|Version/\S+"
    r"|Firefox/\S+|Ubuntu|Mobile)\b"
).sub

_BROWSER_TOKENS = frozenset(
    {
        "Mozilla",
        "AppleWebKit",
        "Gecko",
        "Chrome",
        "Chromium",
        "Safari",
        "Version",
        "Firefox",
        "Ubuntu",
        "Mobile",
    }
)


def _bare_compat(user_agent: str):
    match = _search_compat(user_agent)
    if match and not _reject_compat(match.group(0)):
        return match
    return None


_CHECKS = (
    ("bot_signal", _search_bot_signal),
    ("no_browser_signature", lambda ua: not _search_browser(ua)),
    ("bare_compatible", _bare_compat),
    ("known_tool", _search_known_tool),
    ("url_in_ua", _search_url),
)


@lru_cache(maxsize=_CACHE)
def crawler_signals(user_agent: str) -> list[str]:
    return [name for name, check in _CHECKS if check(user_agent)]


@lru_cache(maxsize=_CACHE)
def is_crawler(user_agent: str) -> bool:
    if _search_positive(user_agent):
        return True
    if not _search_browser(user_agent):
        return True
    return _bare_compat(user_agent) is not None


_CHUNKS: list[list] | None = None


def _ensure_db():
    global _CHUNKS
    if _CHUNKS is not None:
        return

    path = Path(__file__).parent / "crawler-user-agents.json"
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)

    _CHUNKS = [[rows[i : i + _CHUNK], None, None] for i in range(0, len(rows), _CHUNK)]


def _chunk_match(chunk, user_agent):
    rows, combined, entries = chunk

    if combined is None:
        combined = re.compile("|".join(f"(?:{p})" for p, *_ in rows))
        chunk[1] = combined

    if not combined.search(user_agent):
        return None

    if entries is None:
        entries = [(re.compile(p), CrawlerInfo(u, d, tuple(t))) for p, u, d, t in rows]
        chunk[2] = entries
    for pattern, info in entries:
        if pattern.search(user_agent):
            return info
    return None  # pragma: no cover


@lru_cache(maxsize=_CACHE)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    if not is_crawler(user_agent):
        return None

    _ensure_db()
    for chunk in _CHUNKS:  # type: ignore[union-attr]
        info = _chunk_match(chunk, user_agent)
        if info is not None:
            return info
    return None  # pragma: no cover


def crawler_has_tag(user_agent: str, tags: str | list[str]) -> bool:
    info = crawler_info(user_agent)
    if not info:
        return False

    wanted = {tags} if isinstance(tags, str) else set(tags)
    return bool(wanted & set(info.tags))


@lru_cache(maxsize=_CACHE)
def crawler_name(user_agent: str) -> str | None:
    match = _search_compat_name(user_agent)
    if match:
        return match.group(1)

    if not user_agent.startswith("Mozilla/5.0"):
        match = _search_prefix_name(user_agent)
        if match:
            return match.group(1)
        parts = user_agent.split()
        return parts[0].split("/", 1)[0] if parts else None

    cleaned = _sub_browser_bits(" ", _sub_comments(" ", user_agent))
    names = _find_name(cleaned)
    return names[-1] if names else None


@lru_cache(maxsize=_CACHE)
def crawler_version(user_agent: str) -> str | None:
    if not user_agent.startswith("Mozilla/5.0"):
        parts = (user_agent.split() or [""])[0].split("/", 1)
        return parts[1] if len(parts) > 1 else None

    match = _search_compat_version(user_agent)
    if match:
        return match.group(1)

    for token in user_agent.replace("(", " ").replace(")", " ").split():
        if "://" in token:
            continue
        name = token.split("/", 1)[0]
        if name in _BROWSER_TOKENS:
            continue
        match = _search_token_version(token[len(name) :])
        if match:
            return match.group(1)

    return None


@lru_cache(maxsize=_CACHE)
def crawler_url(user_agent: str) -> str | None:
    if not _search_url(user_agent):
        return None

    match = _extract_url(user_agent)
    return match.group(0) if match else None


class _CallableModule(types.ModuleType):
    def __call__(self, user_agent: str) -> bool:
        return is_crawler(user_agent)


sys.modules[__name__].__class__ = _CallableModule
