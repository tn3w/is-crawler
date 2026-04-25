from collections import Counter
import json
from pathlib import Path
import re

import pytest

from is_crawler import (
    CrawlerInfo,
    _robots_name,
    crawler_has_tag,
    crawler_info,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_academic,
    is_advertising,
    is_ai_crawler,
    is_archiver,
    is_bad_crawler,
    is_browser_automation,
    is_crawler,
    is_feed_reader,
    is_good_crawler,
    is_http_library,
    is_monitoring,
    is_scanner,
    is_search_engine,
    is_seo,
    is_social_preview,
    iter_crawlers,
)

_DATA = json.loads(
    (Path(__file__).parents[1] / "is_crawler" / "crawler-user-agents.json").read_text()
)
_KNOWN_TAGS = {
    "academic",
    "advertising",
    "ai-crawler",
    "archiver",
    "browser-automation",
    "feed-reader",
    "http-library",
    "monitoring",
    "scanner",
    "search-engine",
    "seo",
    "social-preview",
}
_TAG_TO_FN = {
    "academic": is_academic,
    "advertising": is_advertising,
    "ai-crawler": is_ai_crawler,
    "archiver": is_archiver,
    "browser-automation": is_browser_automation,
    "feed-reader": is_feed_reader,
    "http-library": is_http_library,
    "monitoring": is_monitoring,
    "scanner": is_scanner,
    "search-engine": is_search_engine,
    "seo": is_seo,
    "social-preview": is_social_preview,
}


def _samples() -> list[tuple[str, str, str, tuple[str, ...]]]:
    out = []
    for pattern, url, desc, tags in _DATA:
        name = _robots_name(pattern)
        if not name:
            continue
        out.append((pattern, name, url, tuple(tags)))
    return out


_SAMPLES = _samples()


# --- dataset shape ---


def test_dataset_loads_and_nonempty():
    assert len(_DATA) > 1000


def test_dataset_rows_have_four_fields():
    bad = [r for r in _DATA if len(r) != 4]
    assert not bad


def test_dataset_pattern_is_nonempty_string():
    bad = [r for r in _DATA if not isinstance(r[0], str) or not r[0]]
    assert not bad


def test_dataset_url_is_string():
    bad = [r for r in _DATA if not isinstance(r[1], str)]
    assert not bad


def test_dataset_description_is_nonempty():
    bad = [r for r in _DATA if not isinstance(r[2], str) or not r[2].strip()]
    assert not bad, f"{len(bad)} rows missing description"


def test_dataset_tags_are_lists():
    bad = [r for r in _DATA if not isinstance(r[3], list) or not r[3]]
    assert not bad


def test_dataset_tags_within_known_set():
    seen = {t for r in _DATA for t in r[3]}
    unknown = seen - _KNOWN_TAGS
    assert not unknown, f"unknown tags: {unknown}"


def test_dataset_no_duplicate_patterns():
    counts = Counter(r[0] for r in _DATA)
    dupes = {p: c for p, c in counts.items() if c > 1}
    assert not dupes, f"duplicate patterns: {list(dupes)[:5]}"


def test_dataset_patterns_compile():
    bad = []
    for r in _DATA:
        try:
            re.compile(r[0])
        except re.error as e:
            bad.append((r[0], str(e)))
    assert not bad, f"invalid regex: {bad[:3]}"


def test_dataset_urls_mostly_well_formed():
    bad = [r[1] for r in _DATA if r[1] and not r[1].startswith(("http://", "https://"))]
    rate = (len(_DATA) - len(bad)) / len(_DATA)
    assert rate >= 0.99, f"only {rate:.2%} well-formed; bad sample: {bad[:5]}"


# --- robots_name extraction ---


def test_robots_name_resolves_for_most_rows():
    resolved = sum(1 for r in _DATA if _robots_name(r[0]))
    rate = resolved / len(_DATA)
    assert rate >= 0.95, f"{rate:.2%} resolvable to robots name"


# --- detection on real patterns ---


@pytest.fixture(scope="module")
def synthesized_uas() -> list[tuple[str, tuple[str, ...]]]:
    return [(name, tags) for _, name, _, tags in _SAMPLES]


def test_every_known_name_classified_as_crawler(synthesized_uas):
    misses = [name for name, _ in synthesized_uas if not is_crawler(name)]
    rate = (len(synthesized_uas) - len(misses)) / len(synthesized_uas)
    assert rate >= 0.97, f"{rate:.2%} detected; misses sample: {misses[:5]}"


def test_known_name_with_version_classified(synthesized_uas):
    misses = [n for n, _ in synthesized_uas if not is_crawler(f"{n}/1.0")]
    rate = (len(synthesized_uas) - len(misses)) / len(synthesized_uas)
    assert rate >= 0.98, f"{rate:.2%}; misses sample: {misses[:5]}"


def test_known_name_with_url_suffix_classified(synthesized_uas):
    template = "Mozilla/5.0 (compatible; {}/1.0; +http://example.com/bot)"
    misses = [n for n, _ in synthesized_uas if not is_crawler(template.format(n))]
    rate = (len(synthesized_uas) - len(misses)) / len(synthesized_uas)
    assert rate >= 0.98, f"{rate:.2%}; misses sample: {misses[:5]}"


# --- crawler_info round-trips ---


def test_crawler_info_lookup_round_trip(synthesized_uas):
    misses = []
    for name, _ in synthesized_uas:
        info = crawler_info(f"{name}/1.0")
        if info is None:
            misses.append(name)
    rate = (len(synthesized_uas) - len(misses)) / len(synthesized_uas)
    assert rate >= 0.97, f"info lookup {rate:.2%}; sample: {misses[:5]}"


def test_crawler_info_returns_known_type():
    info = crawler_info("Googlebot/2.1")
    assert isinstance(info, CrawlerInfo)
    assert info.tags
    assert isinstance(info.tags, tuple)


def test_crawler_info_tags_are_subset_of_known():
    seen = set()
    for info, _ in iter_crawlers():
        seen.update(info.tags)
    assert seen <= _KNOWN_TAGS


# --- tag predicates align with crawler_info ---


def test_tag_predicates_match_dataset(synthesized_uas):
    mismatches = []
    for name, expected_tags in synthesized_uas[:300]:
        ua = f"{name}/1.0"
        info = crawler_info(ua)
        if info is None:
            continue
        for tag, fn in _TAG_TO_FN.items():
            expected = tag in info.tags
            actual = fn(ua)
            if expected != actual:
                mismatches.append((name, tag, expected, actual))
    assert not mismatches, f"{len(mismatches)} mismatches, e.g. {mismatches[:3]}"


def test_good_bad_partition_disjoint_or_via_tags():
    for info, _ in list(iter_crawlers())[:500]:
        good_tags = {
            "search-engine",
            "social-preview",
            "feed-reader",
            "archiver",
            "academic",
        }
        bad_tags = {"ai-crawler", "scanner", "http-library", "browser-automation", "seo"}
        if good_tags & set(info.tags) and bad_tags & set(info.tags):
            continue


def test_is_good_or_bad_for_categorized_uas(synthesized_uas):
    for name, tags in synthesized_uas[:200]:
        ua = f"{name}/1.0"
        info = crawler_info(ua)
        if info is None:
            continue
        if {
            "search-engine",
            "social-preview",
            "feed-reader",
            "archiver",
            "academic",
        } & set(info.tags):
            assert is_good_crawler(ua), f"{name} expected good"
        if {"ai-crawler", "scanner", "http-library", "browser-automation", "seo"} & set(
            info.tags
        ):
            assert is_bad_crawler(ua), f"{name} expected bad"


# --- specific high-value crawlers ---


_KEY_CRAWLERS = [
    ("Googlebot/2.1 (+http://www.google.com/bot.html)", "Googlebot", "search-engine"),
    (
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "bingbot",
        "search-engine",
    ),
    (
        "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
        "YandexBot",
        "search-engine",
    ),
    (
        "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)",
        "DuckDuckBot",
        "search-engine",
    ),
    (
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "Baiduspider",
        "search-engine",
    ),
    (
        "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)",
        "GPTBot",
        "ai-crawler",
    ),
    (
        "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
        "ClaudeBot",
        "ai-crawler",
    ),
    (
        "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
        "PerplexityBot",
        "ai-crawler",
    ),
    (
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        "AhrefsBot",
        "seo",
    ),
    (
        "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
        "SemrushBot",
        "seo",
    ),
    (
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "facebookexternalhit",
        "social-preview",
    ),
    ("Twitterbot/1.0", "Twitterbot", "social-preview"),
    (
        "LinkedInBot/1.0 (compatible; Mozilla/5.0; +http://www.linkedin.com)",
        "LinkedInBot",
        "social-preview",
    ),
    (
        "Mozilla/5.0 (compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)",
        "UptimeRobot",
        "monitoring",
    ),
    ("Mozilla/5.00 (Nikto/2.1.6) (Evasions:None) (Test:000003)", "Nikto", "scanner"),
    ("python-requests/2.28.0", "python-requests", "http-library"),
    ("curl/7.64.1", "curl", "http-library"),
    ("Wget/1.21", "Wget", "http-library"),
    (
        "Mozilla/5.0 (compatible; archive.org_bot; +http://www.archive.org/details/archive.org_bot)",
        "archive.org_bot",
        "archiver",
    ),
    ("Feedly/1.0 (+http://www.feedly.com/fetcher.html)", "Feedly", "feed-reader"),
    (
        "AdsBot-Google (+http://www.google.com/adsbot.html)",
        "AdsBot-Google",
        "advertising",
    ),
]


@pytest.mark.parametrize("ua,name,tag", _KEY_CRAWLERS)
def test_key_crawler_detected(ua, name, tag):
    assert is_crawler(ua), ua


@pytest.mark.parametrize("ua,name,tag", _KEY_CRAWLERS)
def test_key_crawler_name(ua, name, tag):
    assert crawler_name(ua) == name


@pytest.mark.parametrize("ua,name,tag", _KEY_CRAWLERS)
def test_key_crawler_tag(ua, name, tag):
    info = crawler_info(ua)
    assert info is not None, ua
    assert tag in info.tags, f"{name}: expected {tag} in {info.tags}"


# --- adversarial / edge cases ---


_BROWSER_NEGATIVES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Opera/9.80 (Windows NT 6.1) Presto/2.12.388 Version/12.18",
    "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
]


@pytest.mark.parametrize("ua", _BROWSER_NEGATIVES)
def test_real_browsers_not_crawlers(ua):
    assert is_crawler(ua) is False, ua


@pytest.mark.parametrize("ua", _BROWSER_NEGATIVES)
def test_real_browsers_have_no_crawler_info(ua):
    assert crawler_info(ua) is None


@pytest.mark.parametrize("ua", _BROWSER_NEGATIVES)
def test_real_browsers_no_tag_predicates_fire(ua):
    for fn in _TAG_TO_FN.values():
        assert fn(ua) is False, f"{fn.__name__} fired on {ua}"


@pytest.mark.parametrize(
    "ua",
    [
        "",
        " ",
        "\n",
        "\t",
        "-",
        "?",
        "Mozilla",
        "Mozilla/5.0",
    ],
)
def test_degenerate_inputs_safe(ua):
    is_crawler(ua)
    crawler_name(ua)
    crawler_version(ua)
    crawler_url(ua)
    crawler_info(ua)
    crawler_signals(ua)


def test_extremely_long_ua():
    ua = "Googlebot/2.1 " + "x" * 10000
    assert is_crawler(ua) is True


def test_unicode_ua_safe():
    is_crawler("Mozilla/5.0 (compatible; テストBot/1.0)")
    crawler_name("курсорBot/1.0")


def test_repeated_calls_cached_consistent():
    ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
    a = crawler_info(ua)
    b = crawler_info(ua)
    assert a is b


# --- crawler_signals on dataset ---


def test_signals_nonempty_for_dataset_samples(synthesized_uas):
    empty = [n for n, _ in synthesized_uas[:300] if not crawler_signals(f"{n}/1.0")]
    rate = (300 - len(empty)) / 300
    assert rate >= 0.95, f"signals empty for {rate:.2%}; sample: {empty[:5]}"


# --- crawler_has_tag iterable shapes ---


def test_has_tag_accepts_set():
    ua = "Googlebot/2.1"
    assert crawler_has_tag(ua, {"search-engine"}) is True


def test_has_tag_accepts_tuple():
    ua = "Googlebot/2.1"
    assert crawler_has_tag(ua, ("ai-crawler", "search-engine")) is True


def test_has_tag_accepts_generator():
    ua = "Googlebot/2.1"
    assert crawler_has_tag(ua, (t for t in ["search-engine"])) is True


def test_has_tag_empty_iterable_false():
    assert crawler_has_tag("Googlebot/2.1", []) is False
