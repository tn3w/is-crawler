def crawler_name(user_agent: str) -> str | None:
    if user_agent.startswith("Mozilla/"):
        compat = user_agent.find("(compatible;")
        if compat == -1:
            return None
        start = compat + len("(compatible;")
        while start < len(user_agent) and user_agent[start] == " ":
            start += 1
        end = start
        while end < len(user_agent) and user_agent[end] not in " /;)":
            end += 1
        name = user_agent[start:end]
        return name or None

    head = user_agent.split(None, 1)[0] if user_agent else ""
    return head.split("/", 1)[0] or None
