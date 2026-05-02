_KEYWORDS = (
    "bot",
    "crawl",
    "spider",
    "scrape",
    "slurp",
    "archiv",
    "headless",
    "indexer",
    "preview",
    "fetch",
    "monitor",
    "uptime",
    "feed",
    "check",
    "validator",
    "scan",
    "probe",
    "rank",
    "analyz",
    "synthetic",
    "sitemap",
    "favicon",
    "resolver",
    "sleuth",
    "ghost",
    "page speed",
    "search console",
    "-publisher",
    "-agent",
    "www.",
)
_REAL_BROWSERS = (
    "opera/",
    "lynx/",
    "links ",
    "links/",
    "elinks/",
    "w3m/",
    "konqueror/",
    "icab/",
    "netsurf",
    "seamonkey/",
    "iceweasel/",
)
_REAL_COMPAT = (
    "msie",
    "konqueror",
    "avant",
    "maxthon",
    "sleipnir",
    "acoo",
    "slcc",
    ".net clr",
    "presto",
)


def _bare_compatible(low: str) -> bool:
    start = low.find("(compatible;")
    if start == -1:
        return False
    end = low.find(")", start)
    return end != -1 and not any(token in low[start:end] for token in _REAL_COMPAT)


def is_crawler(user_agent: str) -> bool:
    low = user_agent.lower()

    if any(keyword in low for keyword in _KEYWORDS):
        return True
    if "http://" in user_agent or "https://" in user_agent:
        return True
    if not user_agent.startswith("Mozilla/") and not any(
        b in low for b in _REAL_BROWSERS
    ):
        return True
    return _bare_compatible(low)
