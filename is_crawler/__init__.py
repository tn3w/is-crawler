from __future__ import annotations

from csv import reader as _csv_reader
from functools import lru_cache
from pathlib import Path as _Path
from typing import NamedTuple

try:
    import re2 as _regex  # type: ignore[reportMissingImports]
except ImportError:
    import re as _regex

__version__ = "1.0.6"
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
    tags: list[str]


@lru_cache(maxsize=1)
def _load_crawler_db() -> tuple:
    path = _Path(__file__).parent / "crawler-user-agents.csv"
    with path.open(encoding="utf-8") as f:
        rows = list(_csv_reader(f))[1:]
    return tuple(
        (_regex.compile(p), CrawlerInfo(u, d, t.split(";") if t else []))
        for p, u, d, t in rows
    )


_match_bot_signal = _regex.compile(
    r"(?i)bot\b|crawl|spider|scrape|fetch|scan\b|index"
    r"|preview|slurp|archiv|headless"
    r"|\+https?://|@[\w.-]+\.\w{2,}\b"
).search

_match_browser_sign = _regex.compile(
    r"(?i)mozilla/|webkit|gecko|trident|presto|khtml"
    r"|opera[\s/]|links\s|lynx/"
    r"|\((?:windows|macintosh|x11|linux)"
).search

_match_bare_compat = _regex.compile(
    r"(?i)\(compatible;" r"(?![^)]*(?:windows|mac|linux|msie|konqueror))" r"[^)]*\)"
).search

_match_url = _regex.compile(r"(?:^|[+;]|\s-\s)https?://[^\s);,]+").search
_extract_url = _regex.compile(r"https?://[^\s);,]+").search

_match_known_tool = _regex.compile(
    r"(?i)lighthouse|playwright|selenium|wget[\s/]"
    r"|nikto|sqlmap|nmap\b|pingdom|httrack"
    r"|google[\s-](?:favicon|ads|safety|extended)"
    r"|\bby\s+\S+\.(?:com|org|net)\b"
    r"|^[\w.-]+\.(?:com|net|org|io|ai)[/\s]"
    r"|;\s*\w+-agent[);]"
).search

_search_compatible_name = _regex.compile(
    r"(?i)\(compatible;\s*([A-Za-z][\w.-]*)(?:/[\w.-]+)?"
).search
_search_compatible_version = _regex.compile(
    r"(?i)\(compatible;\s*[A-Za-z][\w.-]*/([\w.-]+)"
).search
_search_prefix_name = _regex.compile(
    r"^([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?=(?:/[\w.-]+)?(?:\s|$| - ))"
).search
_find_name = _regex.compile(r"([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?").findall
_search_token_version = _regex.compile(r"/([\w.-]+)").search
_strip_comments = _regex.compile(r"\([^)]*\)").sub
_strip_browser_bits = _regex.compile(
    r"\b(?:Mozilla/\S+|AppleWebKit/\S+|KHTML,?|like|Gecko|"
    r"Chrome/\S+|Chromium/\S+|Safari/\S+|Version/\S+|Firefox/\S+|"
    r"Ubuntu|Mobile)\b"
).sub
_KNOWN_VERSION_TOKENS = frozenset(
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


@lru_cache(maxsize=2048)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    """Return url, description, and tags for the first matching crawler pattern."""
    for pattern, info in _load_crawler_db():
        if pattern.search(user_agent):
            return info
    return None


def crawler_has_tag(user_agent: str, tags: str | list[str]) -> bool:
    """Return True if the crawler matches any of the given tags."""
    info = crawler_info(user_agent)
    if info is None:
        return False
    check = {tags} if isinstance(tags, str) else set(tags)
    return bool(check & set(info.tags))


_CHECKS = (
    ("bot_signal", _match_bot_signal),
    ("no_browser_signature", lambda ua: not _match_browser_sign(ua)),
    ("bare_compatible", _match_bare_compat),
    ("known_tool", _match_known_tool),
    ("url_in_ua", _match_url),
)


@lru_cache(maxsize=2048)
def crawler_signals(user_agent: str) -> list[str]:
    """Return list of matched pattern names, or empty list for real browsers."""
    return [name for name, check in _CHECKS if check(user_agent)]


@lru_cache(maxsize=2048)
def crawler_name(user_agent: str) -> str | None:
    """Return the crawler product name when one can be picked out of the UA."""
    match = _search_compatible_name(user_agent)
    if match:
        return match.group(1)

    if not user_agent.startswith("Mozilla/5.0"):
        match = _search_prefix_name(user_agent)
        if match:
            return match.group(1)
        parts = user_agent.split()
        return parts[0].split("/", 1)[0] if parts else None

    names = _find_name(_strip_browser_bits(" ", _strip_comments(" ", user_agent)))
    return names[-1] if names else None


@lru_cache(maxsize=2048)
def crawler_version(user_agent: str) -> str | None:
    """Return the crawler version when one can be picked out of the UA."""
    if not user_agent.startswith("Mozilla/5.0"):
        parts = (user_agent.split() or [""])[0].split("/", 1)
        return parts[1] if len(parts) > 1 else None

    match = _search_compatible_version(user_agent)
    if match:
        return match.group(1)

    for token in user_agent.replace("(", " ").replace(")", " ").split():
        name = token.split("/", 1)[0]
        if name not in _KNOWN_VERSION_TOKENS:
            match = _search_token_version(token[len(name) :])
            if match:
                return match.group(1)

    return None


@lru_cache(maxsize=2048)
def crawler_url(user_agent: str) -> str | None:
    """Return the first URL found in the user agent string, or None."""
    if not _match_url(user_agent):
        return None
    match = _extract_url(user_agent)
    return match.group(0) if match else None


@lru_cache(maxsize=2048)
def is_crawler(user_agent: str) -> bool:
    """Return True if the user agent string looks like a crawler."""
    return bool(
        _match_bot_signal(user_agent)
        or not _match_browser_sign(user_agent)
        or _match_bare_compat(user_agent)
        or _match_known_tool(user_agent)
        or _match_url(user_agent)
    )


import sys as _sys
import types as _types


class _CallableModule(_types.ModuleType):
    def __call__(self, user_agent: str) -> bool:
        return is_crawler(user_agent)


_self = _sys.modules[__name__]
_mod = _CallableModule(__name__, __doc__)
_mod.__dict__.update(
    {k: v for k, v in _self.__dict__.items() if not k.startswith("_CallableModule")}
)
_sys.modules[__name__] = _mod
