_WIN_NT = {
    "10.0": "10/11",
    "6.3": "8.1",
    "6.2": "8",
    "6.1": "7",
    "6.0": "Vista",
    "5.1": "XP",
    "5.0": "2000",
}


def _read_dotted(text: str, start: int) -> str | None:
    end = start
    while end < len(text) and (text[end].isdigit() or text[end] == "."):
        end += 1
    return text[start:end].strip(".") or None


def _ios_version(user_agent: str) -> str | None:
    for token in ("iPhone OS ", "CPU OS "):
        index = user_agent.find(token)
        if index == -1:
            continue
        end = index + len(token)
        while end < len(user_agent) and user_agent[end] in "0123456789_":
            end += 1
        return user_agent[index + len(token) : end].replace("_", ".") or None
    return None


def detect_os(user_agent: str) -> tuple[str | None, str | None]:
    if "Windows NT" in user_agent:
        version = _read_dotted(user_agent, user_agent.find("Windows NT") + 11)
        return "Windows", _WIN_NT.get(version or "", version)
    if "iPhone OS" in user_agent or "CPU OS" in user_agent:
        name = "iPadOS" if "iPad" in user_agent else "iOS"
        return name, _ios_version(user_agent)
    if "Mac OS X" in user_agent:
        return "macOS", None
    if "Android" in user_agent:
        return "Android", _read_dotted(user_agent, user_agent.find("Android ") + 8)
    if "CrOS" in user_agent:
        return "Chromium OS", None
    if "Linux" in user_agent or "X11" in user_agent:
        return "Linux", None
    return None, None
