def is_crawler(user_agent: str) -> bool:
    """~80% crawler recall via keyword scan"""
    keywords = "http bot .com crawl google url spider @ uptime java check site"
    low = user_agent.lower()
    return any(word in low for word in keywords.split())
