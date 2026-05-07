from pathlib import Path

from is_crawler.parser import (
    UserAgent,
    _android_version,
    _cros_version,
    _detect_browser,
    _detect_cpu,
    _detect_crawler,
    _detect_device_brand,
    _detect_device_kind,
    _detect_engine,
    _detect_os,
    _direct_os_version,
    _distro_version,
    _extract_languages,
    _find_paren_contents,
    _has_any,
    _ios_version,
    _is_blink,
    _linux_kernel_version,
    _mac_version,
    _parse_ua,
    _read_dotted,
    _read_version,
    _token_version,
    _underscore_version,
    is_browser,
    is_crawler,
    normalize_user_agent,
    parse,
    parse_or_none,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[str]:
    return [
        line.strip()
        for line in (_FIXTURES / name).read_text().splitlines()
        if line.strip()
    ]


_CHROME_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0"
_SAFARI_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Safari/605.1.15"
)
_MOBILE_CHROME = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.6099.144 Mobile Safari/537.36"
)
_IPHONE_SAFARI = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)
_IPAD_SAFARI = (
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.0 Mobile/15E148 Safari/604.1"
)
_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
_EDGE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
)


def test_read_version_basic():
    assert _read_version("abc/1.2.3", 4) == "1.2.3"
    assert _read_version("abc/", 4) is None


def test_token_version_found_and_missing():
    assert _token_version("Chrome/120.0", "Chrome/") == "120.0"
    assert _token_version("no-token", "Chrome/") is None


def test_has_any():
    assert _has_any("bot crawler", ("bot",))
    assert not _has_any("normal ua", ("bot",))


def test_detect_browser_chrome():
    browser, version = _detect_browser(_CHROME_WIN)
    assert browser == "Chrome"
    assert version is not None and version.startswith("120")


def test_detect_browser_firefox():
    browser, version = _detect_browser(_FIREFOX_LINUX)
    assert browser == "Firefox"
    assert version is not None and version.startswith("121")


def test_detect_browser_safari():
    browser, version = _detect_browser(_SAFARI_MAC)
    assert browser == "Safari"


def test_detect_browser_edge():
    browser, version = _detect_browser(_EDGE)
    assert browser == "Edge"


def test_detect_browser_mobile_chrome_crios():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0 Mobile/15E148 Safari/604.1"
    )
    browser, version = _detect_browser(ua)
    assert browser == "Mobile Chrome"


def test_detect_browser_mobile_chrome_android():
    browser, version = _detect_browser(_MOBILE_CHROME)
    assert browser == "Mobile Chrome"


def test_detect_browser_mobile_firefox():
    ua = "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/121.0"
    browser, version = _detect_browser(ua)
    assert browser == "Mobile Firefox"


def test_detect_browser_mobile_safari_iphone():
    browser, version = _detect_browser(_IPHONE_SAFARI)
    assert browser == "Mobile Safari"


def test_detect_browser_webview():
    ua = (
        "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36"
    )
    browser, _ = _detect_browser(ua)
    assert browser == "Chrome WebView"


def test_detect_browser_lib_curl():
    browser, version = _detect_browser("curl/7.81.0")
    assert browser == "curl"
    assert version == "7.81.0"


def test_detect_browser_lib_python_requests():
    browser, _ = _detect_browser("python-requests/2.28.0")
    assert browser == "Python Requests"


def test_detect_browser_gecko_fallback():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101"
    browser, version = _detect_browser(ua)
    assert browser == "Firefox"
    assert version == "78.0"


def test_detect_browser_simple_token():
    browser, version = _detect_browser("MyBot/1.0")
    assert browser == "MyBot"
    assert version == "1.0"


def test_detect_browser_unknown():
    browser, version = _detect_browser("something without slash")
    assert browser is None
    assert version is None


def test_detect_browser_token_no_version_skips():
    ua = "Mozilla/5.0 (Macintosh) AppleWebKit/605 (KHTML, like Gecko) Version/ Safari/605"
    browser, _ = _detect_browser(ua)
    assert browser != "Safari"


def test_detect_browser_safari_token_without_safari_slash():
    ua = "Mozilla/5.0 (Macintosh) AppleWebKit/605 Version/17.0"
    browser, _ = _detect_browser(ua)
    assert browser != "Safari"


def test_detect_browser_opera_gx():
    ua = "Mozilla/5.0 ... OPRGX/98.0"
    browser, version = _detect_browser(ua)
    assert browser == "Opera GX"


def test_detect_browser_brave():
    ua = "Mozilla/5.0 ... Brave/1.60"
    browser, version = _detect_browser(ua)
    assert browser == "Brave"


def test_detect_browser_samsung():
    ua = (
        "Mozilla/5.0 (Linux; Android 12; SM-G998B) "
        "AppleWebKit/537.36 SamsungBrowser/18.0 Chrome/120.0 Mobile Safari/537.36"
    )
    browser, _ = _detect_browser(ua)
    assert browser == "Samsung Browser"


def test_detect_browser_fxios():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) FxiOS/120.0"
    browser, _ = _detect_browser(ua)
    assert browser == "Firefox iOS"


def test_detect_engine_blink():
    engine, _ = _detect_engine(_CHROME_WIN)
    assert engine == "Blink"


def test_detect_engine_gecko():
    engine, _ = _detect_engine(_FIREFOX_LINUX)
    assert engine == "Gecko"


def test_detect_engine_webkit():
    engine, _ = _detect_engine(_SAFARI_MAC)
    assert engine == "AppleWebKit"


def test_detect_engine_trident():
    ua = "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko"
    engine, _ = _detect_engine(ua)
    assert engine == "Trident"


def test_detect_engine_trident_via_applewebkit():
    ua = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 Trident/7.0"
    engine, _ = _detect_engine(ua)
    assert engine == "Trident"


def test_detect_engine_presto():
    ua = "Opera/9.80 (Windows NT 6.1) Presto/2.12.388 Version/12.17"
    engine, _ = _detect_engine(ua)
    assert engine == "Presto"


def test_detect_engine_goanna():
    ua = "Mozilla/5.0 (Windows NT 6.1; rv:52.9) Goanna/4.8 Gecko/20100101"
    engine, _ = _detect_engine(ua)
    assert engine == "Goanna"


def test_detect_engine_khtml():
    ua = "Mozilla/5.0 (compatible; Konqueror/5; KHTML)"
    engine, version = _detect_engine(ua)
    assert engine == "KHTML"
    assert version is None


def test_detect_engine_none():
    engine, _ = _detect_engine("curl/7.81.0")
    assert engine is None


def test_is_blink_chrome():
    assert _is_blink(_CHROME_WIN)


def test_is_blink_old_chrome():
    ua = "Mozilla/5.0 Chrome/27.0"
    assert not _is_blink(ua)


def test_is_blink_no_chrome():
    assert not _is_blink("curl/7.81.0")


def test_is_blink_via_token():
    ua = "Mozilla/5.0 OPR/80.0"
    assert _is_blink(ua)


def test_detect_os_windows_nt():
    os_name, os_version = _detect_os(_CHROME_WIN)
    assert os_name == "Windows"
    assert os_version == "10"


def test_detect_os_windows_legacy():
    ua = "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)"
    os_name, os_version = _detect_os(ua)
    assert os_name == "Windows"
    assert os_version == "98"


def test_detect_os_macos():
    os_name, os_version = _detect_os(_SAFARI_MAC)
    assert os_name == "macOS"
    assert os_version is not None and "10" in os_version


def test_detect_os_ios():
    os_name, os_version = _detect_os(_IPHONE_SAFARI)
    assert os_name == "iOS"
    assert os_version is not None and os_version.startswith("17")


def test_detect_os_ipad_ios_crios():
    ua = (
        "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 CriOS/120.0 Mobile/15E148 Safari/604.1"
    )
    os_name, _ = _detect_os(ua)
    assert os_name == "iOS"


def test_detect_os_ipad_ipados():
    os_name, _ = _detect_os(_IPAD_SAFARI)
    assert os_name == "iPadOS"


def test_detect_os_ipad_no_cpu():
    ua = "Mozilla/5.0 (iPad; ...)"
    os_name, _ = _detect_os(ua)
    assert os_name == "iPadOS"


def test_detect_os_android():
    os_name, os_version = _detect_os(_MOBILE_CHROME)
    assert os_name == "Android"
    assert os_version is not None and os_version.startswith("13")


def test_detect_os_linux():
    os_name, _ = _detect_os(_FIREFOX_LINUX)
    assert os_name == "Linux"


def test_detect_os_linux_distro():
    ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101"
    os_name, _ = _detect_os(ua)
    assert os_name == "Ubuntu"


def test_detect_os_direct_chromeos():
    ua = "Mozilla/5.0 (X11; CrOS x86_64 14268.67.0)"
    os_name, _ = _detect_os(ua)
    assert os_name == "Chromium OS"


def test_detect_os_xbox():
    ua = "Mozilla/5.0 (Xbox; Xbox One) AppleWebKit/537.36"
    os_name, _ = _detect_os(ua)
    assert os_name == "Xbox"


def test_detect_os_symbian():
    ua = "Mozilla/5.0 (SymbOS; ...)"
    os_name, _ = _detect_os(ua)
    assert os_name == "Symbian"


def test_detect_os_blackberry():
    ua = "BlackBerry9700/5.0.0.862"
    os_name, _ = _detect_os(ua)
    assert os_name == "BlackBerry"


def test_detect_os_freebsd():
    ua = "Mozilla/5.0 (FreeBSD amd64; ...)"
    os_name, _ = _detect_os(ua)
    assert os_name == "FreeBSD"


def test_detect_os_none():
    os_name, _ = _detect_os("curl/7.81.0")
    assert os_name is None


def test_detect_cpu_x86_64():
    assert _detect_cpu(_CHROME_WIN) == "x86_64"


def test_detect_cpu_arm64():
    assert _detect_cpu("aarch64") == "arm64"


def test_detect_cpu_x86():
    assert _detect_cpu("Mozilla/5.0 (Windows; U; Windows NT 5.1; i686)") == "x86"


def test_detect_cpu_none():
    assert _detect_cpu("curl/7.81.0") is None


def test_detect_device_kind_console():
    assert _detect_device_kind("PlayStation 5") == "Console"


def test_detect_device_kind_smarttv():
    assert _detect_device_kind("SMART-TV;") == "SmartTV"


def test_detect_device_kind_tizen_tv():
    assert _detect_device_kind("Tizen 6.0 SMART-TV") == "SmartTV"


def test_detect_device_kind_tizen_tv_keyword():
    assert _detect_device_kind("Mozilla/5.0 (SMART TV; Tizen 5.0) TV/1.0") == "SmartTV"


def test_detect_device_kind_tablet():
    assert _detect_device_kind("iPad") == "Tablet"


def test_detect_device_kind_mobile():
    assert _detect_device_kind("iPhone") == "Mobile"


def test_detect_device_kind_android_mobile():
    assert _detect_device_kind("Android Mobile") == "Mobile"


def test_detect_device_kind_android_tablet():
    assert _detect_device_kind("Android Tablet") == "Tablet"


def test_detect_device_kind_mobile_keyword():
    assert _detect_device_kind("Mozilla/5.0 Mobile") == "Mobile"


def test_detect_device_kind_desktop():
    assert _detect_device_kind(_CHROME_WIN) == "Desktop"


def test_detect_device_brand_apple():
    _, brand, model = _detect_device_brand(_IPHONE_SAFARI)
    assert brand == "Apple"
    assert model == "iPhone"


def test_detect_device_brand_samsung():
    _, brand, _ = _detect_device_brand("SM-G998B")
    assert brand == "Samsung"


def test_detect_device_brand_android_generic():
    ua = "Mozilla/5.0 (Linux; Android 13; Acme X1 Build/TPB5.220623.001)"
    _, brand, model = _detect_device_brand(ua)
    assert model is not None


def test_detect_device_brand_none():
    token, brand, model = _detect_device_brand(_CHROME_WIN)
    assert brand is None


def test_extract_languages_found():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; en-US)"
    langs = _extract_languages(ua)
    assert "en-US" in langs


def test_extract_languages_two_letter():
    ua = "Mozilla/5.0 (X11; Linux x86_64; de)"
    langs = _extract_languages(ua)
    assert "de" in langs


def test_extract_languages_none():
    langs = _extract_languages("curl/7.81.0")
    assert langs == []


def test_extract_languages_invalid_head():
    assert _extract_languages("Mozilla/5.0 (X11; EN)") == []
    assert _extract_languages("Mozilla/5.0 (X11; 12)") == []
    assert _extract_languages("Mozilla/5.0 (X11; EN-US)") == []
    assert _extract_languages("Mozilla/5.0 (X11; a1)") == []


def test_detect_crawler_bot():
    assert _detect_crawler(_GOOGLEBOT)
    assert not _detect_crawler(_CHROME_WIN)


def test_extract_browser_rendering():
    info = _parse_ua(_CHROME_WIN)
    assert info.rendering == "KHTML, like Gecko"


def test_extract_browser_rendering_khtml_only():
    ua = "Mozilla/5.0 (compatible; Konqueror/5; KHTML)"
    info = _parse_ua(ua)
    assert info.rendering == "KHTML"


def test_extract_browser_no_comment():
    info = _parse_ua("curl/7.81.0")
    assert info.comment is None


def test_normalize_user_agent_bytes():
    result = normalize_user_agent(b"curl/7.81.0")
    assert result == "curl/7.81.0"


def test_normalize_user_agent_none():
    assert normalize_user_agent(None) == ""


def test_normalize_user_agent_non_string():
    result = normalize_user_agent(123)
    assert result == "123"


def test_normalize_user_agent_strips_newlines():
    result = normalize_user_agent("curl/7.81.0\r\n extra")
    assert "\r" not in result and "\n" not in result


def test_parse_with_browser():
    result = parse(_CHROME_WIN)
    assert isinstance(result, UserAgent)
    assert result.browser == "Chrome"


def test_parse_caches():
    result1 = parse(_CHROME_WIN)
    result2 = parse(_CHROME_WIN)
    assert result1 is result2


def test_parse_or_none_valid():
    result = parse_or_none(_CHROME_WIN)
    assert result is not None


def test_parse_or_none_empty():
    assert parse_or_none(None) is None
    assert parse_or_none("") is None


def test_is_crawler_true():
    assert is_crawler(_GOOGLEBOT)


def test_is_crawler_false():
    assert not is_crawler(_CHROME_WIN)


def test_is_browser_true():
    assert is_browser(_CHROME_WIN)


def test_is_browser_false():
    assert not is_browser(_GOOGLEBOT)


def test_user_agent_to_dict():
    result = parse(_CHROME_WIN).to_dict()
    assert "raw" in result and "is_crawler" in result and "browser" in result


def test_detect_os_macos_no_version():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    os_name, _ = _detect_os(ua)
    assert os_name == "macOS"


def test_detect_os_ios_cpu_os():
    ua = "Mozilla/5.0 (CPU OS 17_0 like Mac OS X)"
    os_name, _ = _detect_os(ua)
    assert os_name == "iOS"


def test_read_dotted_no_leading_int():
    assert _read_dotted("abc", 0, 2) is None


def test_read_dotted_stops_on_non_int_after_dot():
    assert _read_dotted("1.x.3", 0, 2) == "1"


def test_underscore_version_no_separator():
    assert _underscore_version("17x0", 0) is None


def test_underscore_version_no_second_int():
    assert _underscore_version("17_x", 0) is None


def test_underscore_version_three_parts():
    assert _underscore_version("17_0_1", 0) == "17.0.1"


def test_underscore_version_two_parts():
    assert _underscore_version("17_0 ", 0) == "17.0"


def test_mac_version_invalid_separator():
    assert _mac_version("10x15", 0) is None


def test_mac_version_no_second_int():
    assert _mac_version("10._x", 0) is None


def test_mac_version_three_parts():
    assert _mac_version("10.15.7", 0) == "10.15.7"


def test_mac_version_two_parts():
    assert _mac_version("10.15 ", 0) == "10.15"


def test_ios_version_not_found():
    assert _ios_version("Mozilla/5.0 (Linux; Android 13)") is None


def test_android_version_not_found():
    assert _android_version("Mozilla/5.0 (Linux; X11)") is None


def test_find_paren_contents_unclosed():
    assert _find_paren_contents("foo (unclosed") == []


def test_find_paren_contents_multiple():
    result = _find_paren_contents("(a) (b)")
    assert result == ["a", "b"]


def test_detect_browser_opera_mini_presto():
    ua = "Opera/9.80 (J2ME/MIDP; Opera Mini/9.80; U; en) Presto/2.12.407 Version/12.50"
    browser, version = _detect_browser(ua)
    assert browser == "Opera Mini"
    assert version is not None


def test_detect_browser_opera_mobile_presto():
    ua = "Opera/9.80 (Android; Opera Mobi/46154; U; en) Presto/2.11.355 Version/12.10"
    browser, version = _detect_browser(ua)
    assert browser == "Opera Mobile"
    assert version is not None


def test_detect_browser_opera_presto():
    ua = "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.12.388 Version/12.17"
    browser, version = _detect_browser(ua)
    assert browser == "Opera"
    assert version == "12.17"


def test_detect_browser_ie_trident_no_msie():
    ua = "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko"
    browser, version = _detect_browser(ua)
    assert browser == "IE"
    assert version == "11.0"


def test_detect_browser_mobile_safari_applewebkit_fallback():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/19A346"
    browser, version = _detect_browser(ua)
    assert browser == "Mobile Safari"
    assert version is not None


def test_detect_browser_safari_no_version():
    ua = "Mozilla/5.0 (Macintosh) AppleWebKit/605.1.15 Safari/604.1"
    browser, version = _detect_browser(ua)
    assert browser == "Safari"
    assert version is not None


def test_detect_browser_apple_mail():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    browser, version = _detect_browser(ua)
    assert browser == "Apple Mail"
    assert version is not None


def test_detect_os_windows_phone_version():
    ua = "Mozilla/5.0 (compatible; MSIE 10.0; Windows Phone 8.0; Trident/6.0)"
    os_name, os_version = _detect_os(ua)
    assert os_name == "Windows Phone"
    assert os_version == "8.0"


def test_detect_os_windows_ce():
    ua = "Mozilla/4.0 (compatible; MSIE 4.01; Windows CE)"
    os_name, os_version = _detect_os(ua)
    assert os_name == "Windows"
    assert os_version == "CE"


def test_detect_os_windows_nt_no_dot():
    ua = "Mozilla/5.0 (Windows NT; U; en)"
    os_name, os_version = _detect_os(ua)
    assert os_name == "Windows"
    assert os_version == "NT"


def test_detect_os_cros_direct_branch():
    ua = "Mozilla/5.0 (X11; CrOS x86_64 14268.67.0) AppleWebKit/537.36"
    os_name, os_version = _detect_os(ua)
    assert os_name == "Chromium OS"
    assert os_version is not None


def test_direct_os_version_symbian():
    assert _direct_os_version("SymbianOS/9.4", "Symbian") == "9.4"
    assert _direct_os_version("Symbian/9.1", "Symbian") == "9.1"
    assert _direct_os_version("S60/3.0", "Symbian") == "3.0"


def test_direct_os_version_kaios():
    assert _direct_os_version("KaiOS/2.5", "KaiOS") == "2.5"


def test_direct_os_version_tizen_space():
    assert _direct_os_version("Tizen 5.0", "Tizen") == "5.0"


def test_direct_os_version_tizen_slash():
    assert _direct_os_version("Tizen/4.0", "Tizen") == "4.0"


def test_direct_os_version_netbsd():
    assert _direct_os_version("NetBSD 9.0", "NetBSD") == "9.0"
    assert _direct_os_version("NetBSD/9.1", "NetBSD") == "9.1"


def test_direct_os_version_openbsd():
    assert _direct_os_version("OpenBSD 7.0", "OpenBSD") == "7.0"
    assert _direct_os_version("OpenBSD/6.9", "OpenBSD") == "6.9"


def test_direct_os_version_webos():
    assert _direct_os_version("webOS/2.1", "webOS") == "2.1"
    assert _direct_os_version("hpwOS/3.0", "webOS") == "3.0"


def test_direct_os_version_returns_none_for_unknown():
    assert _direct_os_version("SunOS 5.11", "Solaris") is None


def test_cros_version_no_cros():
    assert _cros_version("no cros here") is None


def test_cros_version_with_paren_end():
    assert _cros_version("CrOS )") is None


def test_cros_version_with_digits():
    assert _cros_version("Mozilla/5.0 (X11; CrOS x86_64 14268.67.0)") == "14268.67.0"


def test_distro_version_slash():
    assert _distro_version("Ubuntu/22.04", "Ubuntu") == "22.04"


def test_distro_version_space():
    assert _distro_version("Ubuntu 22.04", "Ubuntu") == "22.04"


def test_distro_version_none():
    assert _distro_version("curl/7.81.0", "Ubuntu") is None


def test_linux_kernel_version_no_linux():
    assert _linux_kernel_version("curl/7.81.0") is None


def test_linux_kernel_version_with_digit():
    assert _linux_kernel_version("Mozilla/5.0 (Linux 5.15.0; ...)") == "5.15.0"


def test_detect_device_brand_tesla():
    token, brand, model = _detect_device_brand("Tesla/1.0 QtCarBrowser")
    assert brand == "Tesla"
    assert model == "Tesla"


# --- field coverage fixtures ---

_FIELDS = ("browser", "browser_version", "os", "os_version", "device", "device_brand")
_FIELD_THRESHOLDS = {
    "browser": 0.98,
    "browser_version": 0.98,
    "os": 0.98,
    "os_version": 0.79,
    "device": 0.99,
    "device_brand": 0.51,
}


def _field_rate(uas: list[str], field: str) -> float:
    return sum(1 for ua in uas if getattr(parse(ua), field) is not None) / len(uas)


def test_fixture_browser_browser_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "browser")
    assert rate >= _FIELD_THRESHOLDS["browser"], f"browser coverage {rate:.2%}"


def test_fixture_browser_browser_version_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "browser_version")
    assert rate >= _FIELD_THRESHOLDS["browser_version"], (
        f"browser_version coverage {rate:.2%}"
    )


def test_fixture_browser_os_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "os")
    assert rate >= _FIELD_THRESHOLDS["os"], f"os coverage {rate:.2%}"


def test_fixture_browser_os_version_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "os_version")
    assert rate >= _FIELD_THRESHOLDS["os_version"], f"os_version coverage {rate:.2%}"


def test_fixture_browser_device_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "device")
    assert rate >= _FIELD_THRESHOLDS["device"], f"device coverage {rate:.2%}"


def test_fixture_browser_device_brand_field_coverage():
    uas = _load("browser_user_agents.txt")
    rate = _field_rate(uas, "device_brand")
    assert rate >= _FIELD_THRESHOLDS["device_brand"], f"device_brand coverage {rate:.2%}"


def test_webview_flag():
    ua = "Mozilla/5.0 (Linux; Android 10; SM-G960F; wv) Chrome/90 Mobile Safari/537.36"
    assert parse(ua).is_webview


def test_headless_flag():
    assert parse("Mozilla/5.0 HeadlessChrome/120.0").is_headless
    assert parse("PhantomJS/2.1").is_headless


def test_browser_channel():
    assert parse("Mozilla/5.0 Chrome Canary/121").channel == "canary"
    assert parse("Mozilla/5.0 Firefox Nightly/120").channel == "nightly"
    assert parse("Mozilla/5.0 Chrome/120 Beta/1").channel == "beta"


def test_app_detection():
    ua = "Mozilla/5.0 (Linux; Android) FBAV/300.0.0.0"
    parsed = parse(ua)
    assert parsed.app == "Facebook"
    assert parsed.app_version == "300.0.0.0"


def test_engine_servo():
    assert parse("Mozilla/5.0 (Mobile; rv:48.0) Servo/1.0").engine == "Servo"


def test_engine_edgehtml():
    ua = "Mozilla/5.0 Edge/12.246"
    assert parse(ua).engine == "EdgeHTML"


def test_windows_11_arm():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; arm) Chrome/120"
    assert parse(ua).os_version == "11"


def test_ipados_masquerading_as_mac():
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605 "
        "Mobile/15E148 Safari/604"
    )
    assert parse(ua).os == "iPadOS"


def test_harmonyos_version():
    ua = "Mozilla/5.0 (Linux; HarmonyOS 4.0.0) AppleWebKit/537"
    parsed = parse(ua)
    assert parsed.os == "HarmonyOS"
    assert parsed.os_version == "4.0.0"


def test_xr_device():
    assert parse("Mozilla/5.0 (Linux; Quest 3) AppleWebKit/537").device == "XR"


def test_wearable_device():
    assert parse("Mozilla/5.0 (Wear OS 4.0) AppleWebKit/537").device == "Wearable"


def test_librewolf_browser():
    assert parse("Mozilla/5.0 LibreWolf/120.0").browser == "LibreWolf"


def test_arc_browser():
    assert parse("Mozilla/5.0 Chrome/120 Arc/1.50.0").browser == "Arc"


def test_fixture_crawler_detected_pass_rate():
    uas = _load("crawler_user_agents.txt")
    detected = sum(1 for ua in uas if is_crawler(ua))
    rate = detected / len(uas)
    assert rate >= 0.75, f"pass rate {rate:.2%} ({detected}/{len(uas)})"


def test_fixture_pgts_crawlers_pass_rate():
    uas = _load("crawler_user_agents_pgts.txt")
    detected = sum(1 for ua in uas if is_crawler(ua))
    rate = detected / len(uas)
    assert rate >= 0.70, f"pass rate {rate:.2%} ({detected}/{len(uas)})"


def test_fixture_browser_extended_not_detected():
    uas = _load("browser_user_agents_extended.txt")
    misses = sum(1 for ua in uas if is_crawler(ua))
    rate = (len(uas) - misses) / len(uas)
    assert rate >= 0.999, f"pass rate {rate:.4%} (misses={misses}/{len(uas)})"


def test_fixture_browser_extended_browser_field_coverage():
    uas = _load("browser_user_agents_extended.txt")
    rate = _field_rate(uas, "browser")
    assert rate >= 0.96, f"browser coverage {rate:.2%}"


def test_fixture_browser_extended_os_field_coverage():
    uas = _load("browser_user_agents_extended.txt")
    rate = _field_rate(uas, "os")
    assert rate >= 0.97, f"os coverage {rate:.2%}"


def test_fixture_browser_extended_device_field_coverage():
    uas = _load("browser_user_agents_extended.txt")
    rate = _field_rate(uas, "device")
    assert rate >= 0.99, f"device coverage {rate:.2%}"


def test_fixture_browser_not_detected_pass_rate():
    uas = _load("browser_user_agents.txt")
    misses = sum(1 for ua in uas if is_crawler(ua))
    rate = (len(uas) - misses) / len(uas)
    assert rate >= 0.99, f"pass rate {rate:.4%} (misses={misses}/{len(uas)})"


def test_fixture_loadkpi_crawlers_pass_rate():
    uas = _load("loadkpi_crawlers.txt")
    detected = sum(1 for ua in uas if is_crawler(ua))
    rate = detected / len(uas)
    assert rate >= 0.62, f"pass rate {rate:.2%} ({detected}/{len(uas)})"


# --- browser detection: more real-world UAs ---


def test_detect_browser_vivaldi():
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Vivaldi/6.7.3329.21"
    )
    assert parse(ua).browser == "Vivaldi"


def test_detect_browser_duckduckgo():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 "
        "DuckDuckGo/7 Safari/604.1"
    )
    assert parse(ua).browser == "DuckDuckGo"


def test_detect_browser_yandex():
    ua = (
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36 YaBrowser/23.1"
    )
    assert parse(ua).browser == "Yandex"


def test_detect_browser_uc_browser():
    ua = "Mozilla/5.0 (Linux; U; Android 9) AppleWebKit/537.36 UCBrowser/13.4 Mobile Safari/537.36"
    assert parse(ua).browser == "UC Browser"


def test_detect_browser_silk():
    ua = (
        "Mozilla/5.0 (Linux; Android 9; KFMAWI) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Silk/95.3.2 like Chrome/95.0 Safari/537.36"
    )
    assert parse(ua).browser == "Silk"


def test_detect_browser_miui():
    ua = (
        "Mozilla/5.0 (Linux; Android 12; Redmi Note 9) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/89.0 Mobile Safari/537.36 MiuiBrowser/14.0"
    )
    assert parse(ua).browser == "MIUI Browser"


def test_detect_browser_huawei():
    ua = (
        "Mozilla/5.0 (Linux; Android 12; ELS-NX9) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/99.0 Mobile Safari/537.36 HuaweiBrowser/13.0"
    )
    assert parse(ua).browser == "Huawei Browser"


def test_detect_browser_torbrowser():
    ua = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0 TorBrowser/13.0"
    assert parse(ua).browser == "Tor Browser"


def test_detect_browser_waterfox():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0 Waterfox/102.2"
    assert parse(ua).browser == "Waterfox"


def test_detect_browser_palemoon():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Goanna/6 Firefox/102.0 PaleMoon/32.0"
    assert parse(ua).browser == "PaleMoon"


def test_detect_browser_seamonkey():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.9) Gecko/20100101 Firefox/60.9 SeaMonkey/2.53"
    assert parse(ua).browser == "SeaMonkey"


def test_detect_browser_konqueror():
    ua = "Mozilla/5.0 (compatible; Konqueror/4.0; Linux; X11)"
    assert parse(ua).browser == "Konqueror"


def test_detect_browser_lynx():
    ua = "Lynx/2.9.0dev.6 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/3.6.15"
    assert parse(ua).browser == "Lynx"


def test_detect_browser_elinks():
    ua = "ELinks/0.15.0 (textmode; Linux 5.10.0 x86_64; 220x50)"
    assert parse(ua).browser == "ELinks"


def test_detect_browser_w3m():
    ua = "w3m/0.5.3+git20230121"
    assert parse(ua).browser == "w3m"


def test_detect_browser_snapchat():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Snapchat/12.57.0.49"
    )
    assert parse(ua).browser == "Snapchat"


def test_detect_browser_instagram():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "Instagram 320.0.0.0.0"
    )
    assert parse(ua).browser == "Instagram"


def test_detect_browser_tiktok():
    ua = (
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36 TikTok/29.0"
    )
    assert parse(ua).browser == "TikTok"


def test_detect_browser_pinterest():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Pinterest/12.0"
    )
    assert parse(ua).browser == "Pinterest"


def test_detect_browser_wechat():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.42"
    )
    assert parse(ua).browser == "WeChat"


def test_detect_browser_linkedin():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "LinkedInApp/9.28.4389"
    )
    assert parse(ua).browser == "LinkedIn"


def test_detect_browser_qq():
    ua = (
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36 QQBrowser/14.9"
    )
    assert parse(ua).browser == "QQBrowser"


def test_detect_browser_floorp():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 Floorp/11.0"
    assert parse(ua).browser == "Floorp"


def test_detect_browser_mullvad():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0 MullvadBrowser/13.0"
    assert parse(ua).browser == "Mullvad Browser"


def test_detect_browser_curl():
    assert parse("curl/8.5.0").browser == "curl"
    assert parse("curl/8.5.0").browser_version == "8.5.0"


def test_detect_browser_wget():
    assert parse("Wget/1.21.4").browser == "Wget"
    assert parse("Wget/1.21.4").browser_version == "1.21.4"


def test_detect_browser_httpie():
    assert parse("HTTPie/3.2.2").browser == "HTTPie"


def test_detect_browser_python_urllib():
    assert parse("Python-urllib/3.11").browser == "Python urllib"


def test_detect_browser_aiohttp():
    assert parse("aiohttp/3.9.1").browser == "aiohttp"


def test_detect_browser_httpx():
    assert parse("python-httpx/0.27.0").browser == "httpx"


def test_detect_browser_go_http():
    assert parse("Go-http-client/2.0").browser == "Go-http-client"


def test_detect_browser_okhttp():
    assert parse("okhttp/4.12.0").browser == "OkHttp"


def test_detect_browser_node_fetch():
    assert parse("node-fetch/3.3.2").browser == "node-fetch"


def test_detect_browser_axios():
    assert parse("axios/1.6.8").browser == "axios"


def test_detect_browser_postman():
    assert parse("PostmanRuntime/7.37.0").browser == "PostmanRuntime"


def test_detect_browser_guzzle():
    assert parse("GuzzleHttp/7.8.1 curl/8.5.0 PHP/8.3.0").browser == "Guzzle"


def test_detect_browser_php():
    assert parse("PHP/8.3.0").browser == "PHP"


# --- OS detection: more real-world cases ---


def test_detect_os_windows_8_1():
    ua = "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    assert parse(ua).os_version == "8.1"


def test_detect_os_windows_7():
    ua = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    assert parse(ua).os_version == "7"


def test_detect_os_windows_vista():
    ua = "Mozilla/5.0 (Windows NT 6.0; Win64; x64) AppleWebKit/537.36 Chrome/50 Safari/537.36"
    assert parse(ua).os_version == "Vista"


def test_detect_os_windows_xp():
    ua = "Mozilla/5.0 (Windows NT 5.1; rv:52.0) Gecko/20100101 Firefox/52.0"
    assert parse(ua).os_version == "XP"


def test_detect_os_android_version():
    ua = (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.os == "Android"
    assert parsed.os_version is not None and parsed.os_version.startswith("14")


def test_detect_os_tizen():
    ua = "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.5) AppleWebKit/538.1 (KHTML, like Gecko) Version/6.5 TV Safari/538.1"
    parsed = parse(ua)
    assert parsed.os == "Tizen"
    assert parsed.os_version == "6.5"


def test_detect_os_kaios():
    ua = "Mozilla/5.0 (Mobile; KaiOS/2.5.2; rv:48.0) Gecko/48.0 Firefox/48.0"
    parsed = parse(ua)
    assert parsed.os == "KaiOS"
    assert parsed.os_version == "2.5.2"


def test_detect_os_harmonyos():
    ua = "Mozilla/5.0 (Linux; HarmonyOS 3.1; ELS-NX9) AppleWebKit/537.36 Chrome/99 Mobile Safari/537.36"
    parsed = parse(ua)
    assert parsed.os == "HarmonyOS"
    assert parsed.os_version == "3.1"


def test_detect_os_webos():
    ua = "Mozilla/5.0 (webOS/1.4.5; U; en-US) AppleWebKit/532.2 (KHTML, like Gecko) Version/1.0 Safari/532.2 Pre/1.0"
    assert parse(ua).os == "webOS"


def test_detect_os_haiku():
    ua = "Mozilla/5.0 (compatible; Haiku; U; BePC; Haiku) AppleWebKit/527"
    assert parse(ua).os == "Haiku"


def test_detect_os_os2():
    ua = "Mozilla/5.0 (OS/2; Warp; U; de) AppleWebKit/533.3"
    assert parse(ua).os == "OS/2"


def test_detect_os_amigaos():
    ua = "Mozilla/5.0 (AmigaOS 4.1; U; de) AppleWebKit/533.3"
    assert parse(ua).os == "AmigaOS"


def test_detect_os_solaris():
    ua = "Mozilla/5.0 (SunOS x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"
    assert parse(ua).os == "Solaris"


def test_detect_os_dragonfly():
    ua = "Mozilla/5.0 (DragonFly amd64; rv:78.0) Gecko/20100101 Firefox/78.0"
    assert parse(ua).os == "DragonFly"


def test_detect_os_playstation():
    ua = "Mozilla/5.0 (PlayStation 5 3.00) AppleWebKit/605.1.15 (KHTML, like Gecko)"
    assert parse(ua).os == "PlayStation"


def test_detect_os_nintendo():
    ua = "Mozilla/5.0 (Nintendo Switch; WifiWebAuthApplet) AppleWebKit/609.4 (KHTML, like Gecko)"
    assert parse(ua).os == "Nintendo"


def test_detect_os_windows_phone():
    ua = "Mozilla/5.0 (compatible; MSIE 10.0; Windows Phone 8.0; Trident/6.0; IEMobile/10.0)"
    parsed = parse(ua)
    assert parsed.os == "Windows Phone"
    assert parsed.os_version == "8.0"


def test_detect_os_ubuntu():
    ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
    assert parse(ua).os == "Ubuntu"


def test_detect_os_fedora():
    ua = "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
    assert parse(ua).os == "Fedora"


# --- device detection: more real-world cases ---


def test_detect_device_pixel():
    ua = (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "Google"


def test_detect_device_oneplus():
    ua = (
        "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "OnePlus"


def test_detect_device_nokia():
    ua = (
        "Mozilla/5.0 (Linux; Android 12; Nokia G50) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "Nokia"


def test_detect_device_sony():
    ua = (
        "Mozilla/5.0 (Linux; Android 12; Sony XPERIA 1 IV) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "Sony"


def test_detect_device_xiaomi_redmi():
    ua = (
        "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0 Mobile Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "Xiaomi"


def test_detect_device_console_playstation():
    ua = "Mozilla/5.0 (PlayStation 5 3.00) AppleWebKit/605.1.15 (KHTML, like Gecko)"
    assert parse(ua).device == "Console"


def test_detect_device_console_nintendo():
    ua = "Mozilla/5.0 (Nintendo Switch; WifiWebAuthApplet) AppleWebKit/609.4 (KHTML, like Gecko)"
    assert parse(ua).device == "Console"


def test_detect_device_smarttv_hbbtv():
    ua = "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.5) AppleWebKit/538.1 TV Safari/538.1"
    assert parse(ua).device == "SmartTV"


def test_detect_device_tablet_ipad():
    ua = _IPAD_SAFARI
    assert parse(ua).device == "Tablet"
    assert parse(ua).is_tablet


def test_detect_device_mobile_android():
    ua = _MOBILE_CHROME
    parsed = parse(ua)
    assert parsed.device == "Mobile"
    assert parsed.is_mobile


def test_detect_device_wearable_wear_os():
    ua = "Mozilla/5.0 (Linux; Android 13; Wear OS 4) AppleWebKit/537.36"
    assert parse(ua).device == "Wearable"


def test_detect_device_xr_quest():
    ua = "Mozilla/5.0 (Linux; Android 10; Quest 2) AppleWebKit/537.36"
    assert parse(ua).device == "XR"


def test_detect_device_kindle_fire():
    ua = (
        "Mozilla/5.0 (Linux; Android 9; KFAPWI Build/PS7528) "
        "AppleWebKit/537.36 Silk/95.3.2 like Chrome/95.0 Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.device_brand == "Amazon"


def test_detect_device_roku():
    ua = "Roku/DVP-12.0 (122.00E04170A)"
    parsed = parse(ua)
    assert parsed.device_brand == "Roku"


# --- CPU detection ---


def test_detect_cpu_arm():
    assert _detect_cpu("armv7l") == "arm"


def test_detect_cpu_arm64_aarch64():
    assert _detect_cpu("Mozilla/5.0 (Linux; aarch64)") == "arm64"


def test_detect_cpu_wow64():
    ua = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36"
    assert _detect_cpu(ua) == "x86_64"


def test_detect_cpu_ppc():
    ua = "Mozilla/5.0 (Macintosh; PPC Mac OS X) AppleWebKit/125"
    assert _detect_cpu(ua) == "ppc"


def test_detect_cpu_i386():
    ua = "Mozilla/5.0 (X11; Linux i386; rv:109.0) Gecko/20100101 Firefox/115.0"
    assert _detect_cpu(ua) == "x86"


# --- language extraction ---


def test_extract_languages_multi():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; en-US; fr-FR)"
    langs = _extract_languages(ua)
    assert "en-US" in langs
    assert "fr-FR" in langs


def test_extract_languages_zh_cn():
    ua = "Mozilla/5.0 (Linux; U; Android 10; zh-CN; Mi 9T Pro) AppleWebKit/537.36"
    langs = _extract_languages(ua)
    assert "zh-CN" in langs


# --- parse / UserAgent fields ---


def test_parse_is_mobile_iphone():
    assert parse(_IPHONE_SAFARI).is_mobile


def test_parse_is_tablet_ipad():
    assert parse(_IPAD_SAFARI).is_tablet


def test_parse_not_mobile_desktop():
    assert not parse(_CHROME_WIN).is_mobile


def test_parse_engine_version_blink():
    parsed = parse(_CHROME_WIN)
    assert parsed.engine == "Blink"
    assert parsed.engine_version is not None


def test_parse_browser_major():
    parsed = parse(_CHROME_WIN)
    assert parsed.browser_major == "120"


def test_parse_languages():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; en-US) Chrome/120 Safari/537.36"
    parsed = parse(ua)
    assert "en-US" in parsed.languages


def test_parse_to_dict_complete():
    result = parse(_MOBILE_CHROME).to_dict()
    assert result["is_mobile"]
    assert result["browser"] == "Mobile Chrome"
    assert result["os"] == "Android"


def test_normalize_user_agent_strips_cr_lf():
    assert "\r" not in normalize_user_agent("curl/7.81.0\r\n")
    assert "\n" not in normalize_user_agent("curl/7.81.0\r\n")


def test_normalize_user_agent_int():
    assert normalize_user_agent(42) == "42"


def test_parse_or_none_crawler():
    result = parse_or_none("Googlebot/2.1 (+http://www.google.com/bot.html)")
    assert result is not None
    assert result.is_crawler


def test_is_browser_crawler_returns_false():
    assert not is_browser("Googlebot/2.1 (+http://www.google.com/bot.html)")


def test_headless_selenium():
    assert parse("Mozilla/5.0 Selenium/4.0").is_headless


def test_headless_puppeteer():
    assert parse("Mozilla/5.0 Puppeteer/21.0").is_headless


def test_headless_playwright():
    assert parse("Mozilla/5.0 Playwright/1.40").is_headless


def test_headless_cypress():
    assert parse("Mozilla/5.0 Cypress/13.0").is_headless


def test_headless_webdriver():
    assert parse("Mozilla/5.0 WebDriver/1.0").is_headless


def test_channel_dev():
    assert parse("Mozilla/5.0 Chrome/120 Dev/1").channel == "dev"


def test_channel_aurora():
    assert parse("Mozilla/5.0 Firefox/120 aurora").channel == "aurora"


def test_app_instagram():
    ua = (
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "Mobile Safari/537.36 Instagram 320.0.0.0.0"
    )
    parsed = parse(ua)
    assert parsed.app == "Instagram"


def test_app_snapchat():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Snapchat/12.57"
    parsed = parse(ua)
    assert parsed.app == "Snapchat"


def test_app_twitter():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Twitter for iPhone/9.0"
    parsed = parse(ua)
    assert parsed.app == "Twitter"


def test_webview_wkwebview():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) WKWebView/605.1"
    assert parse(ua).is_webview


def test_webview_fban():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Mobile/15E148 FBAN/FBIOS"
    )
    assert parse(ua).is_webview


def test_windows_11_detection():
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    parsed = parse(ua)
    assert parsed.os == "Windows"
    assert parsed.os_version in ("10/11", "10", "11")


def test_detect_browser_edge_ios():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) EdgiOS/120.0 Mobile/15E148"
    assert parse(ua).browser == "Edge"


def test_detect_browser_edge_android():
    ua = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 EdgA/120.0 Mobile Safari/537.36"
    assert parse(ua).browser == "Edge"


def test_detect_browser_opera_touch():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) OPT/4.0 Mobile Safari/604.1"
    assert parse(ua).browser == "Opera Touch"


def test_detect_os_blackberry_bb10():
    ua = "Mozilla/5.0 (BB10; Smartphone) AppleWebKit/765 (KHTML, like Gecko) Version/10.3"
    assert parse(ua).os == "BlackBerry"


def test_detect_os_windows_mobile():
    ua = "Mozilla/4.0 (compatible; MSIE 4.01; Windows Mobile; PPC)"
    assert parse(ua).os in ("Windows Mobile", "Windows")


def test_detect_device_brand_htc():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 4.0; HTC One X)")
    assert brand == "HTC"


def test_detect_device_brand_lg():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 9; LG-G8)")
    assert brand == "LG"


def test_detect_device_brand_motorola():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 11; Moto G Power)")
    assert brand == "Motorola"


def test_detect_device_brand_oppo():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 12; OPPO A96)")
    assert brand == "Oppo"


def test_detect_device_brand_vivo():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 12; vivo Y35)")
    assert brand == "Vivo"


def test_detect_device_brand_realme():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Linux; Android 12; realme 9 Pro)")
    assert brand == "Realme"


def test_detect_device_brand_surface():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Windows NT 10.0; Surface Pro 9)")
    assert brand == "Microsoft"


def test_detect_device_brand_lumia():
    _, brand, _ = _detect_device_brand("Mozilla/5.0 (Windows Phone; Lumia 950)")
    assert brand == "Microsoft"


def test_detect_device_brand_blackberry():
    _, brand, _ = _detect_device_brand("BlackBerry9700/5.0")
    assert brand == "BlackBerry"
