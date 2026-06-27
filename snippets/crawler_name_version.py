def crawler_name_version(user_agent: str) -> tuple[str | None, str | None]:
    if user_agent.startswith("Mozilla/"):
        compat = user_agent.find("(compatible;")
        if compat == -1:
            return None, None
        start = compat + len("(compatible;")
        length = len(user_agent)
        while start < length and user_agent[start] == " ":
            start += 1
        end = start
        while end < length and user_agent[end] not in " /;)":
            end += 1
        name = user_agent[start:end] or None
        if end >= length or user_agent[end] != "/":
            return name, None
        version_start = end + 1
        version_end = version_start
        while version_end < length and user_agent[version_end] not in " ;)":
            version_end += 1
        return name, user_agent[version_start:version_end] or None

    head = user_agent.split(None, 1)[0] if user_agent else ""
    name, _, version = head.partition("/")
    return name or None, version or None
