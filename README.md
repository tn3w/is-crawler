<div align="center">

# is-crawler

Fast, regex-free crawler detection from user agents. Zero deps, ReDoS-safe heuristics, ~100× faster than alternatives. Includes FCrDNS IP verification for 100+ known crawlers.

[![PyPI](https://img.shields.io/pypi/v/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![Python](https://img.shields.io/pypi/pyversions/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![License](https://img.shields.io/github/license/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/stargazers)
[![Downloads](https://img.shields.io/pypi/dm/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![Buy Me a Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow?style=flat-square)](https://www.buymeacoffee.com/tn3w)

</div>

## Why regex-free?

Regex is a frequent source of ReDoS vulnerabilities, one un-anchored `.*` or nested quantifier against a hostile UA can spike CPU to seconds. Crawler detection runs on every request, so a catastrophic pattern is a denial-of-service primitive. `is-crawler` implements all heuristics with `str.find` + char scans. No regex engine, no backtracking, no ReDoS surface. `crawler_info` uses `re` only to match against curated DB patterns ([monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents)) which are simple literals (e.g. `Googlebot\/`, `bingbot`, `AdsBot-Google([^-]|$)`, `[wW]get`), no nested quantifiers, no catastrophic backtracking paths.

## Install

```bash
pip install is-crawler
```

## Usage

```python
from is_crawler import (
    is_crawler, crawler_signals, crawler_info, crawler_has_tag,
    crawler_name, crawler_version, crawler_url, CrawlerInfo,
)
from is_crawler.ip import verify_crawler_ip

ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
ip = "66.249.66.1"

is_crawler(ua)                              # True
crawler_signals(ua)                         # ['bot_signal', 'no_browser_signature', 'url_in_ua']
crawler_name(ua)                            # 'Googlebot'
crawler_version(ua)                         # '2.1'
crawler_url(ua)                             # 'http://www.google.com/bot.html'
verify_crawler_ip(ua, ip)                   # True - FCrDNS validation

info = crawler_info(ua)                     # CrawlerInfo(...)
if info is not None:
    info.url                                # 'http://www.google.com/bot.html'
    info.description                        # "Google's main web crawling bot..."
    info.tags                               # ('search-engine',)

crawler_has_tag(ua, "search-engine")        # True
crawler_has_tag(ua, ["ai-crawler", "seo"])  # False
```

## API

### `is_crawler(ua: str) -> bool`

Heuristic detection. Returns `True` if the UA is a crawler. No DB lookup, no regex.

Three short-circuit rules:

1. **Positive signal**: bot keywords (`bot`, `crawl`, `spider`, `scrape`, `headless`, `slurp`, `archiv`, `preview`, ...), known tools (`playwright`, `selenium`, `wget`, `lighthouse`, `sqlmap`, `nikto`, `nmap`, `httrack`, `pingdom`, `google-safety`, ...), or a URL/email embedded in the UA.
2. **No browser signature**: missing `Mozilla/`, `WebKit`, `Gecko`, `Trident`, `Presto`, `KHTML`, `Links`, `Lynx`, `Opera`, or an OS token like `(Windows`, `(Linux`, `(X11`, `(Macintosh`.
3. **Bare `(compatible; ...)`**: classic bot block without OS/browser tokens inside.

### `crawler_signals(ua: str) -> list[str]`

Which individual rules fired. Subset of: `bot_signal`, `no_browser_signature`, `bare_compatible`, `known_tool`, `url_in_ua`. Useful for diagnostics and logging. `is_crawler` does not call this.

### `crawler_name(ua: str) -> str | None`

Product name extracted from the UA.

- `Googlebot/2.1 ...` → `'Googlebot'`
- `Mozilla/5.0 (compatible; bingbot/2.0; ...)` → `'bingbot'`
- `Mozilla/5.0 ... Speedy Spider (...)` → `'Speedy Spider'`
- Chrome/Firefox/Safari → `None`

### `crawler_version(ua: str) -> str | None`

Version token extracted from the UA. Returns `None` if no non-browser version is detectable.

- `curl/7.64.1` → `'7.64.1'`
- `Mozilla/5.0 (compatible; Miniflux/2.0.10; ...)` → `'2.0.10'`
- `Googlebot/2.1 ...` → `'2.1'`

### `crawler_url(ua: str) -> str | None`

URL embedded in the UA (after `+`, `;`, or `-`).

- `Googlebot/2.1 (+http://www.google.com/bot.html)` → `'http://www.google.com/bot.html'`
- UA with no embedded URL → `None`

### `crawler_info(ua: str) -> CrawlerInfo | None`

DB lookup against 1200 known crawler patterns. Returns `None` for browsers (short-circuits via `is_crawler`).

```python
class CrawlerInfo(NamedTuple):
    url: str                # crawler's info/docs URL (may be '')
    description: str        # human-readable description
    tags: tuple[str, ...]   # classification tags, e.g. ('search-engine',)
```

### `crawler_has_tag(ua: str, tags: str | Iterable[str]) -> bool`

`True` if the crawler has any of the given tags. `tags` accepts a single string or a list.

Available tags: `search-engine`, `ai-crawler`, `seo`, `social-preview`, `advertising`, `archiver`, `feed-reader`, `monitoring`, `scanner`, `academic`, `http-library`, `browser-automation`.

### Category shortcuts

One-tag wrappers over `crawler_has_tag`:

```python
is_search_engine(ua)       # 'search-engine'
is_ai_crawler(ua)          # 'ai-crawler'
is_seo(ua)                 # 'seo'
is_social_preview(ua)      # 'social-preview'
is_advertising(ua)         # 'advertising'
is_archiver(ua)            # 'archiver'
is_feed_reader(ua)         # 'feed-reader'
is_monitoring(ua)          # 'monitoring'
is_scanner(ua)             # 'scanner'
is_academic(ua)            # 'academic'
is_http_library(ua)        # 'http-library'
is_browser_automation(ua)  # 'browser-automation'
```

### `is_good_crawler(ua)` / `is_bad_crawler(ua)`

Opinionated groupings for quick allow/deny gates.

- **Good** (indexing, previews, archives, feeds, research): `search-engine`, `social-preview`, `feed-reader`, `archiver`, `academic`.
- **Bad** (scraping, scanning, unattributed traffic): `ai-crawler`, `scanner`, `http-library`, `browser-automation`, `seo`.

`advertising` and `monitoring` are intentionally neither: policy-dependent.

### Middleware

```python
from is_crawler.contrib import WSGICrawlerMiddleware

app = WSGICrawlerMiddleware(app)

# Flask
request.environ["is_crawler"].is_crawler

# Django
request.META["is_crawler"].name
```

```python
from is_crawler.contrib import ASGICrawlerMiddleware

app = ASGICrawlerMiddleware(app, block=True, block_tags="ai-crawler")

# FastAPI / Starlette
request.scope["is_crawler"].is_crawler
request.state.crawler.verified
```

Both middlewares are zero-dep. They attach `CrawlerMiddlewareResult` with
`user_agent`, `ip`, `is_crawler`, `name`, and `verified`.

- `WSGICrawlerMiddleware`: Flask, Django, any WSGI app
- `ASGICrawlerMiddleware`: FastAPI, Starlette, any ASGI app

Optional flags: `block=True`, `block_tags=...`, `verify_ip=True`,
`trust_forwarded=True`.

With `trust_forwarded=True`, middleware uses the first IP from
`X-Forwarded-For`, then `X-Real-IP`, before the direct client address.

### `robots.txt` helpers

Generate directives from DB tags. Names extracted from DB patterns (slash/URL-only entries skipped).

```python
from is_crawler import build_robots_txt, robots_agents_for_tags, iter_crawlers

robots_agents_for_tags("ai-crawler")
# ['AI2Bot', 'Applebot-Extended', 'Bytespider', 'CCBot', 'ChatGPT-User', 'Claude-Web', 'GPTBot', ...]

print(build_robots_txt(disallow=["ai-crawler", "scanner"]))
# User-agent: GPTBot
# Disallow: /
#
# User-agent: Nikto
# Disallow: /
# ...

build_robots_txt(allow="search-engine", path="/public")
# User-agent: Googlebot
# Allow: /public
# ...

for info, name in iter_crawlers():      # (CrawlerInfo, robots-name) per DB entry
    ...
```

### IP verification (`is_crawler.ip`)

Forward-confirmed reverse DNS (FCrDNS). rDNS → suffix check → forward lookup → IP match. Catches UA spoofing. `socket` only, no deps.

```python
from is_crawler.ip import verify_crawler_ip, forward_confirmed_rdns, reverse_dns

verify_crawler_ip("Googlebot/2.1 (+http://www.google.com/bot.html)", "66.249.66.1")
# True → rDNS ends in .googlebot.com AND forward lookup returns same IP

verify_crawler_ip("Googlebot/2.1", "8.8.8.8")               # False (spoof)
reverse_dns("8.8.8.8")                                       # 'dns.google'
forward_confirmed_rdns("66.249.66.1", (".googlebot.com",))   # hostname or None
```

Built-in suffixes: Googlebot, Bingbot, Applebot, DuckDuckBot, YandexBot, Baiduspider, FacebookBot, and 80+ more. Crawler name taken from `crawler_name(ua)`.

### CLI

```bash
python -m is_crawler "Googlebot/2.1 (+http://www.google.com/bot.html)"
tail -f access.log | awk -F'"' '{print $6}' | python -m is_crawler
```

One JSON object per UA (arg or stdin line) with `is_crawler`, `name`, `version`, `url`, `signals`, `info`.

### Caching

Every public function has a 32k-entry LRU cache. Repeat UAs hit in ~40 ns.

## Benchmarks

Python 3.14, Linux x86_64. Corpus: 1,231 crawler UAs, 15,812 browser UAs. `cua` = [`crawler-user-agents`](https://pypi.org/project/crawler-user-agents/) v1.44.

### Hot-path (warm cache)

| Function             | is_crawler | cua      | speedup   |
| -------------------- | ---------- | -------- | --------- |
| `is_crawler` (mixed) | 0.05 µs    | 158.9 µs | **3000×** |
| `crawler_info`       | 0.60 µs    | 732.0 µs | **1220×** |
| `crawler_signals`    | 1.13 µs    | -        | -         |
| `crawler_name`       | 0.33 µs    | -        | -         |
| `crawler_version`    | 0.32 µs    | -        | -         |
| `crawler_url`        | 0.09 µs    | -        | -         |
| `crawler_has_tag`    | 0.10 µs    | -        | -         |

### Cold-cache (per-call, no LRU hits)

| Function          | Test Case | is_crawler | cua       | speedup  |
| ----------------- | --------- | ---------- | --------- | -------- |
| `is_crawler`      | crawlers  | 1.94 µs    | 64.35 µs  | **33×**  |
| `is_crawler`      | browsers  | 1.85 µs    | 183.76 µs | **99×**  |
| `is_crawler`      | mixed     | 1.85 µs    | 176.94 µs | **96×**  |
| `crawler_info`    | -         | 2.07 µs    | 733.4 µs  | **354×** |
| `crawler_name`    | -         | 1.36 µs    | -         | -        |
| `crawler_version` | -         | 1.37 µs    | -         | -        |
| `crawler_url`     | -         | 0.29 µs    | -         | -        |

### Cold-start

| Module              | Cold-start |
| ------------------- | ---------- |
| `is_crawler`        | 1.29 ms    |
| `crawleruseragents` | 0.80 ms    |

DB patterns compile lazily per 48-entry chunk on first match.

## Formatting

```bash
pip install black isort
isort . && black .
npx prtfm
```

## Contributing

Bug reports, feature requests, and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Security

Report vulnerabilities via [GitHub private security advisory](https://github.com/tn3w/is-crawler/security), **do not open a public issue**. See [SECURITY.md](SECURITY.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[Apache-2.0](LICENSE)
