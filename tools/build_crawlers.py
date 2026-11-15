import json
from pathlib import Path
from urllib.request import urlopen

SOURCE = "https://raw.githubusercontent.com/tn3w/uaid/main/crawlers.json"
TARGET = Path(__file__).parents[1] / "is_crawler" / "crawlers.min.json"
FIELDS = ("match", "url", "description", "tags", "rdns")


def cased(part: str, instances: list[str]) -> str:
    for instance in instances:
        start = instance.lower().find(part)
        if start >= 0:
            return instance[start : start + len(part)]
    return part


def robots_name(crawler: dict) -> str | None:
    rule = crawler["match"][0]
    part = rule if isinstance(rule, str) else max(rule, key=len)
    name = cased(part.lstrip("^"), crawler["instances"]).strip("/-. \t")
    if not name or "/" in name:
        return None
    return name


def build(crawler: dict) -> dict:
    entry = {key: crawler[key] for key in FIELDS if key in crawler}
    name = robots_name(crawler)
    if name:
        entry["name"] = name
    return entry


def main() -> None:
    with urlopen(SOURCE, timeout=60) as response:
        crawlers = json.load(response)
    entries = [build(crawler) for crawler in crawlers]
    TARGET.write_text(json.dumps(entries, separators=(",", ":")))
    print(f"{len(entries)} crawlers -> {TARGET}")


if __name__ == "__main__":
    main()
