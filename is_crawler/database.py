from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property, lru_cache
import json
from pathlib import Path
import re
from typing import NamedTuple

from is_crawler.detection import is_crawler

_CACHE = 32768
_CHUNK = 48

_custom_rows: dict[str, list] = {}
_custom_chunk: "_Chunk | None" = None


class CrawlerInfo(NamedTuple):
    url: str
    description: str
    tags: tuple[str, ...]
    rdns: tuple[str, ...]


@dataclass
class _Chunk:
    rows: list

    @cached_property
    def combined(self) -> re.Pattern:
        return re.compile("|".join(f"(?:{p})" for p, *_ in self.rows))

    @cached_property
    def entries(self) -> list[tuple[re.Pattern, CrawlerInfo]]:
        return [
            (re.compile(p), CrawlerInfo(u, d, tuple(t), tuple(r)))
            for p, u, d, t, r in self.rows
        ]

    def match(self, user_agent: str) -> CrawlerInfo | None:
        if not self.combined.search(user_agent):
            return None
        for pattern, info in self.entries:
            if pattern.search(user_agent):
                return info
        return None  # pragma: no cover


@lru_cache(maxsize=1)
def _load_chunks() -> list[_Chunk]:
    path = Path(__file__).parent / "crawlers.min.json"
    with path.open(encoding="utf-8") as f:
        entries = json.load(f)
    rows = [
        [
            e.get("pattern", ""),
            e.get("url", ""),
            e.get("description", ""),
            e.get("tags") or [],
            e.get("rdns") or [],
        ]
        for e in entries
    ]
    return [_Chunk(rows[i : i + _CHUNK]) for i in range(0, len(rows), _CHUNK)]


@lru_cache(maxsize=_CACHE)
def crawler_info(user_agent: str) -> CrawlerInfo | None:
    if _custom_chunk is not None:
        custom = _custom_chunk.match(user_agent)
        if custom is not None:
            return custom

    if not is_crawler(user_agent):
        return None

    for chunk in _load_chunks():
        info = chunk.match(user_agent)
        if info is not None:
            return info

    return None  # pragma: no cover


def _rebuild_custom() -> None:
    global _custom_chunk
    _custom_chunk = _Chunk(list(_custom_rows.values())) if _custom_rows else None
    crawler_info.cache_clear()


def register_crawler(
    name: str,
    pattern: str,
    *,
    url: str = "",
    description: str = "",
    tags: Iterable[str] = (),
    rdns: Iterable[str] = (),
) -> None:
    """Register a custom crawler pattern, matched before the bundled DB."""
    re.compile(pattern)
    _custom_rows[name] = [pattern, url, description, list(tags), list(rdns)]
    _rebuild_custom()


def unregister_crawler(name: str) -> bool:
    """Remove a custom pattern by name. Returns whether it existed."""
    if _custom_rows.pop(name, None) is None:
        return False
    _rebuild_custom()
    return True


def clear_custom_crawlers() -> None:
    """Remove all custom crawler patterns."""
    if _custom_rows:
        _custom_rows.clear()
        _rebuild_custom()


@contextmanager
def custom_crawlers(*entries: dict):
    """Temporarily register crawlers; restore the prior registry on exit."""
    global _custom_rows
    saved = {name: list(row) for name, row in _custom_rows.items()}
    try:
        for entry in entries:
            register_crawler(**entry)
        yield
    finally:
        _custom_rows = saved
        _rebuild_custom()


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


def is_ai_fetcher(user_agent: str) -> bool:
    return crawler_has_tag(user_agent, "ai-fetcher")


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
        for pattern, url, description, tags, rdns in chunk.rows:
            name = _robots_name(pattern)
            if name:
                yield (
                    CrawlerInfo(url, description, tuple(tags or ()), tuple(rdns or ())),
                    name,
                )


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

    disallowed_agents = set(robots_agents_for_tags(disallow)) if disallow else set()
    for agent in disallowed_agents:
        directives.setdefault(agent, []).append(f"Disallow: {path}")

    for agent in robots_agents_for_tags(allow) if allow else []:
        if agent not in disallowed_agents:
            directives.setdefault(agent, []).append(f"Allow: {path}")

    for rule_path, rule_tags in rules:
        for agent in robots_agents_for_tags(rule_tags):
            directives.setdefault(agent, []).append(f"Disallow: {rule_path}")

    return directives


def _group_by_directives(directives: dict[str, list[str]], header: str) -> list[str]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for agent, lines in directives.items():
        groups.setdefault(tuple(lines), []).append(agent)

    blocks = []
    for lines, agents in groups.items():
        agent_lines = "\n".join(f"{header}: {agent}" for agent in agents)
        blocks.append(f"{agent_lines}\n" + "\n".join(lines))
    return blocks


def build_robots_txt(
    disallow: str | Iterable[str] = (),
    allow: str | Iterable[str] = (),
    path: str = "/",
    rules: Iterable[tuple[str, str | Iterable[str]]] = (),
) -> str:
    directives = _agent_directives(disallow, allow, path, rules)
    if not directives:
        return ""
    return "\n\n".join(_group_by_directives(directives, "User-agent")) + "\n"


def build_ai_txt(disallow: str | Iterable[str] = "ai-crawler") -> str:
    agents = robots_agents_for_tags(disallow)
    if not agents:
        return ""
    agent_lines = "\n".join(f"User-Agent: {agent}" for agent in agents)
    return f"{agent_lines}\nDisallow: /\n"
