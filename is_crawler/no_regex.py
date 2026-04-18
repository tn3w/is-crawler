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
    if _fetch_not_api(low):
        return True
    if "+http://" in ua or "+https://" in ua:
        return True

    return _email_like(ua)


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
    if _find_word(low, "wget") or _find_word(low, "nmap"):
        return True
    if any(f"google{sep}{suf}" in low for sep in " -" for suf in _GOOGLE_SUFFIXES):
        return True

    return _has_by_domain(low) or _leading_domain(ua) or _semicolon_agent(low)


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
def is_crawler(ua: str) -> bool:
    if _bot_signal(ua) or _known_tool(ua) or _url_in_ua(ua):
        return True
    return not _browser(ua) or _bare_compat(ua)


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


def _name_chars_end(s: str, start: int) -> int:
    j = start
    while j < len(s) and s[j] in _NAME_CHARS:
        j += 1
    return j


def _strip_version(token: str) -> str:
    return token.split("/", 1)[0]


@lru_cache(maxsize=_CACHE)
def crawler_url(ua: str) -> str | None:
    for marker in ("http://", "https://"):
        i = 0
        while (i := ua.find(marker, i)) != -1:
            prefix_ok = (
                i == 0 or ua[i - 1] in "+;" or (i >= 3 and ua[i - 3 : i] == " - ")
            )
            if prefix_ok:
                j = i
                while j < len(ua) and ua[j] not in _URL_STOPS:
                    j += 1
                return ua[i:j]
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


_SKIP_TOKENS = _BROWSER_TOKENS | {"KHTML", "like"}


def _token_is_name(base: str) -> bool:
    return (
        bool(base)
        and _is_name_start(base[0])
        and base not in _SKIP_TOKENS
        and all(c in _NAME_CHARS for c in base)
    )


def _advance_paren_depth(token: str, depth: int) -> int:
    depth += token.count("(") - token.count(")")
    return 0 if depth < 0 else depth


def _token_base(token: str) -> str:
    return token.split("/", 1)[0].rstrip(",")


def _scan_mozilla_name(ua: str) -> str | None:
    last: str | None = None
    prev_name: str | None = None
    depth = 0

    for token in ua.split(" "):
        has_paren = "(" in token or ")" in token

        if depth > 0 or has_paren:
            if has_paren:
                depth = _advance_paren_depth(token, depth)
            prev_name = None
            continue

        base = _token_base(token)
        if not _token_is_name(base):
            prev_name = None
            continue

        last = f"{prev_name} {base}" if prev_name else base
        prev_name = last

    return last


@lru_cache(maxsize=_CACHE)
def crawler_name(ua: str) -> str | None:
    compat = _compat_name(ua)
    if compat:
        return compat

    if not ua.startswith("Mozilla/5.0"):
        return _name_non_mozilla(ua)

    return _scan_mozilla_name(ua)


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
def crawler_version(ua: str) -> str | None:
    if not ua.startswith("Mozilla/5.0"):
        return _version_non_mozilla(ua)
    return _version_mozilla(ua)


@lru_cache(maxsize=_CACHE)
def crawler_signals(ua: str) -> list[str]:
    checks = [
        ("bot_signal", _bot_signal(ua)),
        ("no_browser_signature", not _browser(ua)),
        ("bare_compatible", _bare_compat(ua)),
        ("known_tool", _known_tool(ua)),
        ("url_in_ua", _url_in_ua(ua)),
    ]
    return [name for name, ok in checks if ok]
