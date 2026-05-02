_MOBILE_TOKENS = ("Mobile", "iPhone", "iPod", "Android", "BlackBerry", "Opera Mini")
_TABLET_TOKENS = ("iPad", "Tablet", "Kindle", "PlayBook", "Nexus 7", "Nexus 10")


def is_tablet(user_agent: str) -> bool:
    return any(token in user_agent for token in _TABLET_TOKENS)


def is_mobile(user_agent: str) -> bool:
    if is_tablet(user_agent):
        return False
    return any(token in user_agent for token in _MOBILE_TOKENS)
