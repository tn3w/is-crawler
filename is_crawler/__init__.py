from functools import lru_cache

try:
    import re2 as _regex  # type: ignore[reportMissingImports]
except ImportError:
    import re as _regex

__version__ = "1.0.4"
__all__ = ["is_crawler", "crawler_name", "crawler_signals", "__version__"]

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
_search_prefix_name = _regex.compile(
    r"^([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?=(?:/[\w.-]+)?(?:\s|$| - ))"
).search
_find_name = _regex.compile(r"([A-Z][\w.-]*(?: [A-Z][\w.-]*)*)(?:/[\w.-]+)?").findall
_strip_comments = _regex.compile(r"\([^)]*\)").sub
_strip_browser_bits = _regex.compile(
    r"\b(?:Mozilla/\S+|AppleWebKit/\S+|KHTML,?|like|Gecko|"
    r"Chrome/\S+|Chromium/\S+|Safari/\S+|Version/\S+|Firefox/\S+|"
    r"Ubuntu|Mobile)\b"
).sub


_CHECKS = (
    ("bot_signal", _match_bot_signal),
    ("no_browser_signature", lambda ua: not _match_browser_sign(ua)),
    ("bare_compatible", _match_bare_compat),
    ("known_tool", _match_known_tool),
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
def is_crawler(user_agent: str) -> bool:
    """Return True if the user agent string looks like a crawler."""
    return bool(
        _match_bot_signal(user_agent)
        or not _match_browser_sign(user_agent)
        or _match_bare_compat(user_agent)
        or _match_known_tool(user_agent)
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
