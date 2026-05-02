def build_robots_txt(disallow: list[str], allow: list[str] | None = None) -> str:
    blocks = []
    if disallow:
        agents = "\n".join(f"User-agent: {agent}" for agent in disallow)
        blocks.append(f"{agents}\nDisallow: /")
    if allow:
        agents = "\n".join(f"User-agent: {agent}" for agent in allow)
        blocks.append(f"{agents}\nAllow: /")
    return "\n\n".join(blocks) + "\n" if blocks else ""


def parse_robots_txt(content: str) -> dict[str, list[str]]:
    rules: dict[str, list[str]] = {}
    pending_agents: list[str] = []
    current: list[list[str]] = []

    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()

        if key == "user-agent":
            if current and not pending_agents:
                current = []
            pending_agents.append(value)
            current.append(rules.setdefault(value, []))
        elif key in ("disallow", "allow") and value:
            for bucket in current:
                bucket.append(f"{key}:{value}")
            pending_agents = []

    return rules
