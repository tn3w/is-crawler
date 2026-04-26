from pathlib import Path

import pytest

from is_crawler import (
    __version__,
    _bare_compat,
    _bot_signal,
    _browser,
    _email_like,
    _fetch_not_api,
    _find_word,
    _has_by_domain,
    _known_tool,
    _leading_domain,
    _semicolon_agent,
    _token_after,
    _url_in_ua,
    _word_char,
    _word_ends,
    crawler_contact,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[str]:
    return [
        line.strip()
        for line in (_FIXTURES / name).read_text().splitlines()
        if line.strip()
    ]


# --- module ---


def test_version():
    assert isinstance(__version__, str)


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
        "is_search_engine",
        "is_ai_crawler",
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
        "assert_crawler",
        "crawler_contact",
        "CrawlerInfo",
        "__version__",
    }


# --- primitives ---


def test_word_char():
    assert _word_char("a") and _word_char("0") and _word_char("_")
    assert not _word_char("-") and not _word_char(" ")


def test_word_ends_at_boundary():
    assert _word_ends("bot/1", 3)
    assert not _word_ends("bots", 3)
    assert _word_ends("bot", 3)


def test_find_word_match_and_miss():
    assert _find_word("foobot bar", "bot")
    assert not _find_word("foobots", "bot")
    assert not _find_word("nothing", "bot")


def test_fetch_not_api_variants():
    assert _fetch_not_api("datafetcher")
    assert not _fetch_not_api("fetchapi")
    assert not _fetch_not_api("nothing")


def test_email_like_valid():
    assert _email_like("agent@crawler.example.com")
    assert not _email_like("noatsign")
    assert not _email_like("@nodomain")
    assert not _email_like("a@x.5")


def test_token_after_stops_at_delimiter():
    end, token = _token_after("foo bar", 0)
    assert token == "foo" and end == 3


def test_crawler_contact_found():
    ua = "MyBot/1.0 (+https://example.com; contact@example.com)"
    assert crawler_contact(ua) == "contact@example.com"


def test_crawler_contact_invalid_at():
    assert crawler_contact("agent @nodomain") is None


def test_crawler_contact_none():
    assert crawler_contact("Mozilla/5.0 (Windows NT 10.0)") is None


# --- _bot_signal ---


@pytest.mark.parametrize(
    "ua",
    [
        "MySpider/1.0",
        "web-scraper/0.3",
        "DataFetcher/1.0",
        "PortScan/2.0",
        "site-indexer v3",
        "LinkPreview/1.0",
        "Slurp/3.0",
        "HeadlessChrome/90.0",
        "archive.org_bot/1.0",
        "Googlebot/2.1",
        "checker (+http://example.com)",
        "checker (+https://example.com)",
        "agent@crawler.example.com",
    ],
)
def test_bot_signal_true(ua):
    assert _bot_signal(ua)


def test_bot_signal_false():
    assert not _bot_signal("Mozilla/5.0 (Windows NT 10.0) Chrome/120")


# --- _known_tool ---


@pytest.mark.parametrize(
    "ua",
    [
        "Lighthouse",
        "Playwright/1.40",
        "Selenium/4.0",
        "Wget/1.21",
        "Nmap Scripting Engine",
        "Nikto/2.1.6",
        "sqlmap/1.7",
        "Pingdom.com_bot",
        "HTTrack/3.49",
        "Google Favicon",
        "Google-Safety/1.0",
        "Google Ads Bot",
        "Google-Extended",
        "Mozilla/5.0 by example.com crawl",
        "example.com/crawler",
        "Mozilla/5.0 (Windows NT 10.0; test-agent) Gecko/20100101",
    ],
)
def test_known_tool_true(ua):
    assert _known_tool(ua)


def test_known_tool_false():
    assert not _known_tool("Mozilla/5.0 Chrome/120 Safari/537.36")


def test_has_by_domain_at_start():
    assert _has_by_domain("by example.com")


def test_has_by_domain_mid_word_no_match():
    assert not _has_by_domain("nearby example.com")


def test_leading_domain_slash():
    assert _leading_domain("example.com/crawler")


def test_leading_domain_space():
    assert _leading_domain("example.com crawler")


def test_leading_domain_no_tld():
    assert not _leading_domain("localhost/foo")


def test_leading_domain_no_separator():
    assert not _leading_domain("example.com")


def test_semicolon_agent_paren():
    assert _semicolon_agent("; my-agent)")


def test_semicolon_agent_semicolon():
    assert _semicolon_agent("; my-agent;")


def test_semicolon_agent_no_match():
    assert not _semicolon_agent("; foobar)")


# --- _url_in_ua ---


@pytest.mark.parametrize(
    "ua",
    [
        "http://example.com",
        "SomeBot (+http://example.com)",
        "SomeBot;http://example.com",
        "Feed - http://example.com",
    ],
)
def test_url_in_ua_true(ua):
    assert _url_in_ua(ua)


def test_url_in_ua_false():
    assert not _url_in_ua("Mozilla/5.0 Chrome/120")
    assert not _url_in_ua("see http://example.com for info")


def test_url_in_ua_https_leading():
    assert _url_in_ua("https://example.com")


# --- _browser ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 Chrome/120",
        "AppleWebKit/537.36",
        "Gecko/20100101",
        "Trident/6.0",
        "Presto/2.12",
        "KHTML",
        "Links (2.28; Linux)",
        "Lynx/2.8.9",
        "Opera/9.80 (Windows)",
        "Mozilla/5.0 (Windows NT 10.0)",
        "Mozilla/5.0 (Macintosh; Intel)",
        "Mozilla/5.0 (X11; Linux)",
        "Mozilla/5.0 (Linux; Android)",
    ],
)
def test_browser_true(ua):
    assert _browser(ua)


def test_browser_false():
    assert not _browser("curl/7.68.0")


# --- _bare_compat ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (compatible; AhrefsBot/7.0)",
        "Mozilla/5.0 (compatible; MyBot/1.0)",
    ],
)
def test_bare_compat_true(ua):
    assert _bare_compat(ua)


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1)",
        "Mozilla/5.0 (compatible; Konqueror/4.0; Linux)",
        "Mozilla/5.0",
        "Mozilla/5.0 (compatible; MyBot/1.0",
    ],
)
def test_bare_compat_false(ua):
    assert not _bare_compat(ua)


# --- is_crawler ---


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
        "curl/7.68.0",
        "python-requests/2.28.0",
        "Java/1.8.0_292",
        "",
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        "Mozilla/5.0 (compatible; SemrushBot/7; +http://www.semrush.com/bot.html)",
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
def test_is_crawler_true(ua):
    assert is_crawler(ua) is True


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Opera/9.80 (Windows NT 6.1) Presto/2.12.388 Version/12.18",
        "Links (2.28; Linux x86_64; GNU C)",
        "Lynx/2.8.9rel.1 libwww-FM/2.14",
        "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    ],
)
def test_is_crawler_false(ua):
    assert is_crawler(ua) is False


# --- crawler_signals ---


def test_signals_bot_and_no_browser():
    sigs = crawler_signals("Googlebot/2.1")
    assert "bot_signal" in sigs and "no_browser_signature" in sigs


def test_signals_empty_for_browser():
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    assert crawler_signals(ua) == []


def test_signals_known_tool():
    assert "known_tool" in crawler_signals("Lighthouse")


def test_signals_bare_compatible():
    assert "bare_compatible" in crawler_signals("Mozilla/5.0 (compatible; MyBot/1.0)")


def test_signals_url_in_ua():
    assert "url_in_ua" in crawler_signals("Feed - http://example.com")


# --- crawler_name ---


@pytest.mark.parametrize(
    ("ua", "expected"),
    [
        ("AdsBot-Google (+http://www.google.com/adsbot.html)", "AdsBot-Google"),
        ("Caliperbot/1.0 (+http://www.conductor.com/caliperbot)", "Caliperbot"),
        ("AdsBot-Google-Mobile-Apps", "AdsBot-Google-Mobile-Apps"),
        ("Mozilla/5.0 (compatible; BitSightBot/1.0)", "BitSightBot"),
        (
            "Mozilla/5.0 (compatible; YandexVideoParser/1.0; +http://yandex.com/bots)",
            "YandexVideoParser",
        ),
        (
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) Speedy Spider "
            "(http://www.entireweb.com/about/search_tech/speedy_spider/)",
            "Speedy Spider",
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36 "
            "PingdomPageSpeed/1.0 (pingbot/2.0; +http://www.pingdom.com/)",
            "PingdomPageSpeed",
        ),
        (
            "NewsBlur Feed Fetcher - 1 subscriber - "
            "http://www.newsblur.com/site/0000000/webpage (Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/14.0.1 Safari/605.1.15)",
            "NewsBlur Feed Fetcher",
        ),
    ],
)
def test_crawler_name_expected(ua, expected):
    assert crawler_name(ua) == expected


def test_crawler_name_empty():
    assert crawler_name("") is None


def test_crawler_name_single_bot_in_mozilla():
    assert crawler_name("Mozilla/5.0 AppleWebKit/537.36 FooBot Safari/537.36") == "FooBot"


def test_crawler_name_none_for_browser_only():
    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 "
        "Chrome/59.0.3071.109 Safari/537.36"
    )
    assert crawler_name(ua) is None


def test_crawler_name_lowercase_non_mozilla_falls_back_to_split():
    assert crawler_name("curl/7.64.1") == "curl"


def test_crawler_name_compat_no_alpha_start():
    assert crawler_name("Mozilla/5.0 (compatible; 1badname)") is None


def test_crawler_name_prefix_trailing_slash_eof():
    assert crawler_name("BotName/1.0") == "BotName"


def test_crawler_name_prefix_bare_eof():
    assert crawler_name("BotName") == "BotName"


def test_crawler_name_prefix_odd_trailing_char_falls_back():
    assert crawler_name("BotName!x") == "BotName!x"


def test_crawler_name_unclosed_paren_returns_none():
    assert crawler_name("Mozilla/5.0 (Nikto/2.1.6") is None


def test_crawler_name_skips_browser_platform_parens():
    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"
    )
    assert crawler_name(ua) is None


# --- crawler_version ---


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
def test_crawler_version_expected(ua, expected):
    assert crawler_version(ua) == expected


def test_crawler_version_non_mozilla_no_slash():
    assert crawler_version("curl") is None


def test_crawler_version_empty():
    assert crawler_version("") is None


def test_crawler_version_compat_no_alpha_start_falls_through():
    assert crawler_version("Mozilla/5.0 (compatible; 1bad/2.0)") == "2.0"


def test_crawler_version_mozilla_trailing_slash():
    assert crawler_version("Mozilla/5.0 FooBot/") is None


# --- crawler_url ---


def test_crawler_url_plus_http():
    assert (
        crawler_url("Googlebot/2.1 (+http://www.google.com/bot.html)")
        == "http://www.google.com/bot.html"
    )


def test_crawler_url_space_dash():
    assert (
        crawler_url(
            "NewsBlur Feed Fetcher - 1 subscriber - http://www.newsblur.com/site/0"
        )
        == "http://www.newsblur.com/site/0"
    )


def test_crawler_url_https_leading():
    assert crawler_url("https://example.com/bot") == "https://example.com/bot"


def test_crawler_url_none_when_embedded():
    assert (
        crawler_url("Mozilla/5.0 (Windows NT 10.0; Win64) Chrome/120.0 Safari/537.36")
        is None
    )


def test_crawler_url_none_when_mid_word():
    assert crawler_url("see http://example.com for info") is None


# --- fixtures ---


def test_fixture_crawler_detected_pass_rate():
    uas = _load("crawler_user_agents.txt")
    detected = sum(1 for ua in uas if is_crawler(ua))
    rate = detected / len(uas)
    assert rate >= 0.96, f"pass rate {rate:.2%} ({detected}/{len(uas)})"


def test_fixture_browser_not_detected_pass_rate():
    uas = _load("browser_user_agents.txt")
    misses = sum(1 for ua in uas if is_crawler(ua))
    rate = (len(uas) - misses) / len(uas)
    assert rate >= 0.99, f"pass rate {rate:.4%} (misses={misses}/{len(uas)})"


def test_fixture_loadkpi_crawlers_pass_rate():
    uas = _load("loadkpi_crawlers.txt")
    detected = sum(1 for ua in uas if is_crawler(ua))
    rate = detected / len(uas)
    assert rate >= 0.91, f"pass rate {rate:.2%} ({detected}/{len(uas)})"


# --- module integrity ---


@pytest.mark.parametrize(
    "module",
    ["__init__.py", "__main__.py", "contrib.py", "ip.py", "parser.py"],
)
def test_module_does_not_import_regex(module):
    import ast

    source = (Path(__file__).parent.parent / "is_crawler" / module).read_text()
    blocked = {"re", "regex"}

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in blocked, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in blocked, node.module
