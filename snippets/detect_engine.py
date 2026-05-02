def detect_engine(user_agent: str) -> str | None:
    if "Edge/" in user_agent and "AppleWebKit/" not in user_agent:
        return "EdgeHTML"
    if "AppleWebKit/" in user_agent:
        if "Trident/" in user_agent:
            return "Trident"
        if "Chrome/" in user_agent or "Chromium/" in user_agent:
            return "Blink"
        return "AppleWebKit"
    if "Trident/" in user_agent:
        return "Trident"
    if "Gecko/" in user_agent:
        return "Gecko"
    if "Presto/" in user_agent:
        return "Presto"
    if "KHTML" in user_agent:
        return "KHTML"
    return None
