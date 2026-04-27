from __future__ import annotations

from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any


@dataclass
class UserAgent:
    raw: str
    product_token: str | None
    comment: str | None
    engine: str | None
    engine_version: str | None
    browser: str | None
    browser_version: str | None
    browser_major: str | None
    os: str | None
    os_version: str | None
    cpu: str | None
    device: str | None
    device_brand: str | None
    device_model: str | None
    rendering: str | None
    is_mobile: bool
    is_tablet: bool
    is_crawler: bool
    languages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_BROWSERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Opera GX", ("OPRGX/",)),
    ("Opera Touch", ("OPT/",)),
    ("Opera Mini", ("Opera Mini/",)),
    ("Brave", ("Brave/", "brave/")),
    ("Edge", ("Edg/", "Edge/", "EdgA/", "EdgiOS/")),
    ("Opera", ("OPR/",)),
    ("Samsung Browser", ("SamsungBrowser/",)),
    ("UC Browser", ("UCBrowser/", "UCWEB/")),
    ("Yandex", ("YaBrowser/",)),
    ("Google App", ("GSA/",)),
    ("Mobile Chrome", ("CriOS/",)),
    ("Firefox iOS", ("FxiOS/",)),
    ("Huawei Browser", ("HuaweiBrowser/",)),
    ("MIUI Browser", ("MiuiBrowser/",)),
    ("Silk", ("Silk/",)),
    ("Vivaldi", ("Vivaldi/",)),
    ("Tor Browser", ("TorBrowser/",)),
    ("DuckDuckGo", ("DuckDuckGo/",)),
    ("Waterfox", ("Waterfox/",)),
    ("Whale", ("Whale/",)),
    ("QQBrowser", ("QQBrowser/", "MQQBrowser/")),
    ("WeChat", ("MicroMessenger/",)),
    ("Snapchat", ("Snapchat/",)),
    ("Instagram", ("Instagram ",)),
    ("Facebook", ("FBAV/", "FBIOS/")),
    ("LinkedIn", ("LinkedInApp/",)),
    ("Pinterest", ("Pinterest/",)),
    ("TikTok", ("musical_ly", "musically_go/", "TikTok/")),
    ("Maxthon", ("Maxthon/",)),
    ("Midori", ("Midori/", "midori/")),
    ("Arora", ("Arora/",)),
    ("Iron", ("Iron/",)),
    ("Lunascape", ("Lunascape/",)),
    ("Shiira", ("Shiira/",)),
    ("NetFront NX", ("NX/",)),
    ("NetFront", ("NetFront/",)),
    ("NetNewsWire", ("NetNewsWire/",)),
    ("QtWeb", ("QtWeb Internet Browser/",)),
    ("Stainless", ("Stainless/",)),
    ("Rekonq", ("rekonq/", "Rekonq/")),
    ("Iceape", ("Iceape/",)),
    ("Sunrise", ("Sunrise/",)),
    ("Mosaic", ("NCSA_Mosaic/", "NCSA Mosaic/")),
    ("Opera Mini", ("OPiOS/",)),
    ("Opera Mobile", ("Opera Mobi/",)),
    ("Coc Coc", ("coc_coc_browser/",)),
    ("OmniWeb", ("OmniWeb/",)),
    ("SeaMonkey", ("SeaMonkey/",)),
    ("PaleMoon", ("PaleMoon/", "Palemoon/")),
    ("Iceweasel", ("Iceweasel/", "iceweasel/")),
    ("K-Meleon", ("K-Meleon/",)),
    ("Epiphany", ("Epiphany/",)),
    ("Sleipnir", ("Sleipnir/",)),
    ("Netscape", ("Netscape/", "Navigator/")),
    ("PhantomJS", ("PhantomJS/",)),
    ("Chromium", ("Chromium/",)),
    ("Firefox", ("Firefox/",)),
    ("Chrome", ("Chrome/", "HeadlessChrome/")),
    ("Safari", ("Version/",)),
    ("IE", ("MSIE ",)),
    ("IEMobile", ("IEMobile/",)),
    ("Konqueror", ("Konqueror/",)),
    ("Lynx", ("Lynx/",)),
    ("w3m", ("w3m/",)),
    ("Links", ("Links (", "Links/")),
    ("ELinks", ("ELinks/",)),
)

_LIB_BROWSERS: tuple[tuple[str, str], ...] = (
    ("curl", "curl/"),
    ("Wget", "Wget/"),
    ("HTTPie", "HTTPie/"),
    ("Python Requests", "python-requests/"),
    ("Python urllib", "Python-urllib/"),
    ("aiohttp", "aiohttp/"),
    ("httpx", "python-httpx/"),
    ("Go-http-client", "Go-http-client/"),
    ("Java", "Java/"),
    ("OkHttp", "okhttp/"),
    ("Apache-HttpClient", "Apache-HttpClient/"),
    ("node-fetch", "node-fetch/"),
    ("axios", "axios/"),
    ("got", "got/"),
    ("undici", "undici/"),
    ("Dart", "Dart/"),
    ("Ruby", "Ruby/"),
    ("Faraday", "Faraday "),
    ("PHP", "PHP/"),
    ("Guzzle", "GuzzleHttp/"),
    ("PostmanRuntime", "PostmanRuntime/"),
    ("Insomnia", "insomnia/"),
)

_WIN_NT = {
    "10.0": "10/11",
    "6.3": "8.1",
    "6.2": "8",
    "6.1": "7",
    "6.0": "Vista",
    "5.2": "XP x64",
    "5.1": "XP",
    "5.0": "2000",
    "4.0": "NT 4.0",
}

_DIRECT_OS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Windows Phone OS",), "Windows Phone OS"),
    (("Windows Phone",), "Windows Phone"),
    (("Windows Mobile",), "Windows Mobile"),
    (("CrOS",), "Chromium OS"),
    (("PlayStation", "PLAYSTATION"), "PlayStation"),
    (("Nintendo",), "Nintendo"),
    (("SymbOS", "Symbian", "S60"), "Symbian"),
    (("Tizen",), "Tizen"),
    (("KaiOS",), "KaiOS"),
    (("HarmonyOS",), "HarmonyOS"),
    (("BlackBerry", "BB10"), "BlackBerry"),
    (("webOS", "hpwOS"), "webOS"),
    (("SunOS", "Solaris"), "Solaris"),
    (("FreeBSD",), "FreeBSD"),
    (("NetBSD",), "NetBSD"),
    (("OpenBSD",), "OpenBSD"),
    (("DragonFly",), "DragonFly"),
    (("Haiku",), "Haiku"),
    (("OS/2",), "OS/2"),
    (("AmigaOS",), "AmigaOS"),
)

_LINUX_DISTROS = (
    "Ubuntu",
    "Fedora",
    "Debian",
    "CentOS",
    "Arch",
    "Mint",
    "SUSE",
    "Red Hat",
    "Gentoo",
    "Kali",
    "Raspbian",
    "Slackware",
    "Mageia",
    "OpenSUSE",
    "openSUSE",
    "Kubuntu",
    "Mandriva",
    "Manjaro",
)

_DEVICE_BRANDS: tuple[tuple[str, str, str], ...] = (
    ("iPhone", "Apple", "iPhone"),
    ("iPad", "Apple", "iPad"),
    ("iPod", "Apple", "iPod"),
    ("Macintosh", "Apple", "Mac"),
    ("Apple TV", "Apple", "Apple TV"),
    ("Pixel", "Google", "Pixel"),
    ("Nexus", "Google", "Nexus"),
    ("SM-", "Samsung", "Galaxy"),
    ("GT-", "Samsung", "Galaxy"),
    ("SCH-", "Samsung", "Galaxy"),
    ("SHV-", "Samsung", "Galaxy"),
    ("SPH-", "Samsung", "Galaxy"),
    ("HUAWEI", "Huawei", "Huawei"),
    ("HONOR", "Honor", "Honor"),
    ("Mi ", "Xiaomi", "Mi"),
    ("MI ", "Xiaomi", "Mi"),
    ("Redmi", "Xiaomi", "Redmi"),
    ("POCO", "Xiaomi", "Poco"),
    ("OnePlus", "OnePlus", "OnePlus"),
    ("OPPO", "Oppo", "Oppo"),
    ("vivo", "Vivo", "Vivo"),
    ("realme", "Realme", "Realme"),
    ("Nokia", "Nokia", "Nokia"),
    ("Moto ", "Motorola", "Moto"),
    ("Motorola", "Motorola", "Motorola"),
    ("LG-", "LG", "LG"),
    ("LM-", "LG", "LG"),
    ("HTC", "HTC", "HTC"),
    ("Sony", "Sony", "Sony"),
    ("Kindle Fire", "Amazon", "Kindle Fire"),
    ("Kindle", "Amazon", "Kindle"),
    ("KFAPWI", "Amazon", "Kindle Fire"),
    ("PlayStation", "Sony", "PlayStation"),
    ("Xbox", "Microsoft", "Xbox"),
    ("Nintendo Switch", "Nintendo", "Switch"),
    ("Nintendo", "Nintendo", "Nintendo"),
    ("Surface", "Microsoft", "Surface"),
    ("Lumia", "Microsoft", "Lumia"),
    ("BlackBerry", "BlackBerry", "BlackBerry"),
    ("BB10", "BlackBerry", "BlackBerry"),
    ("Roku", "Roku", "Roku"),
    ("BRAVIA", "Sony", "Bravia"),
    ("AppleTV", "Apple", "Apple TV"),
)

_DEVICE_KIND: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Xbox", "PlayStation", "PLAYSTATION", "Nintendo"), "Console"),
    (("QtCarBrowser", "Tesla/"), "Embedded"),
    (
        ("SMART-TV", "SmartTV", "HbbTV", "SHIELD Android TV", "Android TV", "AppleTV"),
        "SmartTV",
    ),
    (("iPad", "Tablet"), "Tablet"),
    (("iPhone", "iPod"), "Mobile"),
)

_BOT_TOKENS = (
    "bot",
    "crawler",
    "spider",
    "slurp",
    "scraper",
    "preview",
    "fetcher",
    "monitor",
    "archiver",
)

_CPU_PATTERNS: tuple[tuple[str, str], ...] = (
    ("amd64", "x86_64"),
    ("x86_64", "x86_64"),
    ("Win64; x64", "x86_64"),
    ("WOW64", "x86_64"),
    ("x64", "x86_64"),
    ("i686", "x86"),
    ("i386", "x86"),
    ("Win32", "x86"),
    ("aarch64", "arm64"),
    ("arm64", "arm64"),
    ("ARM64", "arm64"),
    ("armv7", "arm"),
    ("armv8", "arm64"),
    ("ARM", "arm"),
    ("PPC", "ppc"),
)

_WIN_LEGACY = ("95", "98", "ME", "XP", "2000")

_CHROME_DISAMBIG = (
    "Edg/",
    "Edge/",
    "EdgA/",
    "EdgiOS/",
    "OPR/",
    "OPRGX/",
    "OPT/",
    "Brave/",
    "brave/",
    "SamsungBrowser/",
    "UCBrowser/",
    "UCWEB/",
    "YaBrowser/",
    "GSA/",
    "HuaweiBrowser/",
    "MiuiBrowser/",
    "Vivaldi/",
    "Whale/",
    "QQBrowser/",
    "MQQBrowser/",
    "coc_coc_browser/",
    "MicroMessenger/",
    "Snapchat/",
    "Instagram ",
    "FBAV/",
    "FBIOS/",
    "LinkedInApp/",
    "Pinterest/",
    "musical_ly",
    "musically_go/",
    "TikTok/",
    "Maxthon/",
    "DuckDuckGo/",
    "PhantomJS/",
    "HeadlessChrome/",
    "CriOS/",
    "Silk/",
    "Chromium/",
)

_FIREFOX_DISAMBIG = (
    "Waterfox/",
    "PaleMoon/",
    "Palemoon/",
    "Iceweasel/",
    "iceweasel/",
    "SeaMonkey/",
    "TorBrowser/",
    "FxiOS/",
    "K-Meleon/",
    "Iceape/",
)


def _read_version(ua: str, start: int) -> str | None:
    end = start
    while end < len(ua) and (ua[end].isdigit() or ua[end] == "."):
        end += 1
    return ua[start:end] or None


def _read_int(ua: str, start: int) -> tuple[str, int]:
    end = start
    while end < len(ua) and ua[end].isdigit():
        end += 1
    return ua[start:end], end


def _read_dotted(ua: str, start: int, max_extra: int) -> str | None:
    head, pos = _read_int(ua, start)
    if not head:
        return None
    parts = [head]
    while max_extra > 0 and pos < len(ua) and ua[pos] == ".":
        nxt, end = _read_int(ua, pos + 1)
        if not nxt:
            break
        parts.append(nxt)
        pos = end
        max_extra -= 1
    return ".".join(parts)


def _underscore_version(ua: str, start: int) -> str | None:
    a, p = _read_int(ua, start)
    if not a or p >= len(ua) or ua[p] != "_":
        return None
    b, p = _read_int(ua, p + 1)
    if not b:
        return None
    if p < len(ua) and ua[p] == "_":
        c, p = _read_int(ua, p + 1)
        if c:
            return f"{a}.{b}.{c}"
    return f"{a}.{b}"


def _mac_version(ua: str, start: int) -> str | None:
    a, p = _read_int(ua, start)
    if not a or p >= len(ua) or ua[p] not in "._":
        return None
    b, p = _read_int(ua, p + 1)
    if not b:
        return None
    if p < len(ua) and ua[p] in "._":
        c, p = _read_int(ua, p + 1)
        if c:
            return f"{a}.{b}.{c}"
    return f"{a}.{b}"


def _ios_version(ua: str) -> str | None:
    for token in ("iPhone OS ", "CPU OS "):
        idx = ua.find(token)
        if idx != -1:
            ver = _underscore_version(ua, idx + len(token))
            if ver:
                return ver
    return None


def _android_version(ua: str) -> str | None:
    for token in ("Android ", "Android-"):
        idx = ua.find(token)
        if idx != -1:
            ver = _read_dotted(ua, idx + len(token), 2)
            if ver:
                return ver
    return None


def _find_paren_contents(ua: str) -> list[str]:
    out: list[str] = []
    i = 0
    while (i := ua.find("(", i)) != -1:
        end = ua.find(")", i + 1)
        if end == -1:
            break
        if end > i + 1:
            out.append(ua[i + 1 : end])
        i = end + 1
    return out


def _token_version(ua: str, token: str) -> str | None:
    idx = ua.find(token)
    return None if idx == -1 else _read_version(ua, idx + len(token))


def _has_any(ua: str, tokens: tuple[str, ...]) -> bool:
    return any(token in ua for token in tokens)


def _detect_browser(ua: str) -> tuple[str | None, str | None]:
    if not ua.startswith("Mozilla/"):
        for family, token in _LIB_BROWSERS:
            version = _token_version(ua, token)
            if version:
                return family, version

    if ua.startswith("Opera/") and ("Presto/" in ua or "Version/" in ua):
        version = _token_version(ua, "Version/") or _token_version(ua, "Opera/")
        if "Opera Mini/" in ua:
            return "Opera Mini", _token_version(ua, "Opera Mini/")
        if "Opera Mobi/" in ua:
            return "Opera Mobile", version
        return "Opera", version

    if ("iPad" in ua or "iPhone" in ua) and "CriOS/" in ua:
        return "Mobile Chrome", _token_version(ua, "CriOS/")

    if "Chrome/" in ua and ("Android" in ua or "iPad" in ua) and "Mobile Safari/" in ua:
        if "; wv)" in ua and "Version/" in ua:
            return "Chrome WebView", _token_version(ua, "Chrome/")
        if not any(t in ua for t in ("Edg", "OPR/", "SamsungBrowser/", "YaBrowser/")):
            return "Mobile Chrome", _token_version(ua, "Chrome/")

    if "Chrome/" in ua and not any(t in ua for t in _CHROME_DISAMBIG):
        return "Chrome", _token_version(ua, "Chrome/")

    if (
        "Firefox/" in ua
        and "Android" not in ua
        and not any(t in ua for t in _FIREFOX_DISAMBIG)
    ):
        return "Firefox", _token_version(ua, "Firefox/")

    for family, tokens in _BROWSERS:
        for token in tokens:
            if token not in ua:
                continue
            version = _token_version(ua, token)
            if not version and family not in ("Lynx", "w3m", "Links", "ELinks", "Mosaic"):
                continue
            if family == "Safari" and "Safari/" not in ua:
                continue
            if family == "Safari" and ("Mobile/" in ua or "Mobile Safari/" in ua):
                return "Mobile Safari", version
            if family == "Firefox" and "Android" in ua and "Mobile;" in ua:
                return "Mobile Firefox", version
            return family, version

    if "Trident/" in ua and "rv:" in ua and "MSIE" not in ua:
        idx = ua.find("rv:")
        return "IE", _read_dotted(ua, idx + 3, 1)

    if ua.startswith("Mozilla/5.0") and "Gecko/" in ua:
        idx = ua.find("rv:")
        version = _read_dotted(ua, idx + 3, 1) if idx != -1 else None
        return "Firefox", version

    if "AppleWebKit/" in ua and ("iPhone" in ua or "iPad" in ua) and "Mobile/" in ua:
        return "Mobile Safari", _token_version(ua, "AppleWebKit/")

    if "AppleWebKit/" in ua and "Safari/" in ua and "Version/" not in ua:
        return "Safari", _token_version(ua, "Safari/")

    if "AppleWebKit/" in ua and "Macintosh" in ua and "Safari/" not in ua:
        return "Apple Mail", _token_version(ua, "AppleWebKit/")

    if " " not in ua and "/" in ua:
        family, _, version = ua.partition("/")
        ver = _read_dotted(version, 0, 99)
        return family, ver

    return None, None


def _detect_engine(ua: str) -> tuple[str | None, str | None]:
    if "AppleWebKit/" in ua:
        version = _token_version(ua, "AppleWebKit/")
        if "Trident/" in ua:
            return "Trident", _token_version(ua, "Trident/")
        if "Blink" in ua or _is_blink(ua):
            return "Blink", version
        return "AppleWebKit", version
    if "Trident/" in ua:
        return "Trident", _token_version(ua, "Trident/")
    if "Goanna/" in ua:
        return "Goanna", _token_version(ua, "Goanna/")
    if "Gecko/" in ua:
        return "Gecko", _token_version(ua, "Gecko/")
    if "Presto/" in ua:
        return "Presto", _token_version(ua, "Presto/")
    if "KHTML" in ua:
        return "KHTML", None
    return None, None


def _is_blink(ua: str) -> bool:
    if _has_any(
        ua,
        ("OPR/", "Edg/", "EdgA/", "Brave/", "Vivaldi/", "SamsungBrowser/", "YaBrowser/"),
    ):
        return True
    version = _token_version(ua, "Chrome/") or _token_version(ua, "Chromium/")
    if not version:
        return False
    major = version.split(".", 1)[0]
    return major.isdigit() and int(major) >= 28


def _detect_os(ua: str) -> tuple[str | None, str | None]:
    nt_idx = ua.find("Windows NT")
    if nt_idx != -1 and "Windows Phone" not in ua:
        ver = _read_dotted(ua, nt_idx + 11, 1)
        if ver and "." in ver:
            return "Windows", _WIN_NT.get(ver, ver)
        return "Windows", "NT"

    if "Windows Phone" in ua:
        idx = ua.find("Windows Phone ")
        ver = _read_dotted(ua, idx + 14, 2) if idx != -1 else None
        return "Windows Phone", ver

    for tokens, name in _DIRECT_OS:
        if _has_any(ua, tokens):
            return name, _direct_os_version(ua, name)

    if "Windows CE" in ua:
        return "Windows", "CE"
    for legacy in _WIN_LEGACY:
        if f"Windows {legacy}" in ua:
            return "Windows", legacy

    if "Xbox" in ua:
        return "Xbox", None

    if "iPhone OS" in ua or ("CPU OS" in ua and "iPad" not in ua):
        return "iOS", _ios_version(ua)

    if "iPad" in ua and "CPU OS" in ua:
        return ("iOS" if "CriOS/" in ua else "iPadOS"), _ios_version(ua)

    if _has_any(ua, ("Mac OS X", "Macintosh", "Mac_PowerPC")):
        idx = ua.find("Mac OS X ")
        return "macOS", _mac_version(ua, idx + 9) if idx != -1 else None

    if "Android" in ua:
        return "Android", _android_version(ua)

    if "iPad" in ua:
        return "iPadOS", None

    if "Linux" in ua or "X11" in ua:
        for distro in _LINUX_DISTROS:
            ver = _distro_version(ua, distro)
            if ver is not None or distro in ua:
                return distro, ver
        kernel = _linux_kernel_version(ua)
        return "Linux", kernel

    return None, None


def _direct_os_version(ua: str, name: str) -> str | None:
    if name == "Chromium OS":
        return _cros_version(ua)
    if name == "Symbian":
        for token in ("SymbianOS/", "Symbian/", "S60/"):
            ver = _token_version(ua, token)
            if ver:
                return ver
    if name == "KaiOS":
        return _token_version(ua, "KaiOS/")
    if name == "Tizen":
        return _token_version(ua, "Tizen ") or _token_version(ua, "Tizen/")
    if name == "FreeBSD":
        return _token_version(ua, "FreeBSD ") or _token_version(ua, "FreeBSD/")
    if name == "NetBSD":
        return _token_version(ua, "NetBSD ") or _token_version(ua, "NetBSD/")
    if name == "OpenBSD":
        return _token_version(ua, "OpenBSD ") or _token_version(ua, "OpenBSD/")
    if name == "BlackBerry":
        return _token_version(ua, "BB10/") or _token_version(ua, "BlackBerry")
    if name == "webOS":
        return _token_version(ua, "webOS/") or _token_version(ua, "hpwOS/")
    return None


def _cros_version(ua: str) -> str | None:
    idx = ua.find("CrOS")
    if idx == -1:
        return None
    pos = idx + 4
    while pos < len(ua) and ua[pos] == " ":
        pos += 1
    while pos < len(ua) and ua[pos] not in (" ", ")"):
        pos += 1
    if pos >= len(ua) or ua[pos] == ")":
        return None
    pos += 1
    return _read_dotted(ua, pos, 3)


def _distro_version(ua: str, distro: str) -> str | None:
    for sep in ("/", " "):
        token = f"{distro}{sep}"
        idx = ua.find(token)
        if idx != -1:
            ver = _read_dotted(ua, idx + len(token), 3)
            if ver:
                return ver
    return None


def _linux_kernel_version(ua: str) -> str | None:
    idx = ua.find("Linux ")
    if idx == -1:
        return None
    pos = idx + 6
    if pos < len(ua) and ua[pos].isdigit():
        return _read_dotted(ua, pos, 3)
    return None


def _detect_cpu(ua: str) -> str | None:
    for token, label in _CPU_PATTERNS:
        if token in ua:
            return label
    return None


def _detect_device_kind(ua: str) -> str | None:
    for tokens, kind in _DEVICE_KIND:
        if _has_any(ua, tokens):
            return kind
    if "Tizen" in ua and ("SMART-TV" in ua or "TV" in ua):
        return "SmartTV"
    if "Android" in ua:
        return "Mobile" if "Mobile" in ua else "Tablet"
    if "Mobile" in ua:
        return "Mobile"
    if _has_any(ua, ("Macintosh", "Windows", "X11", "Linux", "CrOS")):
        return "Desktop"
    return None


def _detect_device_brand(
    ua: str, parens: list[str] | None = None
) -> tuple[str | None, str | None, str | None]:
    for token, brand, model in _DEVICE_BRANDS:
        if token in ua:
            return token, brand, model
    if "Android" in ua:
        for paren in parens if parens is not None else _find_paren_contents(ua):
            for chunk in paren.split(";"):
                chunk = chunk.strip()
                if chunk.startswith(("Linux", "Android")) or chunk == "K":
                    continue
                if chunk and chunk[0].isalpha() and len(chunk) <= 40:
                    return chunk, None, chunk
    if "QtCarBrowser" in ua or "Tesla/" in ua:
        return "Tesla", "Tesla", "Tesla"
    return None, None, None


def _extract_languages(ua: str, parens: list[str] | None = None) -> list[str]:
    languages: list[str] = []
    for paren in parens if parens is not None else _find_paren_contents(ua):
        for chunk in paren.split(";"):
            chunk = chunk.strip()
            if (
                len(chunk) in (2, 5)
                and chunk[:2].islower()
                and chunk[:2].isalpha()
                and (len(chunk) == 2 or (chunk[2] in "-_" and chunk[3:].isupper()))
                and chunk not in languages
            ):
                languages.append(chunk.replace("_", "-"))
    return languages


def _detect_crawler(ua: str) -> bool:
    low = ua.lower()
    return any(token in low for token in _BOT_TOKENS)


def _parse_ua(ua: str) -> UserAgent:
    parts = ua.split()
    open_idx = ua.find("(")
    close_idx = ua.find(")", open_idx) if open_idx >= 0 else -1
    comment = ua[open_idx : close_idx + 1] if 0 <= open_idx < close_idx else None

    rendering = None
    if "KHTML, like Gecko" in ua:
        rendering = "KHTML, like Gecko"
    elif "KHTML" in ua:
        rendering = "KHTML"

    parens = _find_paren_contents(ua)
    engine, engine_version = _detect_engine(ua)
    browser, browser_version = _detect_browser(ua)
    os_name, os_version = _detect_os(ua)
    device_kind = _detect_device_kind(ua)
    device_token, brand, model = _detect_device_brand(ua, parens)

    major = browser_version.split(".", 1)[0] if browser_version else None

    return UserAgent(
        raw=ua,
        product_token=parts[0] if parts else None,
        comment=comment,
        engine=engine,
        engine_version=engine_version,
        browser=browser,
        browser_version=browser_version,
        browser_major=major,
        os=os_name,
        os_version=os_version,
        cpu=_detect_cpu(ua),
        device=device_kind,
        device_brand=brand,
        device_model=model or device_token,
        rendering=rendering,
        is_mobile=device_kind == "Mobile",
        is_tablet=device_kind == "Tablet",
        is_crawler=_detect_crawler(ua),
        languages=_extract_languages(ua, parens),
    )


def normalize_user_agent(value: object) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    elif value is None:
        return ""
    elif not isinstance(value, str):
        value = str(value)
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())


@lru_cache(maxsize=4096)
def parse(ua: str) -> UserAgent:
    return _parse_ua(ua)


def parse_or_none(value: object) -> UserAgent | None:
    normalized = normalize_user_agent(value)
    return parse(normalized) if normalized else None


@lru_cache(maxsize=4096)
def is_crawler(ua: str) -> bool:
    return _detect_crawler(ua)


def is_browser(ua: str) -> bool:
    return not is_crawler(ua)
