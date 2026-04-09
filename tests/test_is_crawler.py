from pathlib import Path

import pytest

from is_crawler import __version__, crawler_signals, is_crawler

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name):
    return [l.strip() for l in (FIXTURES / name).read_text().splitlines() if l.strip()]


def test_version():
    assert __version__ == "1.0.3"


def test_all_exports():
    import is_crawler as mod

    assert set(mod.__all__) == {"is_crawler", "crawler_signals", "__version__"}


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
