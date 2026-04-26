from pathlib import Path
import re

import pytest

from is_crawler import (
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
)
from is_crawler.database import crawler_info

_FIXTURES = Path(__file__).parent / "fixtures"
_LOG_PATTERN = re.compile(r'"[^"]*" \d+ \d+ "[^"]*" "([^"]*)"$')


def _parse_user_agents(log_file: Path) -> list[str]:
    agents = []
    for line in log_file.read_text(errors="replace").splitlines():
        match = _LOG_PATTERN.search(line)
        if match:
            ua = match.group(1)
            if ua and ua != "-":
                agents.append(ua)
    return agents


def _load_log(name: str) -> list[str]:
    return _parse_user_agents(_FIXTURES / name)


@pytest.fixture(scope="module")
def log1_agents():
    return _load_log("apache_access_1.txt")


@pytest.fixture(scope="module")
def log2_agents():
    return _load_log("apache_access_2.txt")


@pytest.fixture(scope="module")
def all_agents(log1_agents, log2_agents):
    return log1_agents + log2_agents


# --- parsing ---


def test_log1_parses_expected_volume(log1_agents):
    assert len(log1_agents) > 10_000


def test_log2_parses_expected_volume(log2_agents):
    assert len(log2_agents) > 5_000


def test_logs_contain_no_empty_agents(all_agents):
    assert all(ua for ua in all_agents)


# --- crawler detection ratio ---


def test_crawler_ratio_in_realistic_range(all_agents):
    detected = sum(1 for ua in all_agents if is_crawler(ua))
    ratio = detected / len(all_agents)
    assert 0.05 < ratio < 0.60, f"crawler ratio {ratio:.1%} out of expected range"


def test_log1_crawler_ratio(log1_agents):
    detected = sum(1 for ua in log1_agents if is_crawler(ua))
    ratio = detected / len(log1_agents)
    assert 0.05 < ratio < 0.70


def test_log2_crawler_ratio(log2_agents):
    detected = sum(1 for ua in log2_agents if is_crawler(ua))
    ratio = detected / len(log2_agents)
    assert 0.05 < ratio < 0.70


# --- known crawlers from real logs ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "Baiduspider+(+http://www.baidu.com/search/spider.htm)",
        "Baiduspider-image+(+http://www.baidu.com/search/spider.htm)",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
        "msnbot/2.0b (+http://search.msn.com/msnbot.htm)._",
        "facebookexternalhit/1.0 (+http://www.facebook.com/externalhit_uatext.php)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "ia_archiver-web.archive.org",
        "Mozilla/5.0 (compatible; archive.org_bot +http://www.archive.org/details/archive.org_bot)",
        "CatchBot/2.0; +http://www.catchbot.com",
        "CatchBot/3.0; +http://www.catchbot.com",
        "DomainCrawler/2.0 (info@domaincrawler.com; http://www.domaincrawler.com/transmsilverio.com",
        "AdnormCrawler www.adnorm.com/crawler",
        "Googlebot-Image/1.0",
        "GoogleBot 1.0",
        "DoCoMo/2.0 N905i(c100;TB;W24H16) (compatible; Googlebot-Mobile/2.1; +http://www.google.com/bot.html)",
        "AppEngine-Google; (+http://code.google.com/appengine; appid: s~getfavicon27)",
        "curl/7.18.2 (i486-pc-linux-gnu) libcurl/7.18.2 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.8",
        "curl/7.22.0 (i686-pc-linux-gnu) libcurl/7.22.0 OpenSSL/1.0.1 zlib/1.2.3.4 libidn/1.23 librtmp/2.3",
        "Java/1.6.0_23",
        "Java/1.6.0_24",
        "libwww-perl/5.803",
        "libwww-perl/5.834",
        "libwww-perl/6.04",
        "Feedfetcher-Google; (+http://www.google.com/feedfetcher.html; 16 subscribers; feed-id=3389821348893992437)",
        "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)",
        "FeedBurner/1.0 (http://www.FeedBurner.com)",
        "UniversalFeedParser/4.2-pre-314-svn +http://feedparser.org/",
        "Tiny Tiny RSS/1.11 (http://tt-rss.org/)",
        "CommaFeed/1.0 (http://www.commafeed.com)",
        "Feedbin - 1 subscribers",
        "Mozilla/5.0 (compatible; Ezooms/1.0; help@moz.com)",
        "Mozilla/5.0 (compatible; archive.org_bot; +http://www.archive.org/details/archive.org_bot)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    ],
)
def test_real_log_crawlers_detected(ua):
    assert is_crawler(ua) is True, f"expected crawler: {ua!r}"


# --- known browsers from real logs ---


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.91 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:27.0) Gecko/20100101 Firefox/27.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:22.0) Gecko/20100101 Firefox/22.0",
        "Mozilla/5.0 (Windows NT 6.1; rv:8.0) Gecko/20100101 Firefox/8.0",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; InfoPath.1)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9) Gecko/2008052906 Firefox/3.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/534.10",
    ],
)
def test_real_log_browsers_not_detected(ua):
    assert is_crawler(ua) is False, f"false positive browser: {ua!r}"


# --- crawler_info / signals / name / version coverage on log UAs ---


def test_crawler_info_returns_none_for_browser_ua():
    ua = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36"
    assert crawler_info(ua) is None


def test_crawler_info_populated_for_googlebot():
    ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    info = crawler_info(ua)
    assert info is not None
    assert info.tags == ("search-engine",)


def test_crawler_signals_nonempty_for_log_crawlers():
    crawlers = [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)",
        "curl/7.18.2 (i486-pc-linux-gnu) libcurl/7.18.2 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.8",
    ]
    for ua in crawlers:
        assert crawler_signals(ua), f"expected signals for {ua!r}"


def test_crawler_name_extracted_from_log_uas():
    cases = {
        "Googlebot-Image/1.0": "Googlebot-Image",
        "CatchBot/2.0; +http://www.catchbot.com": "CatchBot",
        "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)": "Feedly",
        "FeedBurner/1.0 (http://www.FeedBurner.com)": "FeedBurner",
        "curl/7.18.2 (i486-pc-linux-gnu) libcurl/7.18.2 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.8": "curl",
    }
    for ua, expected in cases.items():
        assert crawler_name(ua) == expected, f"name mismatch for {ua!r}"


def test_crawler_version_extracted_from_log_uas():
    cases = {
        "Googlebot-Image/1.0": "1.0",
        "curl/7.18.2 (i486-pc-linux-gnu) libcurl/7.18.2 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.8": "7.18.2",
        "CommaFeed/1.0 (http://www.commafeed.com)": "1.0",
        "UniversalFeedParser/4.2-pre-314-svn +http://feedparser.org/": "4.2-pre-314-svn",
    }
    for ua, expected in cases.items():
        assert crawler_version(ua) == expected, f"version mismatch for {ua!r}"


def test_crawler_url_extracted_from_log_uas():
    assert (
        crawler_url(
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        )
        == "http://www.google.com/bot.html"
    )
    assert (
        crawler_url(
            "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)"
        )
        == "http://www.feedly.com/fetcher.html"
    )
    assert (
        crawler_url("CatchBot/2.0; +http://www.catchbot.com") == "http://www.catchbot.com"
    )


# --- no false positives on unique browser UAs ---


def test_no_false_positives_on_unique_browser_uas(all_agents):
    browser_prefixes = (
        "Mozilla/5.0 (Windows",
        "Mozilla/5.0 (Macintosh",
        "Mozilla/5.0 (X11; Linux",
        "Mozilla/5.0 (X11; Ubuntu",
        "Mozilla/5.0 (Windows; U",
        "Mozilla/4.0 (compatible; MSIE",
    )
    crawler_signals_in_ua = (
        "bot",
        "Bot",
        "spider",
        "Spider",
        "crawler",
        "Crawler",
        "Slurp",
        "slurp",
        "Preview",
        "preview",
        "Proxy",
        "proxy",
        "AppEngine",
        "favicon",
        "fetcher",
        "Fetcher",
    )

    false_positives = [
        ua
        for ua in set(all_agents)
        if any(ua.startswith(p) for p in browser_prefixes)
        and not any(kw in ua for kw in crawler_signals_in_ua)
        and is_crawler(ua)
    ]
    assert false_positives == [], f"false positives: {false_positives}"
