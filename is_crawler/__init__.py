from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from typing import NamedTuple

__version__ = version("is-crawler")
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
    r"bot\b|crawl|spider|scrape|fetch(?!\w*api)"
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


def _bare_compat(user_agent: str) -> bool:
    match = _search_compat(user_agent)
    return bool(match and not _reject_compat(match.group(0)))


_CHECKS = (
    ("bot_signal", lambda ua: bool(_search_bot_signal(ua))),
    ("no_browser_signature", lambda ua: not _search_browser(ua)),
    ("bare_compatible", _bare_compat),
    ("known_tool", lambda ua: bool(_search_known_tool(ua))),
    ("url_in_ua", lambda ua: bool(_search_url(ua))),
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
    return _bare_compat(user_agent)


@dataclass
class _Chunk:
    rows: list
    _combined: re.Pattern | None = field(default=None, init=False, repr=False)
    _entries: list | None = field(default=None, init=False, repr=False)

    def match(self, user_agent: str) -> CrawlerInfo | None:
        if self._combined is None:
            self._combined = re.compile("|".join(f"(?:{p})" for p, *_ in self.rows))

        if not self._combined.search(user_agent):
            return None

        if self._entries is None:
            self._entries = [
                (re.compile(p), CrawlerInfo(u, d, tuple(t))) for p, u, d, t in self.rows
            ]

        for pattern, info in self._entries:
            if pattern.search(user_agent):
                return info
        return None  # pragma: no cover


_chunks: list[_Chunk] | None = None


def _load_chunks() -> list[_Chunk]:
    global _chunks
    if _chunks is not None:
        return _chunks

    path = Path(__file__).parent / "crawler-user-agents.json"
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)

    _chunks = [_Chunk(rows[i : i + _CHUNK]) for i in range(0, len(rows), _CHUNK)]
    return _chunks


@lru_cache(maxsize=_CACHE)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    if not is_crawler(user_agent):
        return None

    for chunk in _load_chunks():
        info = chunk.match(user_agent)
        if info is not None:
            return info

    return None  # pragma: no cover


def crawler_has_tag(user_agent: str, tags: str | Iterable[str]) -> bool:
    info = crawler_info(user_agent)
    if not info:
        return False

    wanted = {tags} if isinstance(tags, str) else set(tags)
    return bool(wanted & set(info.tags))


def _name_non_mozilla(user_agent: str) -> str | None:
    match = _search_prefix_name(user_agent)
    if match:
        return match.group(1)

    parts = user_agent.split()
    return parts[0].split("/", 1)[0] if parts else None


@lru_cache(maxsize=_CACHE)
def crawler_name(user_agent: str) -> str | None:
    match = _search_compat_name(user_agent)
    if match:
        return match.group(1)

    if not user_agent.startswith("Mozilla/5.0"):
        return _name_non_mozilla(user_agent)

    cleaned = _sub_browser_bits(" ", _sub_comments(" ", user_agent))
    names = _find_name(cleaned)
    return names[-1] if names else None


def _version_non_mozilla(user_agent: str) -> str | None:
    parts = (user_agent.split() or [""])[0].split("/", 1)
    return parts[1] if len(parts) > 1 else None


def _version_mozilla(user_agent: str) -> str | None:
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
def crawler_version(user_agent: str) -> str | None:
    if not user_agent.startswith("Mozilla/5.0"):
        return _version_non_mozilla(user_agent)
    return _version_mozilla(user_agent)


@lru_cache(maxsize=_CACHE)
def crawler_url(user_agent: str) -> str | None:
    if not _search_url(user_agent):
        return None

    match = _extract_url(user_agent)
    return match.group(0) if match else None
