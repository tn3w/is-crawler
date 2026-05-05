<div align="center">

# is-crawler

Crawler detection from User-Agent strings in 40 ns. Zero deps, no regex, ReDoS-safe.

[![PyPI](https://img.shields.io/pypi/v/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![Python](https://img.shields.io/pypi/pyversions/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![License](https://img.shields.io/github/license/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/stargazers)
[![Downloads](https://static.pepy.tech/personalized-badge/is-crawler?period=month&units=international_system&left_color=grey&right_color=blue&left_text=downloads/month&style=flat-square)](https://pepy.tech/project/is-crawler)

[![Issues](https://img.shields.io/github/issues/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/tn3w/is-crawler/blob/master/CONTRIBUTING.md)
[![Buy Me a Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow?style=flat-square)](https://www.buymeacoffee.com/tn3w)

</div>

```bash
pip install is-crawler
```

```python
from is_crawler import is_crawler

is_crawler("Googlebot/2.1 (+http://www.google.com/bot.html)")  # True
is_crawler("Mozilla/5.0 (X11; Linux x86_64) Firefox/120.0")    # False
```

One call, runs on every request without blinking.

```
\(°o°)/   caught one!
 /| |\
```

## Why

Crawler detection sits on the request hot path. Most libraries reach for big regex tables, which means slow first hits, ReDoS exposure on hostile UAs, and millisecond-scale latency you pay forever.

`is_crawler` runs `str.find` and small char scans against curated keywords. No backtracking, no DB load, no network. The optional `crawler_info` adds DB lookups when you want classification. Everything else (FCrDNS, IP ranges, robots.txt, middleware) is opt-in.

```
is-crawler  ▏                                                  0.04 µs
cua         ████████████████████████████████████████████████  64.00 µs
```

|                   | is-crawler | crawler-user-agents | ua-parser |
| ----------------- | ---------- | ------------------- | --------- |
| Hot-path regex    | no         | yes                 | yes       |
| ReDoS-safe        | yes        | no                  | no        |
| FCrDNS verify     | yes        | no                  | no        |
| IP range lookup   | yes        | no                  | no        |
| WSGI/ASGI MW      | yes        | no                  | no        |
| Warm `is_crawler` | 0.04 µs    | 66 µs               | n/a       |

## In the wild

What the API returns on real UAs you will actually see:

| User agent                                                                                                        | `is_crawler` | `crawler_name`        | `crawler_version` | `crawler_url`                                      | `crawler_signals`                                     | `crawler_info.tags`       |
| ----------------------------------------------------------------------------------------------------------------- | ------------ | --------------------- | ----------------- | -------------------------------------------------- | ----------------------------------------------------- | ------------------------- |
| `Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)`                                                | True         | `GPTBot`              | `'1.2'`           | `'https://openai.com/gptbot'`                      | `['bot_signal', 'bare_compatible', 'url_in_ua']`      | `('ai-crawler',)`         |
| `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36`   | True         | `HeadlessChrome`      | `'120.0.0.0'`     | `None`                                             | `['bot_signal']`                                      | `('browser-automation',)` |
| `curl/8.4.0`                                                                                                      | True         | `curl`                | `'8.4.0'`         | `None`                                             | `['no_browser_signature']`                            | `('http-library',)`       |
| `python-requests/2.31.0`                                                                                          | True         | `python-requests`     | `'2.31.0'`        | `None`                                             | `['no_browser_signature']`                            | `('http-library',)`       |
| `Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)`                                              | True         | `AhrefsBot`           | `'7.0'`           | `'http://ahrefs.com/robot/'`                       | `['bot_signal', 'bare_compatible', 'url_in_ua']`      | `('seo',)`                |
| `facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)`                                       | True         | `facebookexternalhit` | `'1.1'`           | `'http://www.facebook.com/externalhit_uatext.php'` | `['bot_signal', 'no_browser_signature', 'url_in_ua']` | `('social-preview',)`     |
| `Mozilla/5.0 (compatible; Nikto/2.5.0)`                                                                           | True         | `Nikto`               | `'2.5.0'`         | `None`                                             | `['bare_compatible', 'known_tool']`                   | `('scanner',)`            |
| `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36` | False        | `None`                | `None`            | `None`                                             | `[]`                                                  | `None`                    |

## Detection

```python
from is_crawler import (
    is_crawler, crawler_signals, crawler_info, crawler_has_tag,
    crawler_name, crawler_version, crawler_url, crawler_contact,
)

ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"

is_crawler(ua)         # True
crawler_name(ua)       # 'Googlebot'
crawler_version(ua)    # '2.1'
crawler_url(ua)        # 'http://www.google.com/bot.html'
crawler_signals(ua)    # ['bot_signal', 'no_browser_signature', 'url_in_ua']

ua2 = "MyBot/1.0 (contact: bot@example.com)"
crawler_contact(ua2)   # 'bot@example.com'
crawler_contact(ua)    # None
```

`is_crawler` short-circuits on three rules: positive bot signal (keywords like `bot`/`crawl`/`spider`, known tools, embedded URL/email), missing browser signature (no `Mozilla/`, `WebKit`, OS token, etc.), or a bare `(compatible; ...)` block.

`crawler_signals` exposes which rules fired, for logging and diagnostics.

## Classification

`crawler_info` matches against 1200 curated patterns from [tn3w/Crawlerdex](https://github.com/tn3w/Crawlerdex) plus extras. Patterns compile lazily in 48-entry chunks.

```python
info = crawler_info(ua)
info.url            # 'http://www.google.com/bot.html'
info.description    # "Google's main web crawling bot..."
info.tags           # ('search-engine',)

crawler_has_tag(ua, "search-engine")        # True
crawler_has_tag(ua, ["ai-crawler", "seo"])  # False
```

Tags: `search-engine`, `ai-crawler`, `seo`, `social-preview`, `advertising`, `archiver`, `feed-reader`, `monitoring`, `scanner`, `academic`, `http-library`, `browser-automation`.

One-tag wrappers exist for each: `is_search_engine`, `is_ai_crawler`, `is_seo`, `is_social_preview`, `is_advertising`, `is_archiver`, `is_feed_reader`, `is_monitoring`, `is_scanner`, `is_academic`, `is_http_library`, `is_browser_automation`.

Quick gates:

```python
is_good_crawler(ua)   # search-engine, social-preview, feed-reader, archiver, academic
is_bad_crawler(ua)    # ai-crawler, scanner, http-library, browser-automation, seo
```

`advertising` and `monitoring` are policy-dependent and belong to neither group.

## IP verification

Two strategies, use either or both. `socket` only, no deps.

```python
from is_crawler.ip import (
    verify_crawler_ip, reverse_dns, forward_confirmed_rdns,
    ip_in_range, known_crawler_ip, known_crawler_rdns,
)

verify_crawler_ip("Googlebot/2.1", "66.249.66.1")  # True (FCrDNS, UA-name matched)
verify_crawler_ip("Googlebot/2.1", "8.8.8.8")      # False (spoof)

ip_in_range("66.249.66.1")        # True (CIDR lookup, offline)
known_crawler_rdns("66.249.66.1") # True (rDNS suffix matches any known crawler)

reverse_dns("8.8.8.8")                                      # 'dns.google'
forward_confirmed_rdns("66.249.66.1", (".googlebot.com",))  # hostname or None
```

`verify_crawler_ip` does the full FCrDNS dance: rDNS lookup, suffix check against the UA's vendor, forward lookup, IP match. Catches UA spoofing.

`ip_in_range` runs a bisect over collapsed CIDRs from 39 official sources (Google, Bing, OpenAI, Anthropic, Cloudflare, AWS, ...). Cheap and offline.

## Middleware

Drop-in for any WSGI or ASGI app. Zero deps.

```python
from is_crawler.contrib import WSGICrawlerMiddleware, ASGICrawlerMiddleware

app = WSGICrawlerMiddleware(app)                                  # Flask, Django
app = ASGICrawlerMiddleware(app, block=True, block_tags="ai-crawler")  # FastAPI, Starlette

# Flask:    request.environ["is_crawler"].is_crawler
# Django:   request.META["is_crawler"].name
# FastAPI:  request.scope["is_crawler"].verified
```

Both attach a `CrawlerMiddlewareResult` with `user_agent`, `ip`, `is_crawler`, `name`, `verified`, `in_ip_range`, `rdns_match`.

Flags: `block`, `block_tags`, `verify_ip`, `check_ip_range`, `check_rdns`,
`trust_forwarded`. A positive `in_ip_range` or `rdns_match` forces
`is_crawler=True`, which catches UA-less crawlers. With
`trust_forwarded=True`, IP comes from `Forwarded`, then `X-Forwarded-For`,
then `X-Real-IP`, then the direct client.

## Recipes

Block AI scrapers, let search engines through (FastAPI):

```python
from fastapi import FastAPI
from is_crawler.contrib import ASGICrawlerMiddleware

app = FastAPI()
app = ASGICrawlerMiddleware(app, block=True, block_tags="ai-crawler", trust_forwarded=True)
```

Serve a live `robots.txt` from the DB (Flask):

```python
from flask import Response
from is_crawler import build_robots_txt

@app.route("/robots.txt")
def robots():
    return Response(build_robots_txt(disallow=["ai-crawler", "scanner"]), mimetype="text/plain")
```

Verify Googlebot is real before trusting it:

```python
from is_crawler import is_crawler
from is_crawler.ip import verify_crawler_ip

if is_crawler(ua) and not verify_crawler_ip(ua, ip):
    abort(403)  # spoofed
```

Crawler share of an access log:

```bash
awk -F'"' '{print $6}' access.log | python -m is_crawler | \
  jq -r '.is_crawler' | sort | uniq -c
```

## Snippets

Standalone copy-paste gists in [snippets/](snippets/). No install. Single-file, stdlib only: drop into any project. Includes minimal/full `is_crawler`, `crawler_name`, `crawler_version`, and a compact `parse`.

## robots.txt / ai.txt

Generate directives from tags. Names are extracted from DB patterns, slash/URL-only entries skipped.

```python
from is_crawler import build_robots_txt, build_ai_txt, robots_agents_for_tags

print(build_robots_txt(disallow=["ai-crawler", "scanner"]))
# User-agent: GPTBot
# Disallow: /
# ...

print(build_ai_txt())          # disallows all ai-crawler agents by default
# User-Agent: GPTBot
# Disallow: /
# ...

robots_agents_for_tags("ai-crawler")
# ['AI2Bot', 'Applebot-Extended', 'Bytespider', 'CCBot', 'ChatGPT-User', ...]
```

`build_robots_txt` also accepts a `rules` list of `(path, tags)` pairs for per-path control:

```python
build_robots_txt(rules=[("/api", "scanner"), ("/private", "ai-crawler")])
```

`assert_crawler(ua)`: like `crawler_info` but raises `ValueError` for unknown UAs.

## CLI

```bash
python -m is_crawler "Googlebot/2.1 (+http://www.google.com/bot.html)"
tail -f access.log | awk -F'"' '{print $6}' | python -m is_crawler
python -m is_crawler --help     # usage
python -m is_crawler --version  # show version
```

One JSON object per UA with `is_crawler`, `name`, `version`, `url`, `contact`, `signals`, `info`.

## UA Parser

`parse(ua)` returns a `UserAgent` with all common fields. Zero deps, no regex, 4096-entry LRU cache.

```python
from is_crawler.parser import parse, parse_or_none

ua = parse("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

ua.browser          # 'Chrome'
ua.browser_version  # '134.0.0.0'
ua.browser_major    # '134'
ua.os               # 'Windows'
ua.os_version       # '10'
ua.engine           # 'Blink'
ua.engine_version   # '537.36'
ua.device           # 'Desktop'
ua.device_brand     # None
ua.device_model     # None
ua.cpu              # 'x86_64'
ua.is_mobile        # False
ua.is_tablet        # False
ua.is_crawler       # False
ua.is_webview       # False
ua.is_headless      # False
ua.channel          # None | 'beta' | 'dev' | 'canary' | 'nightly'
ua.app              # None | 'Facebook' | 'Instagram' | 'TikTok' ...
ua.app_version      # in-app browser version
ua.languages        # []
ua.rendering        # 'KHTML, like Gecko'
ua.product_token    # 'Mozilla/5.0'
ua.comment          # '(Windows NT 10.0; Win64; x64)'
ua.raw              # original string

ua.to_dict()        # all fields as dict
```

`parse_or_none(value)` normalises bytes/None/non-str, returns `None` for empty input.

## Benchmarks

Python 3.14, Linux x86_64. `cua` = [`crawler-user-agents`](https://pypi.org/project/crawler-user-agents/) v1.47.

**Apache Logs** 42,512 UA entries (8,942 crawlers, 33,570 browsers, 21% ratio):

| Scenario   | `is_crawler` | `crawler_info` | `cua.is_crawler` | `cua.crawler_info` |
| ---------- | ------------ | -------------- | ---------------- | ------------------ |
| Warm cache | 0.037 µs     | 0.116 µs       | 66.234 µs        | 1585.007 µs        |
| Cold cache | 0.112 µs     | 1.008 µs       | -                | -                  |

~1790× faster on the hot path, ~13660× faster for `crawler_info` warm. Full classify of 42,512 Apache log UAs runs in 1.80 ms.

**Fixture UAs** 2,149 crawlers + 19,910 browsers:

| Scenario   | `is_crawler` (mixed) | `crawler_info` | `cua.is_crawler` (mixed) | `cua.crawler_info` |
| ---------- | -------------------- | -------------- | ------------------------ | ------------------ |
| Warm cache | 0.05 µs              | 1.24 µs        | 80.95 µs                 | 563.53 µs          |
| Cold cache | 1.43 µs              | 4.57 µs        | 82.00 µs                 | 581.76 µs          |

**UA parser** 19,910 real browser UAs vs [`ua-parser`](https://pypi.org/project/ua-parser/) (~24× faster):

| Scenario   | `parser.parse` | `ua-parser` |
| ---------- | -------------- | ----------- |
| Warm cache | 18.48 µs       | 443.20 µs   |
| Cold cache | 18.17 µs       | 443.05 µs   |

**IP verification** warm cache:

| Function                 | Time    |
| ------------------------ | ------- |
| `ip_in_range`            | 0.06 µs |
| `reverse_dns`            | 0.36 µs |
| `known_crawler_rdns`     | 2.14 µs |
| `verify_crawler_ip`      | 2.96 µs |
| `forward_confirmed_rdns` | 3.15 µs |

Every public function has a 32k-entry LRU cache. First-call rDNS latency is network-bound.

## Implementation

`is_crawler` uses `str.find` and char scans, never regex, so hostile UAs cannot trigger backtracking. `crawler_info` does use `re`, but only against curated upstream patterns that are simple by construction.

Data files are built by scripts in `tools/`:

```bash
python3 tools/build_user_agents.py   # crawler-user-agents.json from tn3w/Crawlerdex
python3 tools/build_ip_ranges.py     # crawler-ip-ranges.json from 39 official sources
```

Source definitions for IP ranges live in `tools/crawler-ip-ranges.json` and can be extended without touching the build script.

## Development

```bash
pip install -e ".[dev]"
ruff format . && ruff check --fix .
npx --yes prettier --write --single-quote --print-width=100 --trailing-comma=es5 --end-of-line=lf "**/*.{md,yml,yaml,html,css,js,ts}" "tools/*.json"
```

See [CONTRIBUTING.md](https://github.com/tn3w/is-crawler/blob/master/CONTRIBUTING.md). Report vulnerabilities via [GitHub private security advisory](https://github.com/tn3w/is-crawler/security), not public issues. See [SECURITY.md](https://github.com/tn3w/is-crawler/blob/master/SECURITY.md) and [CODE_OF_CONDUCT.md](https://github.com/tn3w/is-crawler/blob/master/CODE_OF_CONDUCT.md).

## License

[Apache-2.0](https://github.com/tn3w/is-crawler/blob/master/LICENSE)
