from pathlib import Path

import pytest

from is_crawler import (
    __version__,
    crawler_has_tag,
    crawler_info,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name):
    return [l.strip() for l in (FIXTURES / name).read_text().splitlines() if l.strip()]


def test_version():
    assert __version__ == "1.1.2"


def test_all_exports():
    import is_crawler as mod

    assert set(mod.__all__) == {
        "is_crawler",
        "crawler_name",
        "crawler_version",
        "crawler_url",
        "crawler_signals",
        "crawler_info",
        "crawler_has_tag",
        "CrawlerInfo",
        "__version__",
    }


def test_crawler_signals_returns_matched_names():
    assert "bot_signal" in crawler_signals("Googlebot/2.1")
    assert "no_browser_signature" in crawler_signals("Googlebot/2.1")
    assert (
        crawler_signals(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        == []
    )
    assert "known_tool" in crawler_signals("Lighthouse")
    assert "bare_compatible" in crawler_signals("Mozilla/5.0 (compatible; MyBot/1.0)")


@pytest.mark.parametrize(
    ("ua", "expected"),
    [
        (
            "AdsBot-Google (+http://www.google.com/adsbot.html)",
            "AdsBot-Google",
        ),
        (
            "Caliperbot/1.0 (+http://www.conductor.com/caliperbot)",
            "Caliperbot",
        ),
        ("AdsBot-Google-Mobile-Apps", "AdsBot-Google-Mobile-Apps"),
        ("Mozilla/5.0 (compatible; BitSightBot/1.0)", "BitSightBot"),
        (
            "Mozilla/5.0 (compatible; YandexVideoParser/1.0; +http://yandex.com/bots)",
            "YandexVideoParser",
        ),
        (
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) Speedy Spider (http://www.entireweb.com/about/search_tech/speedy_spider/)",
            "Speedy Spider",
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36 PingdomPageSpeed/1.0 (pingbot/2.0; +http://www.pingdom.com/)",
            "PingdomPageSpeed",
        ),
        (
            "NewsBlur Feed Fetcher - 1 subscriber - http://www.newsblur.com/site/0000000/webpage (Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15)",
            "NewsBlur Feed Fetcher",
        ),
    ],
)
def test_crawler_name_extracts_expected_name(ua, expected):
    assert crawler_name(ua) == expected


def test_crawler_url_extracts_url():
    assert (
        crawler_url("Googlebot/2.1 (+http://www.google.com/bot.html)")
        == "http://www.google.com/bot.html"
    )
    assert (
        crawler_url(
            "NewsBlur Feed Fetcher - 1 subscriber - http://www.newsblur.com/site/0"
        )
        == "http://www.newsblur.com/site/0"
    )
    assert (
        crawler_url(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        is None
    )


def test_crawler_name_returns_none_for_empty_non_mozilla_ua():
    assert crawler_name("") is None


def test_crawler_name_returns_single_bot_hint_in_mozilla_ua():
    assert (
        crawler_name("Mozilla/5.0 AppleWebKit/537.36 FooBot Safari/537.36") == "FooBot"
    )


def test_crawler_name_returns_none_for_known_browser_tokens_only():
    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 "
        "Chrome/59.0.3071.109 Safari/537.36"
    )
    assert crawler_name(ua) is None


@pytest.mark.parametrize(
    ("ua", "expected"),
    [
        ("curl/7.64.1", "7.64.1"),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.3478.1649 "
            "Mobile Safari/537.36; Bytespider",
            None,
        ),
        ("Mozilla/5.0 (compatible; Miniflux/2.0.10; +https://miniflux.net)", "2.0.10"),
        (
            "Mozilla/5.0 (compatibl$; Miniflux/2.0.x-dev; +https://miniflux.app)",
            "2.0.x-dev",
        ),
        ("Googlebot/2.1 (+http://www.google.com/bot.html)", "2.1"),
        (
            "Mozilla/5.0 (compatible; heritrix/3.1.1 +http://places.tomtom.com/crawlerinfo)",
            "3.1.1",
        ),
        (
            "Mozilla/5.0 (compatible; Daum/4.1; +http://cs.daum.net/faq/15/4118.html?faqId=28966)",
            "4.1",
        ),
        (
            "Mozilla/5.0 (compatible; AndersPinkBot/1.0; +http://anderspink.com/bot.html)",
            "1.0",
        ),
        (
            "Mozilla/5.0 (compatible; WPScan; +https://wpscan.com/wordpress-security-scanner)",
            None,
        ),
    ],
)
def test_crawler_version_extracts_expected_version(ua, expected):
    assert crawler_version(ua) == expected


# --- bot signal regex ---


@pytest.mark.parametrize(
    "ua",
    [
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; bingbot/2.0)",
        "Apache-HttpClient/4.5 (crawling service)",
        "MySpider/1.0",
        "web-scraper/0.3",
        "DataFetcher/1.0",
        "PortScanner/2.0",
        "site-indexer v3",
        "LinkPreview/1.0",
        "Slurp/3.0",
        "archive.org_bot/1.0",
        "HeadlessChrome/90.0",
        "SomeBot (+https://example.com)",
        "checker (+http://example.com/info)",
        "agent@crawler.example.com",
    ],
)
def test_bot_signal_detected(ua):
    assert is_crawler(ua) is True


# --- browser sign keeps it non-crawler (when nothing else triggers) ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Opera/9.80 (Windows NT 6.1) Presto/2.12.388 Version/12.18",
        "Links (2.28; Linux x86_64; GNU C)",
        "Lynx/2.8.9rel.1 libwww-FM/2.14",
    ],
)
def test_real_browser_not_crawler(ua):
    assert is_crawler(ua) is False


# --- no browser sign → crawler ---


@pytest.mark.parametrize(
    "ua",
    [
        "curl/7.68.0",
        "python-requests/2.28.0",
        "Java/1.8.0_292",
        "",
    ],
)
def test_no_browser_sign_is_crawler(ua):
    assert is_crawler(ua) is True


# --- bare compat (compatible; ...) without OS tokens ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        "Mozilla/5.0 (compatible; SemrushBot/7; +http://www.semrush.com/bot.html)",
    ],
)
def test_bare_compat_is_crawler(ua):
    assert is_crawler(ua) is True


def test_compat_with_os_not_bare():
    """(compatible; MSIE 10.0; Windows ...) should NOT trigger bare compat."""
    ua = "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"
    assert is_crawler(ua) is False


# --- known tool regex ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (X11; Linux x86_64) Lighthouse",
        "Mozilla/5.0 (Windows NT 10.0) Playwright/1.40",
        "Mozilla/5.0 (Windows NT 10.0) Selenium/4.0",
        "Wget/1.21",
        "Nikto/2.1.6",
        "sqlmap/1.7",
        "Nmap Scripting Engine",
        "Pingdom.com_bot_version_1.4",
        "HTTrack/3.49",
        "Mozilla/5.0 (Windows NT 10.0) Google-Safety/1.0",
        "Mozilla/5.0 (Windows NT 10.0) Google Favicon",
        "Mozilla/5.0 (Windows NT 10.0) Google Ads Bot",
        "Mozilla/5.0 (Windows NT 10.0) Google-Extended",
        "Mozilla/5.0 (Windows NT 10.0) by example.com crawl",
        "example.com/crawler",
        "Mozilla/5.0 (Windows NT 10.0; test-agent) Gecko/20100101",
    ],
)
def test_known_tool_is_crawler(ua):
    assert is_crawler(ua) is True


# --- fixture-based tests ---


@pytest.mark.parametrize("ua", _load_fixture("crawler_user_agents.txt"))
def test_fixture_crawler_detected(ua):
    assert is_crawler(ua) is True


@pytest.mark.parametrize("ua", _load_fixture("browser_user_agents.txt"))
def test_fixture_browser_not_detected(ua):
    assert is_crawler(ua) is False


# --- crawler_info ---

_GOOGLEBOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"
_BINGBOT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
_LINKEDINBOT = "LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)"


def test_crawler_info_returns_none_for_browser():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    assert crawler_info(ua) is None


def test_crawler_info_googlebot():
    info = crawler_info(_GOOGLEBOT)
    assert info is not None
    assert info.url == "http://www.google.com/bot.html"
    assert info.description == "Google's main web crawling bot for search indexing"
    assert info.tags == ["search-engine"]


def test_crawler_info_bingbot():
    info = crawler_info(_BINGBOT)
    assert info is not None
    assert info.url == "http://www.bing.com/bingbot.htm"
    assert info.description == "Microsoft's web crawling bot for Bing search indexing"
    assert info.tags == ["search-engine"]


def test_crawler_info_linkedinbot():
    info = crawler_info(_LINKEDINBOT)
    assert info is not None
    assert info.url == ""
    assert (
        info.description
        == "LinkedIn's bot for crawling professional content and profiles"
    )
    assert info.tags == ["social-preview"]


# --- crawler_has_tag ---


def test_crawler_has_tag_single_string():
    assert crawler_has_tag(_GOOGLEBOT, "search-engine") is True
    assert crawler_has_tag(_GOOGLEBOT, "ai-crawler") is False


def test_crawler_has_tag_list():
    assert crawler_has_tag(_GOOGLEBOT, ["search-engine", "ai-crawler"]) is True
    assert crawler_has_tag(_GOOGLEBOT, ["ai-crawler", "scanner"]) is False


def test_crawler_has_tag_returns_false_for_browser():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    assert crawler_has_tag(ua, "search-engine") is False


# --- callable module ---


def test_module_callable():
    import is_crawler as mod

    assert callable(mod)
    assert mod("Googlebot/2.1") is True
    assert (
        mod(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        is False
    )


def test_module_callable_matches_function():
    import is_crawler as mod

    ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
    assert mod(ua) == mod.is_crawler(ua)  # type: ignore[reportCallIssue]
