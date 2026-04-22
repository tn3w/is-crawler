from pathlib import Path

import pytest

from is_crawler import (
    CrawlerInfo,
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
    _robots_name,
    _semicolon_agent,
    _token_after,
    _url_in_ua,
    _word_char,
    _word_ends,
    build_robots_txt,
    crawler_has_tag,
    crawler_info,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
    iter_crawlers,
    robots_agents_for_tags,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[str]:
    return [l.strip() for l in (_FIXTURES / name).read_text().splitlines() if l.strip()]


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
    assert (
        crawler_name("Mozilla/5.0 AppleWebKit/537.36 FooBot Safari/537.36") == "FooBot"
    )


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
    assert info.tags == ("search-engine",)


def test_crawler_info_bingbot():
    info = crawler_info(_BINGBOT)
    assert info is not None
    assert info.url == "http://www.bing.com/bingbot.htm"
    assert info.description == "Microsoft's web crawling bot for Bing search indexing"
    assert info.tags == ("search-engine",)


def test_crawler_info_linkedinbot():
    info = crawler_info(_LINKEDINBOT)
    assert info is not None
    assert info.url == ""
    assert (
        info.description
        == "LinkedIn's bot for crawling professional content and profiles"
    )
    assert info.tags == ("social-preview",)


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


def test_crawler_has_tag_dedup_multi_tag():
    assert crawler_has_tag("tagoobot/1.0", ["ai-crawler", "search-engine"]) is True


# --- fixtures ---


@pytest.mark.parametrize("ua", _load("crawler_user_agents.txt"))
def test_fixture_crawler_detected(ua):
    assert is_crawler(ua) is True


@pytest.mark.parametrize("ua", _load("browser_user_agents.txt"))
def test_fixture_browser_not_detected(ua):
    assert is_crawler(ua) is False


# --- CLI (__main__) ---

import io
import json
from unittest.mock import patch

from is_crawler.__main__ import _analyze, _iter_inputs, main

_GOOGLEBOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"


def test_analyze_crawler():
    result = _analyze(_GOOGLEBOT)
    assert result["is_crawler"] is True
    assert result["name"] == "Googlebot"
    assert result["version"] == "2.1"
    assert result["url"] == "http://www.google.com/bot.html"
    assert "bot_signal" in result["signals"]
    assert result["info"] is not None
    assert result["info"]["tags"] == ("search-engine",)


def test_analyze_browser():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    result = _analyze(ua)
    assert result["is_crawler"] is False
    assert result["info"] is None


def test_iter_inputs_argv():
    items = list(_iter_inputs(["prog", "Googlebot/2.1"]))
    assert items == ["Googlebot/2.1"]


def test_iter_inputs_argv_multi_words():
    items = list(_iter_inputs(["prog", "My", "Bot/1.0"]))
    assert items == ["My Bot/1.0"]


def test_iter_inputs_stdin():
    fake_stdin = io.StringIO("BotA\nBotB\n\nBotC\n")
    with patch("sys.stdin", fake_stdin):
        items = list(_iter_inputs(["prog"]))
    assert items == ["BotA", "BotB", "BotC"]


def test_iter_inputs_stdin_crlf_and_whitespace():
    fake_stdin = io.StringIO("BotA\r\n  \r\n BotB \r\n")
    with patch("sys.stdin", fake_stdin):
        items = list(_iter_inputs(["prog"]))
    assert items == ["BotA", "BotB"]


def test_main_argv(capsys):
    with patch("sys.argv", ["prog", _GOOGLEBOT]):
        result = main()
    assert result == 0
    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["is_crawler"] is True
    assert data["name"] == "Googlebot"


def test_main_stdin(capsys):
    fake_stdin = io.StringIO(_GOOGLEBOT + "\n")
    with patch("sys.argv", ["prog"]), patch("sys.stdin", fake_stdin):
        result = main()
    assert result == 0
    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["is_crawler"] is True


def test_main_stdin_multiple(capsys):
    ua_browser = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    fake_stdin = io.StringIO(f"{_GOOGLEBOT}\n{ua_browser}\n")
    with patch("sys.argv", ["prog"]), patch("sys.stdin", fake_stdin):
        main()
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["is_crawler"] is True
    assert json.loads(lines[1])["is_crawler"] is False


def test_main_stdin_crlf(capsys):
    fake_stdin = io.StringIO(_GOOGLEBOT + "\r\n")
    with patch("sys.argv", ["prog"]), patch("sys.stdin", fake_stdin):
        result = main()
    assert result == 0
    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["name"] == "Googlebot"


# --- category shortcuts ---

from is_crawler import (
    is_academic,
    is_advertising,
    is_ai_crawler,
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
)


def test_is_search_engine():
    assert is_search_engine(_GOOGLEBOT) is True
    assert is_search_engine("curl/7.64.1") is False


def test_is_ai_crawler():
    ua = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
    assert is_ai_crawler(ua) is True
    assert is_ai_crawler(_GOOGLEBOT) is False


def test_is_seo():
    assert is_seo("Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)")
    assert is_seo(_GOOGLEBOT) is False


def test_is_social_preview():
    ua = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
    assert is_social_preview(ua) is True
    assert is_social_preview(_GOOGLEBOT) is False


def test_is_advertising():
    ua = "Mozilla/5.0 (compatible; AdsBot-Google; +http://www.google.com/adsbot.html)"
    assert is_advertising(ua) is True


def test_is_archiver():
    ua = "Mozilla/5.0 (compatible; archive.org_bot; +http://www.archive.org/details/archive.org_bot)"
    assert is_archiver(ua) is True


def test_is_feed_reader():
    ua = "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)"
    assert is_feed_reader(ua) is True


def test_is_monitoring():
    ua = "Mozilla/5.0 (compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)"
    assert is_monitoring(ua) is True


def test_is_scanner():
    ua = "Mozilla/5.00 (Nikto/2.1.6) (Evasions:None) (Test:000003)"
    assert is_scanner(ua) is True


def test_is_academic():
    ua = "ia_archiver-web.archive.org"
    _ = is_academic(ua)
    assert is_academic(_GOOGLEBOT) is False


def test_is_http_library():
    assert is_http_library("python-requests/2.28.0") is True


def test_is_browser_automation():
    ua = "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/100.0.0.0 Safari/537.36"
    _ = is_browser_automation(ua)


def test_is_good_crawler():
    assert is_good_crawler(_GOOGLEBOT) is True
    ua = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
    assert is_good_crawler(ua) is False


def test_is_bad_crawler():
    ua = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
    assert is_bad_crawler(ua) is True
    assert is_bad_crawler(_GOOGLEBOT) is False


def test_good_bad_on_browser():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    assert is_good_crawler(ua) is False
    assert is_bad_crawler(ua) is False


# --- robots.txt helpers ---


def test_robots_name_plain():
    assert _robots_name("Googlebot\\/") == "Googlebot"


def test_robots_name_escaped():
    assert _robots_name("AdsBot-Google([^-]|$)") == "AdsBot-Google"


def test_robots_name_charclass():
    assert _robots_name("[wW]get") == "wget"


def test_robots_name_escaped_dot():
    assert _robots_name("grub\\.org") == "grub.org"


def test_robots_name_escaped_parens():
    assert _robots_name("Mediapartners \\(Googlebot\\)") == "Mediapartners"


def test_robots_name_trailing_space():
    assert _robots_name("webmon ") == "webmon"


def test_robots_name_anchored():
    assert _robots_name("^curl") == "curl"


def test_robots_name_drops_urls():
    assert _robots_name("https://example.com/bot") is None


def test_robots_name_empty():
    assert _robots_name("(compatible)") is None


def test_iter_crawlers():
    items = list(iter_crawlers())
    assert len(items) > 500
    info, name = items[0]
    assert isinstance(info, CrawlerInfo)
    assert name


def test_robots_agents_single_tag():
    agents = robots_agents_for_tags("search-engine")
    assert "Googlebot" in agents
    assert "bingbot" in agents
    assert agents == sorted(agents)


def test_robots_agents_multi_tag():
    agents = robots_agents_for_tags(["ai-crawler", "scanner"])
    assert "GPTBot" in agents
    assert "Nikto" in agents


def test_build_robots_txt_disallow():
    out = build_robots_txt(disallow="ai-crawler")
    assert "User-agent: GPTBot" in out
    assert "Disallow: /" in out
    assert out.endswith("\n")


def test_build_robots_txt_allow_path():
    out = build_robots_txt(allow="search-engine", path="/public")
    assert "User-agent: Googlebot" in out
    assert "Allow: /public" in out


def test_build_robots_txt_both():
    out = build_robots_txt(disallow="scanner", allow="search-engine")
    assert "Disallow: /" in out
    assert "Allow: /" in out


def test_build_robots_txt_disallow_precedence_on_overlap():
    out = build_robots_txt(
        disallow=["ai-crawler", "scanner"],
        allow=["ai-crawler", "search-engine"],
    )
    assert out.count("User-agent: GPTBot\n") == 1
    assert "User-agent: GPTBot\nDisallow: /\n" in out
    assert "User-agent: GPTBot\nAllow: /\n" not in out


def test_build_robots_txt_empty():
    assert build_robots_txt() == ""
