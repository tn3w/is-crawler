import asyncio
from unittest.mock import patch

from is_crawler.contrib import (
    ASGICrawlerMiddleware,
    CrawlerMiddlewareResult,
    WSGICrawlerMiddleware,
    _first_forwarded_ip,
    _forwarded_ip,
    _scope_header,
    _scope_ip,
    _should_block,
    _to_tags,
    _wsgi_ip,
)

_BOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"
_BROWSER = "Mozilla/5.0 (Windows NT 10.0) Chrome/120"


def test_to_tags_variants():
    assert _to_tags(None) == ()
    assert _to_tags("ai-crawler") == ("ai-crawler",)
    assert _to_tags(["ai-crawler", "scanner"]) == ("ai-crawler", "scanner")


def test_first_forwarded_ip_variants():
    assert _first_forwarded_ip(None) is None
    assert _first_forwarded_ip("  ") is None
    assert _first_forwarded_ip("1.2.3.4, 5.6.7.8") == "1.2.3.4"


def test_forwarded_ip_variants():
    assert _forwarded_ip(None) is None
    assert _forwarded_ip("for=1.2.3.4;proto=https;by=203.0.113.43") == "1.2.3.4"
    assert _forwarded_ip('for=""') is None
    assert _forwarded_ip('for="1.2.3.4:1234"') == "1.2.3.4"
    assert _forwarded_ip('for="[2001:db8:cafe::17]:4711"') == "2001:db8:cafe::17"
    assert _forwarded_ip('for="[2001:db8:cafe::17:4711"') is None
    assert _forwarded_ip("proto=https;by=203.0.113.43") is None


def test_wsgi_ip_prefers_forwarded_when_trusted():
    environ = {
        "HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8",
        "REMOTE_ADDR": "9.9.9.9",
    }
    assert _wsgi_ip(environ, True) == "1.2.3.4"


def test_wsgi_ip_prefers_standard_forwarded_when_trusted():
    environ = {
        "HTTP_FORWARDED": 'for="66.249.66.1:1234";proto=https',
        "HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8",
        "REMOTE_ADDR": "9.9.9.9",
    }
    assert _wsgi_ip(environ, True) == "66.249.66.1"


def test_wsgi_ip_falls_back_to_x_real_ip_when_trusted():
    environ = {
        "HTTP_X_REAL_IP": "1.2.3.4",
        "REMOTE_ADDR": "9.9.9.9",
    }
    assert _wsgi_ip(environ, True) == "1.2.3.4"


def test_wsgi_ip_falls_back_to_remote_addr():
    assert _wsgi_ip({"REMOTE_ADDR": "9.9.9.9"}, False) == "9.9.9.9"


def test_wsgi_ip_normalizes_remote_addr():
    assert _wsgi_ip({"REMOTE_ADDR": " 9.9.9.9 "}, False) == "9.9.9.9"
    assert _wsgi_ip({"REMOTE_ADDR": "   "}, False) is None


def test_scope_header_match_and_miss():
    scope = {"headers": [(b"user-agent", b"Googlebot/2.1")]}
    assert _scope_header(scope, b"user-agent") == "Googlebot/2.1"
    assert _scope_header(scope, b"x-forwarded-for") == ""


def test_scope_header_case_insensitive():
    scope = {"headers": [(b"User-Agent", b"Googlebot/2.1")]}
    assert _scope_header(scope, b"user-agent") == "Googlebot/2.1"


def test_scope_ip_forwarded_client_and_none():
    forwarded = {
        "headers": [(b"x-forwarded-for", b"1.2.3.4, 5.6.7.8")],
        "client": ("9.9.9.9", 1234),
    }
    assert _scope_ip(forwarded, True) == "1.2.3.4"
    assert (
        _scope_ip(
            {
                "headers": [(b"x-real-ip", b"1.2.3.4")],
                "client": ("9.9.9.9", 1234),
            },
            True,
        )
        == "1.2.3.4"
    )
    assert (
        _scope_ip(
            {
                "headers": [(b"forwarded", b'for="[2001:db8:cafe::17]:4711"')],
                "client": ("9.9.9.9", 1234),
            },
            True,
        )
        == "2001:db8:cafe::17"
    )
    assert _scope_ip({"client": ("9.9.9.9", 1234)}, False) == "9.9.9.9"
    assert _scope_ip({}, False) is None


def test_should_block_variants():
    browser = CrawlerMiddlewareResult(_BROWSER, None, False, None, False)
    crawler = CrawlerMiddlewareResult(_BOT, None, True, "Googlebot", False)
    assert _should_block(browser, ()) is False
    assert _should_block(crawler, ()) is True


def test_wsgi_middleware_attaches_context():
    seen = {}

    def app(environ, start_response):
        seen["result"] = environ["is_crawler"]
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    middleware = WSGICrawlerMiddleware(app)
    calls = []

    def start_response(status, headers):
        calls.append((status, headers))

    body = middleware(
        {
            "HTTP_USER_AGENT": _BOT,
            "REMOTE_ADDR": "66.249.66.1",
        },
        start_response,
    )

    assert body == [b"ok"]
    assert calls == [("200 OK", [("Content-Type", "text/plain")])]
    assert seen["result"].is_crawler is True
    assert seen["result"].name == "Googlebot"
    assert seen["result"].verified is False


def test_wsgi_middleware_check_ip_range_sets_flag():
    seen = {}

    def app(environ, start_response):
        seen["result"] = environ["is_crawler"]
        start_response("200 OK", [])
        return [b"ok"]

    middleware = WSGICrawlerMiddleware(app, check_ip_range=True)

    with patch("is_crawler.contrib.known_crawler_ip", return_value=True) as check:
        middleware(
            {"HTTP_USER_AGENT": _BROWSER, "REMOTE_ADDR": "66.249.66.1"},
            lambda status, headers: None,
        )

    check.assert_called_once_with("66.249.66.1")
    assert seen["result"].in_ip_range is True
    assert seen["result"].is_crawler is True


def test_wsgi_middleware_check_rdns_sets_flag():
    seen = {}

    def app(environ, start_response):
        seen["result"] = environ["is_crawler"]
        start_response("200 OK", [])
        return [b"ok"]

    middleware = WSGICrawlerMiddleware(app, check_rdns=True)

    with patch("is_crawler.contrib.known_crawler_rdns", return_value=True) as check:
        middleware(
            {"HTTP_USER_AGENT": _BROWSER, "REMOTE_ADDR": "66.249.66.1"},
            lambda status, headers: None,
        )

    check.assert_called_once_with("66.249.66.1")
    assert seen["result"].rdns_match is True
    assert seen["result"].is_crawler is True


def test_wsgi_middleware_verify_ip_without_ip_skips_lookup():
    middleware = WSGICrawlerMiddleware(
        lambda environ, start_response: [b"ok"],
        verify_ip=True,
    )

    with patch("is_crawler.contrib.verify_crawler_ip") as verify:
        middleware({"HTTP_USER_AGENT": _BOT}, lambda status, headers: None)

    verify.assert_not_called()


def test_wsgi_middleware_verify_ip_skips_blank_remote_addr():
    middleware = WSGICrawlerMiddleware(
        lambda environ, start_response: [b"ok"],
        verify_ip=True,
    )

    with patch("is_crawler.contrib.verify_crawler_ip") as verify:
        middleware(
            {
                "HTTP_USER_AGENT": _BOT,
                "REMOTE_ADDR": "   ",
            },
            lambda status, headers: None,
        )

    verify.assert_not_called()


def test_wsgi_middleware_uses_x_real_ip_for_verification():
    middleware = WSGICrawlerMiddleware(
        lambda environ, start_response: [b"ok"],
        verify_ip=True,
        trust_forwarded=True,
    )

    with patch("is_crawler.contrib.verify_crawler_ip", return_value=True) as verify:
        middleware(
            {
                "HTTP_USER_AGENT": _BOT,
                "HTTP_X_REAL_IP": "66.249.66.1",
                "REMOTE_ADDR": "10.0.0.1",
            },
            lambda status, headers: None,
        )

    verify.assert_called_once_with(_BOT, "66.249.66.1")


def test_wsgi_middleware_blocks_matching_tags():
    middleware = WSGICrawlerMiddleware(
        lambda environ, start_response: [b"ok"],
        block=True,
        block_tags="search-engine",
        body=b"blocked",
    )
    calls = []

    def start_response(status, headers):
        calls.append((status, headers))

    body = middleware({"HTTP_USER_AGENT": _BOT}, start_response)

    assert body == [b"blocked"]
    assert calls == [("403 Forbidden", [("Content-Type", "text/plain; charset=utf-8")])]


def test_wsgi_middleware_does_not_block_tag_miss():
    middleware = WSGICrawlerMiddleware(
        lambda environ, start_response: [b"ok"],
        block=True,
        block_tags="ai-crawler",
    )
    body = middleware({"HTTP_USER_AGENT": _BOT}, lambda status, headers: None)
    assert body == [b"ok"]


def test_wsgi_middleware_custom_key_and_browser():
    seen = {}

    def app(environ, start_response):
        seen["result"] = environ["crawler_ctx"]
        start_response("200 OK", [])
        return [b"ok"]

    middleware = WSGICrawlerMiddleware(app, environ_key="crawler_ctx")
    middleware({"HTTP_USER_AGENT": _BROWSER}, lambda status, headers: None)
    assert seen["result"].is_crawler is False
    assert seen["result"].name is None


def test_asgi_middleware_passes_through_and_sets_state():
    sent = []
    seen = {}

    async def app(scope, receive, send):
        seen["scope"] = scope
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = ASGICrawlerMiddleware(app, verify_ip=True)

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        sent.append(message)

    with patch("is_crawler.contrib.verify_crawler_ip", return_value=True) as verify:
        asyncio.run(
            middleware(
                {
                    "type": "http",
                    "headers": [(b"user-agent", _BOT.encode())],
                    "client": ("66.249.66.1", 1234),
                },
                receive,
                send,
            )
        )

    verify.assert_called_once_with(_BOT, "66.249.66.1")
    assert sent[-1] == {"type": "http.response.body", "body": b"ok"}
    assert seen["scope"]["is_crawler"].verified is True
    assert seen["scope"]["state"]["crawler"].name == "Googlebot"


def test_asgi_middleware_reads_mixed_case_headers():
    sent = []
    seen = {}

    async def app(scope, receive, send):
        seen["scope"] = scope
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = ASGICrawlerMiddleware(app, trust_forwarded=True, verify_ip=True)

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        sent.append(message)

    with patch("is_crawler.contrib.verify_crawler_ip", return_value=True) as verify:
        asyncio.run(
            middleware(
                {
                    "type": "http",
                    "headers": [
                        (b"User-Agent", _BOT.encode()),
                        (b"X-Forwarded-For", b"66.249.66.1, 10.0.0.1"),
                    ],
                    "client": ("10.0.0.1", 1234),
                },
                receive,
                send,
            )
        )

    verify.assert_called_once_with(_BOT, "66.249.66.1")
    assert sent[-1] == {"type": "http.response.body", "body": b"ok"}
    assert seen["scope"]["is_crawler"].ip == "66.249.66.1"


def test_asgi_middleware_uses_x_real_ip():
    sent = []
    seen = {}

    async def app(scope, receive, send):
        seen["scope"] = scope
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = ASGICrawlerMiddleware(app, trust_forwarded=True, verify_ip=True)

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        sent.append(message)

    with patch("is_crawler.contrib.verify_crawler_ip", return_value=True) as verify:
        asyncio.run(
            middleware(
                {
                    "type": "http",
                    "headers": [
                        (b"user-agent", _BOT.encode()),
                        (b"x-real-ip", b"66.249.66.1"),
                    ],
                    "client": ("10.0.0.1", 1234),
                },
                receive,
                send,
            )
        )

    verify.assert_called_once_with(_BOT, "66.249.66.1")
    assert sent[-1] == {"type": "http.response.body", "body": b"ok"}
    assert seen["scope"]["is_crawler"].ip == "66.249.66.1"


def test_asgi_middleware_block_and_custom_keys():
    sent = []

    async def app(scope, receive, send):
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = ASGICrawlerMiddleware(
        app,
        block=True,
        scope_key="crawler_ctx",
        state_key="bot",
        status_code=429,
        body=b"slow down",
    )

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "headers": [(b"user-agent", _BOT.encode())],
        "state": {},
    }
    asyncio.run(middleware(scope, receive, send))

    assert sent == [
        {
            "type": "http.response.start",
            "status": 429,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        },
        {
            "type": "http.response.body",
            "body": b"slow down",
        },
    ]
    assert scope["crawler_ctx"].is_crawler is True
    assert scope["state"]["bot"].name == "Googlebot"


def test_asgi_middleware_non_dict_state_and_non_http():
    seen = {"called": 0}

    async def app(scope, receive, send):
        seen["called"] += 1

    middleware = ASGICrawlerMiddleware(app)

    async def receive():
        return {"type": "lifespan.startup"}

    async def send(message):
        raise AssertionError(message)

    asyncio.run(middleware({"type": "lifespan"}, receive, send))
    asyncio.run(
        middleware(
            {
                "type": "http",
                "headers": [(b"user-agent", _BROWSER.encode())],
                "state": [],
            },
            lambda: receive(),
            lambda message: asyncio.sleep(0),
        )
    )

    assert seen["called"] == 2
