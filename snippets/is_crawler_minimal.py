def is_crawler(user_agent: str) -> bool:
    low = user_agent.lower()
    return (
        "bot" in low
        or "crawl" in low
        or "spider" in low
        or "scrap" in low
        or "http://" in low
        or "https://" in low
        or "www." in low
        or ".com" in low
        or "@" in low
        or "fetch" in low
        or "check" in low
        or "scan" in low
        or "inspect" in low
        or "monitor" in low
        or "preview" in low
        or "feed" in low
        or "uptime" in low
        or "resolver" in low
        or "agent" in low
        or "client" in low
        or "ping" in low
    )
