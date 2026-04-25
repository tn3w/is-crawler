import json
import socket
from unittest.mock import patch

import pytest

from is_crawler.ip import (
    _all_domain_suffixes,
    _domains_for,
    _forward_ips,
    _load_domains,
    _parse_networks,
    forward_confirmed_rdns,
    ip_in_range,
    known_crawler_ip,
    known_crawler_rdns,
    reverse_dns,
    verify_crawler_ip,
)

# --- _load_domains ---


def test_load_domains_returns_dict():
    mapping = _load_domains()
    assert isinstance(mapping, dict)
    assert len(mapping) > 100


def test_load_domains_cached():
    assert _load_domains() is _load_domains()


def test_load_domains_keys_lowercase():
    mapping = _load_domains()
    assert all(k == k.lower() for k in mapping)


def test_load_domains_values_are_tuples_of_dotted_strings():
    for suffixes in _load_domains().values():
        assert isinstance(suffixes, tuple)
        assert all(s.startswith(".") for s in suffixes)


# --- _domains_for ---


@pytest.mark.parametrize(
    ("name", "expected_suffix"),
    [
        ("Googlebot", ".googlebot.com"),
        ("bingbot", ".search.msn.com"),
        ("Applebot", ".applebot.apple.com"),
        ("DuckDuckBot", ".duckduckgo.com"),
        ("YandexBot", ".yandex.ru"),
        ("Baiduspider", ".baidu.com"),
        ("facebookexternalhit", ".facebook.com"),
        ("GPTBot", ".openai.com"),
        ("ClaudeBot", ".anthropic.com"),
        ("PerplexityBot", ".perplexity.ai"),
        ("AhrefsBot", ".ahrefs.com"),
        ("SemrushBot", ".semrush.com"),
        ("MJ12bot", ".majestic12.co.uk"),
        ("CCBot", ".commoncrawl.org"),
        ("ia_archiver", ".archive.org"),
        ("Bytespider", ".bytespider.bytedance.com"),
        ("PetalBot", ".petalsearch.com"),
        ("YandexImages", ".yandex.ru"),
        ("Twitterbot", ".twttr.com"),
        ("LinkedInBot", ".linkedin.com"),
        ("Slurp", ".crawl.yahoo.net"),
        ("SeznamBot", ".seznam.cz"),
        ("DotBot", ".moz.com"),
        ("Diffbot", ".diffbot.com"),
        ("MojeekBot", ".mojeek.com"),
    ],
)
def test_domains_for_known_crawlers(name, expected_suffix):
    suffixes = _domains_for(name)
    assert suffixes is not None
    assert expected_suffix in suffixes


def test_domains_for_unknown_returns_none():
    assert _domains_for("UnknownRandomBot12345") is None


def test_domains_for_empty_string():
    assert _domains_for("") is None


def test_domains_for_name_with_version_slash():
    suffixes = _domains_for("Googlebot/2.1")
    assert suffixes is not None
    assert ".googlebot.com" in suffixes


def test_domains_for_name_with_space():
    suffixes = _domains_for("Sogou Web Spider")
    assert suffixes is not None
    assert ".sogou.com" in suffixes


def test_domains_for_case_insensitive():
    assert _domains_for("GOOGLEBOT") == _domains_for("googlebot")
    assert _domains_for("gOoGlEbOt") == _domains_for("googlebot")


# --- _parse_networks ---


def test_parse_networks_returns_list():
    nets = _parse_networks()
    assert isinstance(nets, list)


def test_build_index_lazy_and_cached():
    import is_crawler.ip as ip_mod
    from is_crawler.ip import _build_index

    original = ip_mod._IP_INDEX
    try:
        ip_mod._IP_INDEX = None
        ip_in_range.cache_clear()
        first = _build_index()
        assert _build_index() is first
        starts4, ends4, starts6, ends6 = first
        assert len(starts4) == len(ends4)
        assert len(starts6) == len(ends6)
    finally:
        ip_mod._IP_INDEX = original
        ip_in_range.cache_clear()


def test_parse_networks_without_file_returns_empty(tmp_path, monkeypatch):
    import is_crawler.ip as ip_mod

    monkeypatch.setattr(ip_mod, "__file__", str(tmp_path / "ip.py"))
    assert ip_mod._parse_networks() == []


def test_parse_networks_skips_invalid_cidr(tmp_path, monkeypatch):
    import is_crawler.ip as ip_mod

    data = {"test": ["192.168.1.0/24", "not-a-cidr", "10.0.0.0/8"]}
    (tmp_path / "crawler-ip-ranges.json").write_text(json.dumps(data))

    monkeypatch.setattr(ip_mod, "__file__", str(tmp_path / "ip.py"))
    assert len(ip_mod._parse_networks()) == 2


# --- reverse_dns ---


def test_reverse_dns_success():
    fake_host = "crawl-66-249-66-1.googlebot.com"
    with patch("socket.gethostbyaddr", return_value=(fake_host, [], ["66.249.66.1"])):
        result = reverse_dns.cache_clear() or reverse_dns("66.249.66.1")
    assert result == fake_host.lower()


def test_reverse_dns_strips_trailing_dot():
    with patch("socket.gethostbyaddr", return_value=("host.googlebot.com.", [], [])):
        reverse_dns.cache_clear()
        assert reverse_dns("1.2.3.4") == "host.googlebot.com"


def test_reverse_dns_lowercases():
    with patch("socket.gethostbyaddr", return_value=("Host.GoogleBot.COM", [], [])):
        reverse_dns.cache_clear()
        assert reverse_dns("1.2.3.4") == "host.googlebot.com"


def test_reverse_dns_oserror_returns_none():
    with patch("socket.gethostbyaddr", side_effect=OSError):
        reverse_dns.cache_clear()
        assert reverse_dns("0.0.0.0") is None


def test_reverse_dns_herror_returns_none():
    with patch("socket.gethostbyaddr", side_effect=socket.herror):
        reverse_dns.cache_clear()
        assert reverse_dns("0.0.0.1") is None


def test_reverse_dns_invalid_ip_returns_none_without_lookup():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr") as lookup:
        assert reverse_dns("not-an-ip") is None
    lookup.assert_not_called()


def test_reverse_dns_strips_ip_whitespace():
    with patch("socket.gethostbyaddr", return_value=("host.googlebot.com", [], [])):
        reverse_dns.cache_clear()
        assert reverse_dns(" 1.2.3.4 \n") == "host.googlebot.com"


# --- _forward_ips ---


def test_forward_ips_success():
    fake_infos = [
        (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("66.249.66.1", 0)),
    ]
    with patch("socket.getaddrinfo", return_value=fake_infos):
        _forward_ips.cache_clear()
        result = _forward_ips("crawl-66-249-66-1.googlebot.com")
    assert "66.249.66.1" in result


def test_forward_ips_gaierror_returns_empty():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror):
        _forward_ips.cache_clear()
        assert _forward_ips("nonexistent.invalid") == frozenset()


def test_forward_ips_oserror_returns_empty():
    with patch("socket.getaddrinfo", side_effect=OSError):
        _forward_ips.cache_clear()
        assert _forward_ips("bad.host") == frozenset()


def test_forward_ips_multiple_addrs():
    fake_infos = [
        (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("1.2.3.4", 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("5.6.7.8", 0)),
    ]
    with patch("socket.getaddrinfo", return_value=fake_infos):
        _forward_ips.cache_clear()
        result = _forward_ips("multi.example.com")
    assert result == frozenset({"1.2.3.4", "5.6.7.8"})


# --- forward_confirmed_rdns ---


def _mock_rdns(ip: str, host: str, forward_ips: list[str]):
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with (
        patch("socket.gethostbyaddr", return_value=(host, [], [ip])),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", (fwd_ip, 0))
                for fwd_ip in forward_ips
            ],
        ),
    ):
        return forward_confirmed_rdns(ip, (".googlebot.com", ".google.com"))


def test_forward_confirmed_rdns_valid():
    result = _mock_rdns(
        "66.249.66.1",
        "crawl-66-249-66-1.googlebot.com",
        ["66.249.66.1"],
    )
    assert result == "crawl-66-249-66-1.googlebot.com"


def test_forward_confirmed_rdns_no_reverse():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr", side_effect=OSError):
        result = forward_confirmed_rdns("1.1.1.1", (".googlebot.com",))
    assert result is None


def test_forward_confirmed_rdns_wrong_suffix():
    result = _mock_rdns(
        "1.2.3.4",
        "host.evil.com",
        ["1.2.3.4"],
    )
    assert result is None


def test_forward_confirmed_rdns_suffix_mismatch_forward_miss():
    result = _mock_rdns(
        "1.2.3.4",
        "crawl.googlebot.com",
        ["9.9.9.9"],
    )
    assert result is None


def test_forward_confirmed_rdns_exact_suffix_match():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with (
        patch("socket.gethostbyaddr", return_value=("googlebot.com", [], [])),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("5.5.5.5", 0)),
            ],
        ),
    ):
        result = forward_confirmed_rdns("5.5.5.5", (".googlebot.com",))
    assert result == "googlebot.com"


def test_forward_confirmed_rdns_invalid_ip_returns_none_without_lookup():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr") as lookup:
        result = forward_confirmed_rdns("not-an-ip", (".googlebot.com",))
    assert result is None
    lookup.assert_not_called()


def test_all_domain_suffixes_cached():
    _all_domain_suffixes.cache_clear()
    assert _all_domain_suffixes() is _all_domain_suffixes()


# --- ip_in_range / known_crawler_ip ---


def _with_networks(cidrs: list[str]):
    import ipaddress

    import is_crawler.ip as ip_mod

    original = ip_mod._IP_INDEX
    nets = [ipaddress.ip_network(c, strict=False) for c in cidrs]
    v4 = sorted(ipaddress.collapse_addresses([n for n in nets if n.version == 4]))
    v6 = sorted(ipaddress.collapse_addresses([n for n in nets if n.version == 6]))
    ip_mod._IP_INDEX = (
        [int(n.network_address) for n in v4],
        [int(n.broadcast_address) for n in v4],
        [int(n.network_address) for n in v6],
        [int(n.broadcast_address) for n in v6],
    )
    ip_in_range.cache_clear()
    return original


def _restore_networks(original):
    import is_crawler.ip as ip_mod

    ip_mod._IP_INDEX = original
    ip_in_range.cache_clear()


def test_ip_in_range_hit():
    orig = _with_networks(["66.249.64.0/19", "192.178.4.0/27"])
    try:
        assert ip_in_range("66.249.66.1") is True
    finally:
        _restore_networks(orig)


def test_ip_in_range_miss():
    orig = _with_networks(["66.249.64.0/19"])
    try:
        assert ip_in_range("8.8.8.8") is False
    finally:
        _restore_networks(orig)


def test_ip_in_range_ipv6_hit():
    orig = _with_networks(["2001:4860:4801::/48"])
    try:
        assert ip_in_range("2001:4860:4801::1") is True
    finally:
        _restore_networks(orig)


def test_ip_in_range_invalid_ip():
    orig = _with_networks(["66.249.64.0/19"])
    try:
        assert ip_in_range("not-an-ip") is False
    finally:
        _restore_networks(orig)


def test_ip_in_range_empty_networks():
    orig = _with_networks([])
    try:
        assert ip_in_range("66.249.66.1") is False
    finally:
        _restore_networks(orig)


def test_known_crawler_ip_delegates():
    orig = _with_networks(["66.249.64.0/19"])
    try:
        assert known_crawler_ip("66.249.66.1") is True
        assert known_crawler_ip("8.8.8.8") is False
    finally:
        _restore_networks(orig)


def test_known_crawler_rdns_hit():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    ip = "66.249.66.1"
    with (
        patch(
            "socket.gethostbyaddr",
            return_value=("crawl-66-249-66-1.googlebot.com", [], [ip]),
        ),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, 0)),
            ],
        ),
    ):
        assert known_crawler_rdns(ip) is True


def test_known_crawler_rdns_miss():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with patch("socket.gethostbyaddr", return_value=("dns.google", [], ["8.8.8.8"])):
        assert known_crawler_rdns("8.8.8.8") is False


def test_known_crawler_rdns_invalid_ip_returns_false_without_lookup():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr") as lookup:
        assert known_crawler_rdns("not-an-ip") is False
    lookup.assert_not_called()


# --- verify_crawler_ip ---


_GOOGLEBOT_UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"
_BINGBOT_UA = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
_GPTBOT_UA = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
_CLAUDE_UA = "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://anthropic.com/bot)"
_APPLEBOT_UA = "Mozilla/5.0 (compatible; Applebot/0.1; +http://www.apple.com/go/applebot)"
_DUCKBOT_UA = "DuckDuckBot/1.1"
_YANDEX_UA = "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"
_BAIDU_UA = (
    "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"
)
_FB_UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
_AHREFS_UA = "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"
_SEMRUSH_UA = "Mozilla/5.0 (compatible; SemrushBot/7; +http://www.semrush.com/bot.html)"
_TWITTER_UA = "Twitterbot/1.0"
_LINKEDIN_UA = "LinkedInBot/1.0"
_PINTEREST_UA = "Pinterest/0.2 (+http://www.pinterest.com/bot.html)"
_PERPLEXITY_UA = (
    "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"
)
_ARCHIVE_UA = (
    "ia_archiver (+http://www.alexa.com/site/help/webmasters; crawler@alexa.com)"
)
_CCBOT_UA = "CCBot/2.0 (https://commoncrawl.org/faq/)"
_BYTESPIDER_UA = "Mozilla/5.0 (Linux; Android 5.0) Bytespider"
_MOJEEK_UA = "Mozilla/5.0 (compatible; MojeekBot/0.11; +https://www.mojeek.com/bot.html)"


@pytest.mark.parametrize(
    ("ua", "host", "ip", "suffix"),
    [
        (
            _GOOGLEBOT_UA,
            "crawl-66-249-66-1.googlebot.com",
            "66.249.66.1",
            ".googlebot.com",
        ),
        (
            _BINGBOT_UA,
            "msnbot-40-77-167-23.search.msn.com",
            "40.77.167.23",
            ".search.msn.com",
        ),
        (
            _GPTBOT_UA,
            "crawl-23-102-140-112.openai.com",
            "23.102.140.112",
            ".openai.com",
        ),
        (_CLAUDE_UA, "crawl-1-2-3-4.anthropic.com", "1.2.3.4", ".anthropic.com"),
        (
            _APPLEBOT_UA,
            "crawl.applebot.apple.com",
            "17.58.96.100",
            ".applebot.apple.com",
        ),
        (_YANDEX_UA, "crawler.yandex.ru", "77.88.55.77", ".yandex.ru"),
        (
            _BAIDU_UA,
            "baiduspider-180-76-15-136.crawl.baidu.com",
            "180.76.15.136",
            ".crawl.baidu.com",
        ),
        (_FB_UA, "crawl-66-220-155-35.facebook.com", "66.220.155.35", ".facebook.com"),
        (_AHREFS_UA, "crawl-54-36-148-247.ahrefs.com", "54.36.148.247", ".ahrefs.com"),
        (_SEMRUSH_UA, "crawler.semrush.com", "185.191.171.1", ".semrush.com"),
        (_TWITTER_UA, "crawl-199-16-156-69.twttr.com", "199.16.156.69", ".twttr.com"),
        (_LINKEDIN_UA, "crawl.linkedin.com", "108.174.10.10", ".linkedin.com"),
        (_PINTEREST_UA, "crawl.pinterest.com", "54.236.1.1", ".pinterest.com"),
        (_PERPLEXITY_UA, "bot.perplexity.ai", "52.1.2.3", ".perplexity.ai"),
        (_ARCHIVE_UA, "crawl.archive.org", "207.241.224.2", ".archive.org"),
        (_CCBOT_UA, "crawl.commoncrawl.org", "54.172.5.4", ".commoncrawl.org"),
        (
            _BYTESPIDER_UA,
            "crawl.bytespider.bytedance.com",
            "198.200.2.2",
            ".bytespider.bytedance.com",
        ),
        (_MOJEEK_UA, "crawl.mojeek.com", "93.157.30.5", ".mojeek.com"),
    ],
)
def test_verify_crawler_ip_valid(ua, host, ip, suffix):
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with (
        patch("socket.gethostbyaddr", return_value=(host, [], [ip])),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, 0)),
            ],
        ),
    ):
        assert verify_crawler_ip(ua, ip) is True


def test_verify_crawler_ip_spoof_wrong_rdns():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with patch("socket.gethostbyaddr", return_value=("evil.attacker.com", [], [])):
        assert verify_crawler_ip(_GOOGLEBOT_UA, "1.2.3.4") is False


def test_verify_crawler_ip_spoof_no_rdns():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr", side_effect=OSError):
        assert verify_crawler_ip(_GOOGLEBOT_UA, "1.2.3.4") is False


def test_verify_crawler_ip_forward_mismatch():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with (
        patch("socket.gethostbyaddr", return_value=("crawl.googlebot.com", [], [])),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("9.9.9.9", 0)),
            ],
        ),
    ):
        assert verify_crawler_ip(_GOOGLEBOT_UA, "1.2.3.4") is False


def test_verify_crawler_ip_unknown_ua():
    assert (
        verify_crawler_ip("Mozilla/5.0 (Windows NT 10.0) Chrome/120", "1.2.3.4") is False
    )


def test_verify_crawler_ip_empty_ua():
    assert verify_crawler_ip("", "1.2.3.4") is False


def test_verify_crawler_ip_unknown_crawler_no_rdns_mapping():
    assert verify_crawler_ip("UnknownSpecialCrawler/1.0", "1.2.3.4") is False


def test_verify_crawler_ip_invalid_ip_returns_false_without_lookup():
    reverse_dns.cache_clear()
    with patch("socket.gethostbyaddr") as lookup:
        assert verify_crawler_ip(_GOOGLEBOT_UA, "not-an-ip") is False
    lookup.assert_not_called()


def test_verify_crawler_ip_accepts_ip_whitespace():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    with (
        patch(
            "socket.gethostbyaddr",
            return_value=("crawl-66-249-66-1.googlebot.com", [], ["66.249.66.1"]),
        ),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("66.249.66.1", 0)),
            ],
        ),
    ):
        assert verify_crawler_ip(_GOOGLEBOT_UA, " 66.249.66.1 ") is True


def test_verify_crawler_ip_duckduckbot():
    reverse_dns.cache_clear()
    _forward_ips.cache_clear()
    ip = "46.51.197.89"
    with (
        patch("socket.gethostbyaddr", return_value=("crawl.duckduckgo.com", [], [ip])),
        patch(
            "socket.getaddrinfo",
            return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, 0)),
            ],
        ),
    ):
        assert verify_crawler_ip(_DUCKBOT_UA, ip) is True


# --- __all__ ---


def test_all_exports():
    from is_crawler import ip

    assert set(ip.__all__) == {
        "verify_crawler_ip",
        "reverse_dns",
        "forward_confirmed_rdns",
        "ip_in_range",
        "known_crawler_ip",
        "known_crawler_rdns",
    }
