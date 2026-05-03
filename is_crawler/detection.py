from __future__ import annotations

from functools import lru_cache

_CACHE = 32768

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


def _local_start(ua: str, at: int) -> int:
    start = at
    while start > 0 and (ua[start - 1].isalnum() or ua[start - 1] in "._%+-"):
        start -= 1
    return start


def _domain_end(ua: str, at: int) -> int:
    end = at + 1
    while end < len(ua) and (ua[end].isalnum() or ua[end] in "_.-"):
        end += 1
    return end


def _valid_email_at(ua: str, at: int) -> tuple[int, int] | None:
    end = _domain_end(ua, at)
    domain = ua[at + 1 : end]
    if "." not in domain:
        return None
    tld = domain.rsplit(".", 1)[1]
    if len(tld) < 2 or not tld.isalpha():
        return None
    start = _local_start(ua, at)
    return (start, end) if start < at else None


@lru_cache(maxsize=_CACHE)
def crawler_contact(user_agent: str) -> str | None:
    i = 0
    while (i := user_agent.find("@", i)) != -1:
        span = _valid_email_at(user_agent, i)
        if span:
            start, end = span
            return user_agent[start:end]
        i += 1
    return None


def _bot_signal(ua: str, low: str) -> bool:
    if any(k in low for k in _BOT_KEYWORDS):
        return True
    if _find_word(low, "bot") or _find_word(low, "scan"):
        return True
    if "fetch" in low and _fetch_not_api(low):
        return True
    if "+http://" in ua or "+https://" in ua:
        return True

    return "@" in ua and crawler_contact(ua) is not None


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


def _known_tool(ua: str, low: str) -> bool:
    if any(t in low for t in _TOOLS):
        return True
    if _find_word(low, "wget") or _find_word(low, "nmap"):
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

    if suspicious and (
        _bot_signal(user_agent, low)
        or _known_tool(user_agent, low)
        or crawler_url(user_agent)
    ):
        return True
    if (
        not suspicious
        and not user_agent.startswith("Mozilla/")
        and _leading_domain(user_agent)
    ):
        return True
    return not _browser(user_agent) or _bare_compat(user_agent)


@lru_cache(maxsize=_CACHE)
def crawler_signals(user_agent: str) -> list[str]:
    low = user_agent.lower()
    checks = [
        ("bot_signal", _bot_signal(user_agent, low)),
        ("no_browser_signature", not _browser(user_agent)),
        ("bare_compatible", _bare_compat(user_agent)),
        ("known_tool", _known_tool(user_agent, low)),
        ("url_in_ua", crawler_url(user_agent) is not None),
    ]
    return [name for name, ok in checks if ok]


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


def _compat_name_span(ua: str) -> tuple[int, int] | None:
    i = ua.lower().find("(compatible;")
    if i == -1:
        return None

    j = i + len("(compatible;")
    while j < len(ua) and ua[j] == " ":
        j += 1

    if j >= len(ua) or not ua[j].isalpha():
        return None

    return j, _name_chars_end(ua, j)


def _compat_name(ua: str) -> str | None:
    span = _compat_name_span(ua)
    if span is None:
        return None
    j, end = span
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
        end = _name_chars_end(ua, end + 1)
        if end >= len(ua):
            return name
        after = ua[end]

    if after == " " and ua[end:].startswith(" - "):
        return name
    if after in " \t":
        return name
    return None


def _name_non_mozilla(ua: str) -> str | None:
    parts = ua.split()
    return _strip_version(parts[0]) if parts else None


_PAREN_SKIP_PREFIXES = (
    "compatible;",
    "khtml,",
    "windows",
    "macintosh",
    "x11",
    "linux",
    "iphone",
    "ipad",
    "ipod",
    "android",
)


def _split_segments(ua: str) -> list[str]:
    open_i = ua.find("(")
    if open_i == -1:
        return [ua]

    segments = []
    start = 0
    while open_i != -1:
        segments.append(ua[start:open_i])
        close_i = ua.find(")", open_i + 1)
        if close_i == -1:
            start = len(ua)
            break
        inner = ua[open_i + 1 : close_i]
        if not inner.lstrip().lower().startswith(_PAREN_SKIP_PREFIXES):
            segments.append(inner)
        start = close_i + 1
        open_i = ua.find("(", start)
    segments.append(ua[start:])
    return segments


def _token_name(token: str) -> str | None:
    slash = token.find("/")
    base = token[:slash] if slash != -1 else token.rstrip(",")
    if not base or not _is_name_start(base[0]) or base in _SKIP_TOKENS:
        return None
    if any(c not in _NAME_CHARS for c in base):
        return None
    return base


def _scan_mozilla_name(ua: str) -> str | None:
    last: str | None = None

    for segment in _split_segments(ua):
        prev: str | None = None
        for token in segment.split():
            base = _token_name(token)
            if base is None:
                prev = None
                continue
            last = f"{prev} {base}" if prev else base
            prev = last

    return last


@lru_cache(maxsize=_CACHE)
def crawler_name(user_agent: str) -> str | None:
    if not user_agent.startswith("Mozilla/"):
        prefix = _prefix_name(user_agent)
        if prefix:
            return prefix

    compat = _compat_name(user_agent)
    if compat:
        return compat

    if not user_agent.startswith("Mozilla/5.0"):
        return _name_non_mozilla(user_agent)

    return _scan_mozilla_name(user_agent)


def _version_from_compat(ua: str) -> str | None:
    span = _compat_name_span(ua)
    if span is None:
        return None
    _, end = span
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
