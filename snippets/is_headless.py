_HEADLESS = ("headless", "phantomjs", "slimerjs", "electron", "nightmare")

_AUTOMATION = ("selenium", "webdriver", "puppeteer", "playwright", "cypress")

_HTTP_CLIENTS = (
    "curl",
    "wget",
    "python-requests",
    "python-urllib",
    "aiohttp",
    "httpx",
    "go-http-client",
    "okhttp",
    "java/",
    "libwww",
    "guzzle",
    "axios",
    "node-fetch",
    "postman",
    "insomnia",
    "restsharp",
)


def headless_kind(user_agent: str) -> str | None:
    """Classify non-human client: 'headless', 'automation', 'http-client'"""
    low = user_agent.lower()
    if any(token in low for token in _HEADLESS):
        return "headless"
    if any(token in low for token in _AUTOMATION):
        return "automation"
    if any(token in low for token in _HTTP_CLIENTS):
        return "http-client"
    return None


def is_headless(user_agent: str) -> bool:
    """User agent is a headless browser, automation tool, or HTTP library"""
    return headless_kind(user_agent) is not None
