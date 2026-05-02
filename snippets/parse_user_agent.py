from dataclasses import dataclass


@dataclass
class UserAgent:
    raw: str
    browser: str | None
    browser_version: str | None
    engine: str | None
    os: str | None
    os_version: str | None
    device: str | None
    is_mobile: bool


_BROWSERS = (
    ("Edge", ("Edg/", "Edge/", "EdgA/", "EdgiOS/")),
    ("Opera", ("OPR/", "Opera/")),
    ("Samsung", ("SamsungBrowser/",)),
    ("Firefox", ("Firefox/", "FxiOS/")),
    ("Mobile Chrome", ("CriOS/",)),
    ("Chrome", ("Chrome/",)),
    ("Safari", ("Version/",)),
    ("IE", ("MSIE ", "Trident/")),
)


def _read_version(user_agent: str, start: int) -> str | None:
    end = start
    while end < len(user_agent) and user_agent[end] in "0123456789.":
        end += 1
    return user_agent[start:end] or None


def _token_version(user_agent: str, token: str) -> str | None:
    index = user_agent.find(token)
    return None if index == -1 else _read_version(user_agent, index + len(token))


def _detect_browser(user_agent: str) -> tuple[str | None, str | None]:
    for name, tokens in _BROWSERS:
        for token in tokens:
            if token in user_agent:
                return name, _token_version(user_agent, token)
    return None, None


def _detect_engine(user_agent: str) -> str | None:
    for token in ("AppleWebKit", "Gecko", "Trident", "Presto", "KHTML"):
        if token in user_agent:
            return token
    return None


def _detect_os(user_agent: str) -> tuple[str | None, str | None]:
    if "Windows NT" in user_agent:
        return "Windows", _token_version(user_agent, "Windows NT ")
    if "Android" in user_agent:
        return "Android", _token_version(user_agent, "Android ")
    if "iPhone OS" in user_agent or "CPU OS" in user_agent:
        token = "iPhone OS " if "iPhone OS" in user_agent else "CPU OS "
        index = user_agent.find(token) + len(token)
        end = index
        while end < len(user_agent) and user_agent[end] in "0123456789_":
            end += 1
        return "iOS", user_agent[index:end].replace("_", ".") or None
    if "Mac OS X" in user_agent:
        return "macOS", None
    if "Linux" in user_agent or "X11" in user_agent:
        return "Linux", None
    return None, None


def _detect_device(user_agent: str) -> str | None:
    if "iPad" in user_agent or "Tablet" in user_agent:
        return "Tablet"
    if "Mobile" in user_agent or "iPhone" in user_agent:
        return "Mobile"
    if "Windows" in user_agent or "Macintosh" in user_agent or "X11" in user_agent:
        return "Desktop"
    return None


def parse(user_agent: str) -> UserAgent:
    browser, version = _detect_browser(user_agent)
    os_name, os_version = _detect_os(user_agent)
    device = _detect_device(user_agent)
    return UserAgent(
        raw=user_agent,
        browser=browser,
        browser_version=version,
        engine=_detect_engine(user_agent),
        os=os_name,
        os_version=os_version,
        device=device,
        is_mobile=device == "Mobile",
    )
