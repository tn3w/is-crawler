def is_crawler(user_agent: str) -> bool:
    low = user_agent.lower()
    return (
        "bot" in low
        or "+http" in low
        or "https://" in low
        or "crawler" in low
        or "spider" in low
        or "feed" in low
        or "monitor" in low
        or "uptime" in low
        or "python-" in low
        or "fetcher" in low
        or "scraper" in low
        or "archiver" in low
        or "slurp" in low
        or "ptst/" in low
    )
