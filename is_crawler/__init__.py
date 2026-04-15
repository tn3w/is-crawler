from __future__ import annotations

import json
import re
import sys
import types
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

__version__ = "1.3.0"
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


class CrawlerInfo(NamedTuple):
    url: str
    description: str
    tags: tuple[str, ...]


_ENTRIES: tuple[tuple[re.Pattern[str], CrawlerInfo], ...] | None = None
_COMBINED: re.Pattern[str] | None = None


def _ensure_db():
    global _ENTRIES, _COMBINED
    if _ENTRIES is not None:
        return

    path = Path(__file__).parent / "crawler-user-agents.json"
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)

    patterns = [p for p, *_ in rows]
    _COMBINED = re.compile("|".join(f"(?:{p})" for p in patterns))
    _ENTRIES = tuple(
        (re.compile(p), CrawlerInfo(u, d, tuple(t))) for p, u, d, t in rows
    )


_search_bot_signal = re.compile(
    r"(?i)bot\b|crawl|spider|scrape|fetch(?![\w]*api)"
    r"|scan\b|index(?:er|ing)"
    r"|preview|slurp|archiv|headless"
    r"|\+https?://|@[\w.-]+\.\w{2,}\b"
).search

_search_browser = re.compile(
    r"(?i)mozilla/|webkit|gecko|trident|presto|khtml"
    r"|opera[\s/]|links\s|lynx/"
    r"|\((?:windows|macintosh|x11|linux)"
).search

_search_compat = re.compile(r"(?i)\(compatible;[^)]*\)").search
_reject_compat = re.compile(r"(?i)windows|mac|linux|msie|konqueror").search

_search_url = re.compile(r"(?:^|[+;]|\s-\s)https?://[^\s);,]+").search
_extract_url = re.compile(r"https?://[^\s);,]+").search

_search_known_tool = re.compile(
    r"(?i)lighthouse|playwright|selenium|wget[\s/]"
    r"|nikto|sqlmap|nmap\b|pingdom|httrack"
    r"|google[\s-](?:favicon|ads|safety|extended)"
    r"|\bby\s+\S+\.(?:com|org|net)\b"
    r"|^[\w.-]+\.(?:com|net|org|io|ai)[/\s]"
    r"|;\s*\w+-agent[);]"
).search

_search_compat_name = re.compile(
    r"(?i)\(compatible;\s*([A-Za-z][\w.-]*)(?:/[\w.-]+)?"
).search
_search_compat_version = re.compile(
    r"(?i)\(compatible;\s*[A-Za-z][\w.-]*/([\w.-]+)"
).search
_search_prefix_name = re.compile(
    r"^([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?" r"(?:\s|$| - )"
).search
_find_name = re.compile(r"([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?").findall
_search_token_version = re.compile(r"/([\w.-]+)").search
_sub_comments = re.compile(r"\([^)]*\)").sub
_sub_browser_bits = re.compile(
    r"\b(?:Mozilla/\S+|AppleWebKit/\S+|KHTML,?|like|Gecko|"
    r"Chrome/\S+|Chromium/\S+|Safari/\S+|Version/\S+|"
    r"Firefox/\S+|Ubuntu|Mobile)\b"
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


def _match_bare_compat(user_agent: str):
    match = _search_compat(user_agent)
    if match and not _reject_compat(str(match.group(0))):
        return match
    return None


_CHECKS = (
    ("bot_signal", _search_bot_signal),
    ("no_browser_signature", lambda ua: not _search_browser(ua)),
    ("bare_compatible", _match_bare_compat),
    ("known_tool", _search_known_tool),
    ("url_in_ua", _search_url),
)


@lru_cache(maxsize=8192)
def crawler_signals(user_agent: str) -> list[str]:
    return [name for name, check in _CHECKS if check(user_agent)]


@lru_cache(maxsize=8192)
def is_crawler(user_agent: str) -> bool:
    return bool(crawler_signals(user_agent))


@lru_cache(maxsize=8192)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    _ensure_db()
    assert _COMBINED is not None and _ENTRIES is not None

    if not _COMBINED.search(user_agent):
        return None

    for pattern, info in _ENTRIES:
        if pattern.search(user_agent):
            return info

    return None  # pragma: no cover


def crawler_has_tag(user_agent: str, tags: str | list[str]) -> bool:
    info = crawler_info(user_agent)
    if not info:
        return False
    normalized = {tags} if isinstance(tags, str) else set(tags)
    return bool(normalized & set(info.tags))


@lru_cache(maxsize=8192)
def crawler_name(user_agent: str) -> str | None:
    match = _search_compat_name(user_agent)
    if match:
        return str(match.group(1))

    if not user_agent.startswith("Mozilla/5.0"):
        match = _search_prefix_name(user_agent)
        if match:
            return str(match.group(1))
        parts = user_agent.split()
        return parts[0].split("/", 1)[0] if parts else None

    cleaned = _sub_browser_bits(" ", _sub_comments(" ", user_agent))
    names = _find_name(cleaned)
    return names[-1] if names else None


@lru_cache(maxsize=8192)
def crawler_version(user_agent: str) -> str | None:
    if not user_agent.startswith("Mozilla/5.0"):
        parts = (user_agent.split() or [""])[0].split("/", 1)
        return parts[1] if len(parts) > 1 else None

    match = _search_compat_version(user_agent)
    if match:
        return str(match.group(1))

    for token in user_agent.replace("(", " ").replace(")", " ").split():
        if "://" in token:
            continue
        name = token.split("/", 1)[0]
        if name not in _BROWSER_TOKENS:
            match = _search_token_version(token[len(name) :])
            if match:
                return str(match.group(1))

    return None


@lru_cache(maxsize=8192)
def crawler_url(user_agent: str) -> str | None:
    if not _search_url(user_agent):
        return None
    match = _extract_url(user_agent)
    return str(match.group(0)) if match else None


class _CallableModule(types.ModuleType):
    def __call__(self, user_agent: str) -> bool:
        return is_crawler(user_agent)


sys.modules[__name__].__class__ = _CallableModule
