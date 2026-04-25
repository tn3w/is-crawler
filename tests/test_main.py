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


def test_main_help(capsys):
    for flag in ("-h", "--help"):
        with patch("sys.argv", ["prog", flag]):
            assert main() == 0
        out = capsys.readouterr().out
        assert "Usage:" in out
        assert "--version" in out


def test_main_version(capsys):
    for flag in ("-V", "--version"):
        with patch("sys.argv", ["prog", flag]):
            assert main() == 0
        assert capsys.readouterr().out.strip() == __version__
