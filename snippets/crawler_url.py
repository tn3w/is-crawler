_URL_STOPS = " );,"


def crawler_url(user_agent: str) -> str | None:
    for marker in ("http://", "https://"):
        index = 0
        while (index := user_agent.find(marker, index)) != -1:
            valid_prefix = (
                index == 0
                or user_agent[index - 1] in "+;"
                or user_agent[max(0, index - 3) : index] == " - "
            )
            if valid_prefix:
                end = index
                while end < len(user_agent) and user_agent[end] not in _URL_STOPS:
                    end += 1
                return user_agent[index:end]
            index += 1
    return None


def crawler_contact(user_agent: str) -> str | None:
    at = user_agent.find("@")
    if at <= 0:
        return None
    start = at
    while start > 0 and (
        user_agent[start - 1].isalnum() or user_agent[start - 1] in ".-_+"
    ):
        start -= 1
    end = at + 1
    while end < len(user_agent) and (
        user_agent[end].isalnum() or user_agent[end] in ".-_"
    ):
        end += 1
    domain = user_agent[at + 1 : end]
    if "." not in domain or start == at:
        return None
    return user_agent[start:end]
