import io
import json
from unittest.mock import patch

from is_crawler import __version__
from is_crawler.__main__ import _analyze, _iter_inputs, main

_GOOGLEBOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"


def test_analyze_crawler():
    result = _analyze(_GOOGLEBOT)
    assert result["is_crawler"] is True
    assert result["name"] == "Googlebot"
    assert result["version"] == "2.1"
    assert result["url"] == "http://www.google.com/bot.html"
    assert "bot_signal" in result["signals"]
    assert "bot" in result["matches"]
    assert result["info"] is not None
    assert result["info"]["tags"] == ("search-engine",)


def test_analyze_browser():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    result = _analyze(ua)
    assert result["is_crawler"] is False
    assert result["info"] is None


def test_iter_inputs_argv():
    assert list(_iter_inputs(["Googlebot/2.1"])) == ["Googlebot/2.1"]


def test_iter_inputs_argv_multi_words():
    assert list(_iter_inputs(["My", "Bot/1.0"])) == ["My Bot/1.0"]


def test_iter_inputs_stdin():
    fake_stdin = io.StringIO("BotA\nBotB\n\nBotC\n")
    with patch("sys.stdin", fake_stdin):
        items = list(_iter_inputs([]))
    assert items == ["BotA", "BotB", "BotC"]


def test_iter_inputs_stdin_crlf_and_whitespace():
    fake_stdin = io.StringIO("BotA\r\n  \r\n BotB \r\n")
    with patch("sys.stdin", fake_stdin):
        items = list(_iter_inputs([]))
    assert items == ["BotA", "BotB"]


def _run(*argv, stdin=None):
    patches = [patch("sys.argv", ["prog", *argv])]
    if stdin is not None:
        patches.append(patch("sys.stdin", io.StringIO(stdin)))
    for p in patches:
        p.start()
    try:
        return main()
    finally:
        for p in patches:
            p.stop()


def test_main_argv(capsys):
    assert _run(_GOOGLEBOT) == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["is_crawler"] is True
    assert data["name"] == "Googlebot"


def test_main_detect_explicit(capsys):
    assert _run("detect", _GOOGLEBOT) == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["is_crawler"] is True


def test_main_pretty(capsys):
    assert _run("--pretty", _GOOGLEBOT) == 0
    out = capsys.readouterr().out
    assert "\n  " in out
    assert json.loads(out)["name"] == "Googlebot"


def test_main_stdin(capsys):
    assert _run(stdin=_GOOGLEBOT + "\n") == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["is_crawler"] is True


def test_main_stdin_multiple(capsys):
    ua_browser = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    _run(stdin=f"{_GOOGLEBOT}\n{ua_browser}\n")
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["is_crawler"] is True
    assert json.loads(lines[1])["is_crawler"] is False


def test_main_stdin_crlf(capsys):
    assert _run(stdin=_GOOGLEBOT + "\r\n") == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["name"] == "Googlebot"


def test_main_parse(capsys):
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )
    assert _run("parse", ua) == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["browser"] == "Chrome"
    assert data["os"] == "Windows"


def test_main_verify(capsys):
    targets = "is_crawler.__main__"
    with (
        patch(f"{targets}.verify_crawler_ip", return_value=True),
        patch(f"{targets}.known_crawler_ip", return_value=True),
        patch(f"{targets}.reverse_dns", return_value="crawl-66-249.googlebot.com"),
        patch(f"{targets}.known_crawler_rdns", return_value=True),
    ):
        assert _run("verify", "Googlebot/2.1", "66.249.66.1") == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["verified"] is True
    assert data["ip"] == "66.249.66.1"
    assert data["user_agent"] == "Googlebot/2.1"


def test_main_verify_missing_args(capsys):
    assert _run("verify", "66.249.66.1") == 2
    assert "verify requires" in capsys.readouterr().err


def test_main_ip(capsys):
    targets = "is_crawler.__main__"
    with (
        patch(f"{targets}.known_crawler_ip", return_value=True),
        patch(f"{targets}.reverse_dns", return_value="dns.google"),
        patch(f"{targets}.known_crawler_rdns", return_value=False),
    ):
        assert _run("ip", "8.8.8.8", "66.249.66.1") == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["rdns"] == "dns.google"


def test_main_ip_missing_args(capsys):
    assert _run("ip") == 2
    assert "ip requires" in capsys.readouterr().err


def test_main_robots(capsys):
    assert _run("robots", "--disallow", "ai-crawler", "--path", "/private") == 0
    out = capsys.readouterr().out
    assert "Disallow: /private" in out
    assert "User-agent:" in out


def test_main_robots_empty(capsys):
    assert _run("robots") == 0
    assert capsys.readouterr().out == ""


def test_main_ai_txt(capsys):
    assert _run("ai-txt") == 0
    out = capsys.readouterr().out
    assert "Disallow: /" in out
    assert "User-Agent:" in out


def test_main_ai_txt_custom(capsys):
    assert _run("ai-txt", "--disallow", "scanner") == 0
    assert "Disallow: /" in capsys.readouterr().out


def test_main_help(capsys):
    for flag in ("-h", "--help"):
        assert _run(flag) == 0
        out = capsys.readouterr().out
        assert "Usage:" in out
        assert "--version" in out


def test_main_version(capsys):
    for flag in ("-V", "--version"):
        assert _run(flag) == 0
        assert capsys.readouterr().out.strip() == __version__


def test_main_unknown_flag(capsys):
    assert _run("--bogus") == 2
    err = capsys.readouterr().err
    assert "unknown option: --bogus" in err
    assert "Usage:" in err
