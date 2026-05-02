from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CrawlerInfo:
    pattern: str
    url: str
    description: str
    tags: tuple[str, ...]


def load_database(path: str | Path) -> list[CrawlerInfo]:
    raw = json.loads(Path(path).read_text())
    return [
        CrawlerInfo(pattern.replace("\\/", "/"), url, description, tuple(tags))
        for pattern, url, description, tags in raw
    ]


@lru_cache(maxsize=1)
def _index(path: str) -> tuple[list[CrawlerInfo], dict[str, list[int]]]:
    entries = load_database(path)
    buckets: dict[str, list[int]] = {}
    for index, entry in enumerate(entries):
        key = entry.pattern.lower()[:3]
        buckets.setdefault(key, []).append(index)
    return entries, buckets


def crawler_info(user_agent: str, path: str) -> CrawlerInfo | None:
    entries, buckets = _index(path)
    for index in range(len(user_agent) - 2):
        for entry_index in buckets.get(user_agent[index : index + 3].lower(), ()):
            entry = entries[entry_index]
            if entry.pattern in user_agent:
                return entry
    return None


def crawlers_with_tag(tag: str, path: str) -> list[CrawlerInfo]:
    entries, _ = _index(path)
    return [entry for entry in entries if tag in entry.tags]
