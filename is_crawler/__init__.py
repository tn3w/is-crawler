from __future__ import annotations

import json
import re as _re
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
    "is_search_engine",
    "is_ai_crawler",
    "is_seo",
    "is_social_preview",
    "is_advertising",
    "is_archiver",
    "is_feed_reader",
    "is_monitoring",
    "is_scanner",
    "is_academic",
    "is_http_library",
    "is_browser_automation",
    "is_good_crawler",
    "is_bad_crawler",
    "iter_crawlers",
    "robots_agents_for_tags",
    "build_robots_txt",
    "CrawlerInfo",
    "__version__",
]

_CACHE = 32768
_CHUNK = 48

_BOT_KEYWORDS = (
    "crawl",
    "spider",
    "scrape",
    "preview",
    "slurp",
    "archiv",
    "headless",
    "indexer",
    "indexing",
)
_TOOLS = (
    "lighthouse",
    "playwright",
    "selenium",
    "nikto",
    "sqlmap",
    "pingdom",
    "httrack",
)
_GOOGLE_SUFFIXES = ("favicon", "ads", "safety", "extended")
_DOMAIN_TLDS = frozenset(("com", "net", "org", "io", "ai"))
_BROWSER_LITERALS = (
    "mozilla/",
    "webkit",
    "gecko",
    "trident",
    "presto",
    "khtml",
    "links ",
    "lynx/",
)
_OS_TOKENS = ("windows", "macintosh", "x11", "linux")
_COMPAT_REJECT = ("windows", "mac", "linux", "msie", "konqueror")
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
_URL_STOPS = frozenset(" );,")
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
)
_SKIP_TOKENS = _BROWSER_TOKENS | {"KHTML", "like"}

_SUSPICIOUS_LOW = (
    "bot",
    "crawl",
    "spider",
    "scan",
    "fetch",
    "wget",
    "scrape",
    "preview",
    "slurp",
    "archiv",
    "headless",
    "indexer",
    "indexing",
    "lighthouse",
    "playwright",
    "selenium",
    "nikto",
    "sqlmap",
    "pingdom",
    "httrack",
    "nmap",
    "google-",
    "google ",
    "by ",
    "-agent",
)


def _word_char(c: str) -> bool:
    return c.isalnum() or c == "_"


def _word_ends(s: str, end: int) -> bool:
    return end >= len(s) or not _word_char(s[end])


def _find_word(s: str, word: str) -> bool:
    i = 0
    while (i := s.find(word, i)) != -1:
        if _word_ends(s, i + len(word)):
            return True
        i += 1
    return False


def _fetch_not_api(s: str) -> bool:
    i = 0
    while (i := s.find("fetch", i)) != -1:
        j = i + 5
        while j < len(s) and _word_char(s[j]):
            j += 1
        if "api" not in s[i + 5 : j]:
            return True
        i += 1
    return False


def _email_like(ua: str) -> bool:
    i = 0
    while (i := ua.find("@", i)) != -1:
        j = i + 1
        while j < len(ua) and (ua[j].isalnum() or ua[j] in "_.-"):
            j += 1

        token = ua[i + 1 : j]
        if "." in token and i > 0:
            tld = token.rsplit(".", 1)[1]
            if len(tld) >= 2 and tld.isalpha():
                return True
        i += 1
    return False


def _bot_signal(ua: str) -> bool:
    low = ua.lower()

    if any(k in low for k in _BOT_KEYWORDS):
        return True
    if _find_word(low, "bot") or _find_word(low, "scan"):
        return True
    if "fetch" in low and _fetch_not_api(low):
        return True
    if "+http://" in ua or "+https://" in ua:
        return True

    return "@" in ua and _email_like(ua)


def _token_after(s: str, start: int, stops: str = " ();,") -> tuple[int, str]:
    j = start
    while j < len(s) and s[j] not in stops:
        j += 1
    return j, s[start:j]


def _domain_tld(token: str) -> bool:
    return "." in token and token.rsplit(".", 1)[1].lower() in _DOMAIN_TLDS


def _has_by_domain(low: str) -> bool:
    i = 0
    while (i := low.find("by ", i)) != -1:
        if i == 0 or not low[i - 1].isalnum():
            _, token = _token_after(low, i + 3)
            if _domain_tld(token):
                return True
        i += 1
    return False


def _leading_domain(ua: str) -> bool:
    end, token = _token_after(ua, 0, "/ ")
    return end < len(ua) and _domain_tld(token) and ua[end] in "/ "


def _semicolon_agent(low: str) -> bool:
    i = 0
    while (i := low.find(";", i)) != -1:
        j = i + 1
        while j < len(low) and low[j] == " ":
            j += 1

        k = j
        while k < len(low) and (low[k].isalnum() or low[k] == "-"):
            k += 1

        if low[j:k].endswith("-agent") and k < len(low) and low[k] in ");":
            return True
        i += 1
    return False


def _known_tool(ua: str) -> bool:
    low = ua.lower()

    if any(t in low for t in _TOOLS):
        return True
    if ("wget" in low and _find_word(low, "wget")) or (
        "nmap" in low and _find_word(low, "nmap")
    ):
        return True
    if "google" in low and any(
        f"google{sep}{suf}" in low for sep in " -" for suf in _GOOGLE_SUFFIXES
    ):
        return True
    if "by " in low and _has_by_domain(low):
        return True
    if _leading_domain(ua):
        return True
    return "-agent" in low and _semicolon_agent(low)


def _url_in_ua(ua: str) -> bool:
    for marker in ("http://", "https://"):
        i = 0
        while (i := ua.find(marker, i)) != -1:
            if i == 0 or ua[i - 1] in "+;" or (i >= 3 and ua[i - 3 : i] == " - "):
                return True
            i += 1
    return False


def _browser(ua: str) -> bool:
    low = ua.lower()

    if any(b in low for b in _BROWSER_LITERALS):
        return True
    if _find_word(low, "opera"):
        return True

    return any(f"({t}" in low for t in _OS_TOKENS)


def _bare_compat(ua: str) -> bool:
    low = ua.lower()
    i = 0
    while (i := low.find("(compatible;", i)) != -1:
        close = low.find(")", i)
        if close == -1:
            return False
        if not any(r in low[i : close + 1] for r in _COMPAT_REJECT):
            return True
        i = close
    return False


@lru_cache(maxsize=_CACHE)
def is_crawler(user_agent: str) -> bool:
    low = user_agent.lower()

    suspicious = (
        "bot" in low
        or "crawl" in low
        or "spider" in low
        or "scan" in low
        or "fetch" in low
        or "wget" in low
        or "scrape" in low
        or "preview" in low
        or "slurp" in low
        or "archiv" in low
        or "headless" in low
        or "index" in low
        or "lighthouse" in low
        or "playwright" in low
        or "selenium" in low
        or "nikto" in low
        or "sqlmap" in low
        or "pingdom" in low
        or "httrack" in low
        or "nmap" in low
        or "google" in low
        or "by " in low
        or "-agent" in low
        or "@" in user_agent
        or "http://" in user_agent
        or "https://" in user_agent
    )

    if not suspicious:
        if not user_agent.startswith("Mozilla/") and _leading_domain(user_agent):
            return True
        return not _browser(user_agent) or _bare_compat(user_agent)

    if _bot_signal(user_agent) or _known_tool(user_agent) or _url_in_ua(user_agent):
        return True
    return not _browser(user_agent) or _bare_compat(user_agent)


@lru_cache(maxsize=_CACHE)
def crawler_signals(user_agent: str) -> list[str]:
    checks = [
        ("bot_signal", _bot_signal(user_agent)),
        ("no_browser_signature", not _browser(user_agent)),
        ("bare_compatible", _bare_compat(user_agent)),
        ("known_tool", _known_tool(user_agent)),
        ("url_in_ua", _url_in_ua(user_agent)),
    ]
    return [name for name, ok in checks if ok]


class CrawlerInfo(NamedTuple):
    url: str
    description: str
    tags: tuple[str, ...]


@dataclass
class _Chunk:
    rows: list
    _combined: _re.Pattern | None = field(default=None, init=False, repr=False)
    _entries: list | None = field(default=None, init=False, repr=False)

    def match(self, user_agent: str) -> CrawlerInfo | None:
        if self._combined is None:
            self._combined = _re.compile("|".join(f"(?:{p})" for p, *_ in self.rows))

        if not self._combined.search(user_agent):
            return None

        if self._entries is None:
            self._entries = [
                (_re.compile(p), CrawlerInfo(u, d, tuple(t)))
                for p, u, d, t in self.rows
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


_GOOD_TAGS = frozenset(
    {"search-engine", "social-preview", "feed-reader", "archiver", "academic"}
)
_BAD_TAGS = frozenset(
    {"ai-crawler", "scanner", "http-library", "browser-automation", "seo"}
)


def is_search_engine(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "search-engine")


def is_ai_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "ai-crawler")


def is_seo(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "seo")


def is_social_preview(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "social-preview")


def is_advertising(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "advertising")


def is_archiver(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "archiver")


def is_feed_reader(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "feed-reader")


def is_monitoring(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "monitoring")


def is_scanner(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "scanner")


def is_academic(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "academic")


def is_http_library(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "http-library")


def is_browser_automation(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "browser-automation")


def is_good_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, _GOOD_TAGS)


def is_bad_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, _BAD_TAGS)


_ROBOTS_CHARCLASS = _re.compile(r"\[([^\]]+)\]")
_ROBOTS_ESCAPE = _re.compile(r"\\(.)")
_ROBOTS_META = _re.compile(r"[(|$?*+]")


def _robots_name(pattern: str) -> str | None:
    name = _ROBOTS_CHARCLASS.sub(lambda m: m.group(1)[0], pattern)
    name = _ROBOTS_ESCAPE.sub(r"\1", name).lstrip("^")
    name = _ROBOTS_META.split(name)[0].strip("/-. \t")
    if not name or "://" in name or "/" in name:
        return None
    return name


def iter_crawlers() -> Iterable[tuple[CrawlerInfo, str]]:
    for chunk in _load_chunks():
        for pattern, url, description, tags in chunk.rows:
            name = _robots_name(pattern)
            if name:
                yield CrawlerInfo(url, description, tuple(tags or ())), name


def robots_agents_for_tags(tags: str | Iterable[str]) -> list[str]:
    wanted = {tags} if isinstance(tags, str) else set(tags)
    seen: set[str] = set()
    for info, name in iter_crawlers():
        if wanted & set(info.tags) and name not in seen:
            seen.add(name)
    return sorted(seen)


def build_robots_txt(
    disallow: str | Iterable[str] = (),
    allow: str | Iterable[str] = (),
    path: str = "/",
) -> str:
    disallow_tags = {disallow} if isinstance(disallow, str) else set(disallow)
    allow_tags = {allow} if isinstance(allow, str) else set(allow)
    disallow_agents = robots_agents_for_tags(disallow_tags) if disallow_tags else []
    allow_agents = robots_agents_for_tags(allow_tags) if allow_tags else []
    blocked = set(disallow_agents)

    blocks = []
    for agent in disallow_agents:
        blocks.append(f"User-agent: {agent}\nDisallow: {path}")
    for agent in allow_agents:
        if agent in blocked:
            continue
        blocks.append(f"User-agent: {agent}\nAllow: {path}")

    return "\n\n".join(blocks) + "\n" if blocks else ""


def _name_chars_end(s: str, start: int) -> int:
    j = start
    while j < len(s) and s[j] in _NAME_CHARS:
        j += 1
    return j


def _strip_version(token: str) -> str:
    return token.split("/", 1)[0]


@lru_cache(maxsize=_CACHE)
def crawler_url(user_agent: str) -> str | None:
    for marker in ("http://", "https://"):
        i = 0
        while (i := user_agent.find(marker, i)) != -1:
            prefix_ok = (
                i == 0
                or user_agent[i - 1] in "+;"
                or (i >= 3 and user_agent[i - 3 : i] == " - ")
            )
            if prefix_ok:
                j = i
                while j < len(user_agent) and user_agent[j] not in _URL_STOPS:
                    j += 1
                return user_agent[i:j]
            i += 1
    return None


def _compat_name(ua: str) -> str | None:
    low = ua.lower()
    i = low.find("(compatible;")
    if i == -1:
        return None

    j = i + len("(compatible;")
    while j < len(ua) and ua[j] == " ":
        j += 1

    if j >= len(ua) or not ua[j].isalpha():
        return None

    end = _name_chars_end(ua, j)
    return _strip_version(ua[j:end])


def _is_name_start(c: str) -> bool:
    return "A" <= c <= "Z"


def _grab_name_sequence(ua: str, start: int) -> tuple[int, str]:
    end = _name_chars_end(ua, start)
    name = ua[start:end]

    while end + 1 < len(ua) and ua[end] == " " and _is_name_start(ua[end + 1]):
        next_end = _name_chars_end(ua, end + 1)
        name += " " + ua[end + 1 : next_end]
        end = next_end

    return end, _strip_version(name)


def _prefix_name(ua: str) -> str | None:
    if not ua or not _is_name_start(ua[0]):
        return None

    end, name = _grab_name_sequence(ua, 0)
    if end >= len(ua):
        return name

    after = ua[end]
    if after == "/":
        tail_end = _name_chars_end(ua, end + 1)
        end = tail_end
        if end >= len(ua):
            return name
        after = ua[end]

    if after == " " and ua[end:].startswith(" - "):
        return name
    if after in " \t":
        return name
    return None


def _name_non_mozilla(ua: str) -> str | None:
    name = _prefix_name(ua)
    if name:
        return name

    parts = ua.split()
    return _strip_version(parts[0]) if parts else None


def _strip_parens(ua: str) -> str:
    open_i = ua.find("(")
    if open_i == -1:
        return ua

    parts = []
    start = 0
    while open_i != -1:
        parts.append(ua[start:open_i])
        close_i = ua.find(")", open_i + 1)
        start = close_i + 1 if close_i != -1 else len(ua)
        open_i = ua.find("(", start)
    parts.append(ua[start:])
    return " ".join(parts)


def _token_name(token: str) -> str | None:
    slash = token.find("/")
    base = token[:slash] if slash != -1 else token.rstrip(",")
    if not base or not ("A" <= base[0] <= "Z") or base in _SKIP_TOKENS:
        return None
    return base


def _scan_mozilla_name(ua: str) -> str | None:
    last: str | None = None
    prev: str | None = None

    for token in _strip_parens(ua).split():
        base = _token_name(token)
        if base is None:
            prev = None
            continue

        last = f"{prev} {base}" if prev else base
        prev = last

    return last


@lru_cache(maxsize=_CACHE)
def crawler_name(user_agent: str) -> str | None:
    compat = _compat_name(user_agent)
    if compat:
        return compat

    if not user_agent.startswith("Mozilla/5.0"):
        return _name_non_mozilla(user_agent)

    return _scan_mozilla_name(user_agent)


def _version_from_compat(ua: str) -> str | None:
    low = ua.lower()
    i = low.find("(compatible;")
    if i == -1:
        return None

    j = i + len("(compatible;")
    while j < len(ua) and ua[j] == " ":
        j += 1

    if j >= len(ua) or not ua[j].isalpha():
        return None

    end = _name_chars_end(ua, j)
    if end >= len(ua) or ua[end] != "/":
        return None

    ver_end = _name_chars_end(ua, end + 1)
    return ua[end + 1 : ver_end] or None


def _version_mozilla(ua: str) -> str | None:
    compat = _version_from_compat(ua)
    if compat:
        return compat

    cleaned = ua.replace("(", " ").replace(")", " ")
    for token in cleaned.split():
        if "://" in token:
            continue

        slash = token.find("/")
        if slash == -1:
            continue

        base = token[:slash]
        if base in _BROWSER_TOKENS:
            continue

        ver_end = _name_chars_end(token, slash + 1)
        ver = token[slash + 1 : ver_end]
        if ver:
            return ver
    return None


def _version_non_mozilla(ua: str) -> str | None:
    parts = ua.split()
    if not parts:
        return None

    first = parts[0]
    slash = first.find("/")
    return first[slash + 1 :] if slash != -1 else None


@lru_cache(maxsize=_CACHE)
def crawler_version(user_agent: str) -> str | None:
    if not user_agent.startswith("Mozilla/5.0"):
        return _version_non_mozilla(user_agent)
    return _version_mozilla(user_agent)
