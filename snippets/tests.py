from pathlib import Path

from crawler_name import crawler_name
from crawler_url import crawler_contact, crawler_url
from crawler_version import crawler_version
from db_reader import crawler_info, crawlers_with_tag, load_database
from detect_engine import detect_engine
from detect_os import detect_os
from is_crawler_full import is_crawler as is_crawler_full
from is_crawler_minimal import is_crawler as is_crawler_minimal
from is_mobile import is_mobile, is_tablet
from parse_user_agent import parse
from robots_txt import build_robots_txt, parse_robots_txt

_FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"


def _load(name: str) -> list[str]:
    return [
        line.strip()
        for line in (_FIXTURES / name).read_text().splitlines()
        if line.strip()
    ]


CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
GPTBOT = "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"
CURL = "curl/8.4.0"
PYREQ = "python-requests/2.31.0"
AHREFS = "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"
HEADLESS = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "HeadlessChrome/120.0.0.0 Safari/537.36"
)


def test_minimal_browsers_pass():
    for ua in (CHROME, FIREFOX_LINUX, SAFARI_IPHONE):
        assert not is_crawler_minimal(ua), ua


def test_minimal_crawlers_caught():
    for ua in (GOOGLEBOT, GPTBOT, PYREQ, AHREFS):
        assert is_crawler_minimal(ua), ua


def test_full_browsers_pass():
    for ua in (CHROME, FIREFOX_LINUX, SAFARI_IPHONE):
        assert not is_crawler_full(ua), ua


def test_full_crawlers_caught():
    for ua in (GOOGLEBOT, GPTBOT, CURL, PYREQ, AHREFS, HEADLESS):
        assert is_crawler_full(ua), ua


def test_minimal_browser_fixture_pass_rate():
    uas = _load("browser_user_agents.txt")
    misses = sum(1 for ua in uas if is_crawler_minimal(ua))
    rate = (len(uas) - misses) / len(uas)
    assert rate >= 0.99, f"{rate:.4%} ({misses}/{len(uas)})"


def test_minimal_crawler_fixture_pass_rate():
    uas = _load("crawler_user_agents.txt")
    detected = sum(1 for ua in uas if is_crawler_minimal(ua))
    assert detected / len(uas) >= 0.75


def test_full_crawler_fixture_pass_rate():
    uas = _load("crawler_user_agents.txt")
    detected = sum(1 for ua in uas if is_crawler_full(ua))
    assert detected / len(uas) >= 0.96


def test_full_loadkpi_fixture_pass_rate():
    uas = _load("loadkpi_crawlers.txt")
    detected = sum(1 for ua in uas if is_crawler_full(ua))
    assert detected / len(uas) >= 0.94


def test_full_browser_fixture_pass_rate():
    uas = _load("browser_user_agents.txt")
    misses = sum(1 for ua in uas if is_crawler_full(ua))
    rate = (len(uas) - misses) / len(uas)
    assert rate >= 0.99


def test_crawler_name_compatible():
    assert crawler_name(GOOGLEBOT) == "Googlebot"
    assert crawler_name(GPTBOT) == "GPTBot"
    assert crawler_name(AHREFS) == "AhrefsBot"


def test_crawler_name_prefix():
    assert crawler_name(CURL) == "curl"
    assert crawler_name(PYREQ) == "python-requests"


def test_crawler_version_compatible():
    assert crawler_version(GOOGLEBOT) == "2.1"
    assert crawler_version(GPTBOT) == "1.2"
    assert crawler_version(AHREFS) == "7.0"


def test_crawler_version_prefix():
    assert crawler_version(CURL) == "8.4.0"
    assert crawler_version(PYREQ) == "2.31.0"


def test_crawler_url():
    assert crawler_url(GOOGLEBOT) == "http://www.google.com/bot.html"
    assert crawler_url(GPTBOT) == "https://openai.com/gptbot"
    assert crawler_url(CHROME) is None


def test_crawler_contact():
    ua = "MyBot/1.0 (contact: bot@example.com)"
    assert crawler_contact(ua) == "bot@example.com"
    assert crawler_contact(CHROME) is None


def test_parse_chrome():
    parsed = parse(CHROME)
    assert parsed.browser == "Chrome"
    assert parsed.browser_version == "120.0.0.0"
    assert parsed.engine == "AppleWebKit"
    assert parsed.os == "Windows"
    assert parsed.device == "Desktop"


def test_parse_firefox():
    parsed = parse(FIREFOX_LINUX)
    assert parsed.browser == "Firefox"
    assert parsed.os == "Linux"
    assert parsed.engine == "Gecko"


def test_parse_iphone():
    parsed = parse(SAFARI_IPHONE)
    assert parsed.os == "iOS"
    assert parsed.os_version == "16.5"
    assert parsed.device == "Mobile"
    assert parsed.is_mobile


def test_detect_os_windows():
    assert detect_os(CHROME) == ("Windows", "10/11")


def test_detect_os_ios():
    assert detect_os(SAFARI_IPHONE) == ("iOS", "16.5")


def test_detect_os_android():
    ua = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0"
    assert detect_os(ua) == ("Android", "14")


def test_detect_os_macos():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1"
    assert detect_os(ua) == ("macOS", None)


def test_detect_engine_blink():
    assert detect_engine(CHROME) == "Blink"


def test_detect_engine_gecko():
    assert detect_engine(FIREFOX_LINUX) == "Gecko"


def test_detect_engine_webkit():
    assert (
        detect_engine(SAFARI_IPHONE) == "Blink"
        or detect_engine(SAFARI_IPHONE) == "AppleWebKit"
    )


def test_is_mobile():
    assert is_mobile(SAFARI_IPHONE)
    assert not is_mobile(CHROME)
    assert not is_mobile(FIREFOX_LINUX)


def test_is_tablet():
    ua = (
        "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    )
    assert is_tablet(ua)
    assert not is_mobile(ua)


def test_robots_build():
    output = build_robots_txt(disallow=["GPTBot", "Bytespider"])
    assert "User-agent: GPTBot" in output
    assert "Disallow: /" in output
    assert "Bytespider" in output


_DB_PATH = str(Path(__file__).parent.parent / "is_crawler" / "crawler-user-agents.json")


def test_db_load():
    entries = load_database(_DB_PATH)
    assert len(entries) > 1000
    assert any("Googlebot" in entry.pattern for entry in entries)


def test_db_match_googlebot():
    info = crawler_info(GOOGLEBOT, _DB_PATH)
    assert info is not None
    assert "Googlebot" in info.pattern
    assert "search-engine" in info.tags


def test_db_match_gptbot():
    info = crawler_info(GPTBOT, _DB_PATH)
    assert info is not None
    assert "ai-crawler" in info.tags


def test_db_no_match_browser():
    assert crawler_info(CHROME, _DB_PATH) is None


def test_db_tag_filter():
    ai = crawlers_with_tag("ai-crawler", _DB_PATH)
    assert len(ai) > 10


def test_robots_parse():
    rules = parse_robots_txt(
        "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
    )
    assert "GPTBot" in rules
    assert "disallow:/" in rules["GPTBot"]
    assert "allow:/" in rules["*"]
