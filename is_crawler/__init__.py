from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from is_crawler.database import (
        CrawlerInfo,
        assert_crawler,
        build_ai_txt,
        build_robots_txt,
        crawler_has_tag,
        crawler_info,
        is_academic,
        is_advertising,
        is_ai_crawler,
        is_ai_fetcher,
        is_archiver,
        is_bad_crawler,
        is_browser_automation,
        is_feed_reader,
        is_good_crawler,
        is_http_library,
        is_monitoring,
        is_scanner,
        is_search_engine,
        is_seo,
        is_social_preview,
        iter_crawlers,
        robots_agents_for_tags,
    )
    from is_crawler.detection import (
        crawler_contact,
        crawler_name,
        crawler_signals,
        crawler_url,
        crawler_version,
        is_crawler,
    )

try:
    __version__ = version("is-crawler")
except PackageNotFoundError:
    __version__ = "0+unknown"

_DETECTION = frozenset(
    {
        "is_crawler",
        "crawler_name",
        "crawler_version",
        "crawler_url",
        "crawler_contact",
        "crawler_signals",
    }
)

__all__ = [
    "is_crawler",
    "crawler_name",
    "crawler_version",
    "crawler_url",
    "crawler_contact",
    "crawler_signals",
    "crawler_info",
    "assert_crawler",
    "crawler_has_tag",
    "is_search_engine",
    "is_ai_crawler",
    "is_ai_fetcher",
    "is_seo",
    "is_social_preview",
    "is_advertising",
    "is_archiver",
    "is_feed_reader",
    "is_monitoring",
    "is_scanner",
    "is_academic",
    "is_http_library",
    "is_browser_automation",
    "is_good_crawler",
    "is_bad_crawler",
    "iter_crawlers",
    "robots_agents_for_tags",
    "build_robots_txt",
    "build_ai_txt",
    "CrawlerInfo",
    "__version__",
]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module 'is_crawler' has no attribute {name!r}")
    module = "is_crawler.detection" if name in _DETECTION else "is_crawler.database"
    value = getattr(import_module(module), name)
    globals()[name] = value
    return value
