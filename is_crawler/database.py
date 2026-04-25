from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import NamedTuple

_CACHE = 32768
_CHUNK = 48


class CrawlerInfo(NamedTuple):
    url: str
    description: str
    tags: tuple[str, ...]


@dataclass
class _Chunk:
    rows: list
    _combined: re.Pattern | None = field(default=None, init=False, repr=False)
    _entries: list | None = field(default=None, init=False, repr=False)

    def match(self, user_agent: str) -> CrawlerInfo | None:
        if self._combined is None:
            self._combined = re.compile("|".join(f"(?:{p})" for p, *_ in self.rows))

        if not self._combined.search(user_agent):
            return None

        if self._entries is None:
            self._entries = [
                (re.compile(p), CrawlerInfo(u, d, tuple(t))) for p, u, d, t in self.rows
            ]

        for pattern, info in self._entries:
            if pattern.search(user_agent):
                return info
        return None  # pragma: no cover


_chunks: list[_Chunk] | None = None


def _load_chunks() -> list[_Chunk]:
    global _chunks
    if _chunks is not None:
        return _chunks

    path = Path(__file__).parent / "crawler-user-agents.json"
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)

    _chunks = [_Chunk(rows[i : i + _CHUNK]) for i in range(0, len(rows), _CHUNK)]
    return _chunks


@lru_cache(maxsize=_CACHE)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    from is_crawler import is_crawler

    if not is_crawler(user_agent):
        return None

    for chunk in _load_chunks():
        info = chunk.match(user_agent)
        if info is not None:
            return info

    return None  # pragma: no cover


def assert_crawler(user_agent: str) -> CrawlerInfo:
    info = crawler_info(user_agent)
    if info is None:
        raise ValueError(f"not a known crawler: {user_agent!r}")
    return info


def crawler_has_tag(user_agent: str, tags: str | Iterable[str]) -> bool:
    info = crawler_info(user_agent)
    if not info:
        return False
    return bool(_as_set(tags) & set(info.tags))


_GOOD_TAGS = frozenset(
    {"search-engine", "social-preview", "feed-reader", "archiver", "academic"}
)
_BAD_TAGS = frozenset(
    {"ai-crawler", "scanner", "http-library", "browser-automation", "seo"}
)


def is_search_engine(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "search-engine")


def is_ai_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "ai-crawler")


def is_seo(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "seo")


def is_social_preview(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "social-preview")


def is_advertising(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "advertising")


def is_archiver(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "archiver")


def is_feed_reader(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "feed-reader")


def is_monitoring(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "monitoring")


def is_scanner(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "scanner")


def is_academic(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "academic")


def is_http_library(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "http-library")


def is_browser_automation(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "browser-automation")


def is_good_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, _GOOD_TAGS)


def is_bad_crawler(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, _BAD_TAGS)


_ROBOTS_CHARCLASS = re.compile(r"\[([^\]]+)\]")
_ROBOTS_ESCAPE = re.compile(r"\\(.)")
_ROBOTS_META = re.compile(r"[(|$?*+]")


def _robots_name(pattern: str) -> str | None:
    name = _ROBOTS_CHARCLASS.sub(lambda m: m.group(1)[0], pattern)
    name = _ROBOTS_ESCAPE.sub(r"\1", name).lstrip("^")
    name = _ROBOTS_META.split(name)[0].strip("/-. \t")
    if not name or "://" in name or "/" in name:
        return None
    return name


def iter_crawlers() -> Iterable[tuple[CrawlerInfo, str]]:
    for chunk in _load_chunks():
        for pattern, url, description, tags in chunk.rows:
            name = _robots_name(pattern)
            if name:
                yield CrawlerInfo(url, description, tuple(tags or ())), name


def robots_agents_for_tags(tags: str | Iterable[str]) -> list[str]:
    wanted = _as_set(tags)
    return sorted({name for info, name in iter_crawlers() if wanted & set(info.tags)})


def _as_set(tags: str | Iterable[str]) -> set[str]:
    return {tags} if isinstance(tags, str) else set(tags)


def _agent_directives(
    disallow: str | Iterable[str],
    allow: str | Iterable[str],
    path: str,
    rules: Iterable[tuple[str, str | Iterable[str]]],
) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}

    for agent in robots_agents_for_tags(disallow) if disallow else []:
        directives.setdefault(agent, []).append(f"Disallow: {path}")

    for agent in robots_agents_for_tags(allow) if allow else []:
        directives.setdefault(agent, []).append(f"Allow: {path}")

    for rule_path, rule_tags in rules:
        for agent in robots_agents_for_tags(rule_tags):
            directives.setdefault(agent, []).append(f"Disallow: {rule_path}")

    return directives


def build_robots_txt(
    disallow: str | Iterable[str] = (),
    allow: str | Iterable[str] = (),
    path: str = "/",
    rules: Iterable[tuple[str, str | Iterable[str]]] = (),
) -> str:
    directives = _agent_directives(disallow, allow, path, rules)
    if not directives:
        return ""

    blocks = [
        f"User-agent: {agent}\n" + "\n".join(lines) for agent, lines in directives.items()
    ]
    return "\n\n".join(blocks) + "\n"


def build_ai_txt(disallow: str | Iterable[str] = "ai-crawler") -> str:
    agents = robots_agents_for_tags(disallow)
    if not agents:
        return ""
    blocks = [f"User-Agent: {agent}\nDisallow: /" for agent in agents]
    return "\n\n".join(blocks) + "\n"
