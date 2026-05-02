def crawler_version(user_agent: str) -> str | None:
    if user_agent.startswith("Mozilla/"):
        compat = user_agent.find("(compatible;")
        if compat == -1:
            return None
        slash = user_agent.find("/", compat)
        if slash == -1:
            return None
        end = slash + 1
        while end < len(user_agent) and user_agent[end] not in " ;)":
            end += 1
        return user_agent[slash + 1 : end] or None

    head = user_agent.split(None, 1)[0] if user_agent else ""
    _, _, version = head.partition("/")
    return version or None
