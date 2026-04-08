from functools import lru_cache

try:
    import re2 as _regex  # type: ignore[reportMissingImports]
except ImportError:
    import re as _regex

__version__ = "1.0.0"
__all__ = ["is_crawler", "__version__"]

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


@lru_cache(maxsize=2048)
def is_crawler(user_agent: str) -> bool:
    """Return True if the user agent string looks like a crawler."""
    return bool(
        _match_bot_signal(user_agent)
        or not _match_browser_sign(user_agent)
        or _match_bare_compat(user_agent)
        or _match_known_tool(user_agent)
    )
