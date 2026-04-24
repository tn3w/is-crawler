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
from is_crawler.ip import (
    verify_crawler_ip,
    reverse_dns,
    forward_confirmed_rdns,
    ip_in_range,
    known_crawler_ip,
    known_crawler_rdns,
)

ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
ip = "66.249.66.1"

is_crawler(ua)                                  # True
crawler_signals(ua)                             # ['bot_signal', 'no_browser_signature', 'url_in_ua']
crawler_name(ua)                                # 'Googlebot'
crawler_version(ua)                             # '2.1'
crawler_url(ua)                                 # 'http://www.google.com/bot.html'
verify_crawler_ip(ua, ip)                       # True - FCrDNS validation
reverse_dns(ip)                                 # 'crawl-66-249-66-1.googlebot.com'
forward_confirmed_rdns(ip, (".googlebot.com",)) # hostname or None
ip_in_range(ip)                                 # True - in known crawler CIDRs
known_crawler_ip(ip)                            # alias for ip_in_range
known_crawler_rdns(ip)                          # True - known crawler via FCrDNS/rDNS

info = crawler_info(ua)                         # CrawlerInfo(...)
if info is not None:
    info.url                                    # 'http://www.google.com/bot.html'
    info.description                            # "Google's main web crawling bot..."
    info.tags                                   # ('search-engine',)

crawler_has_tag(ua, "search-engine")            # True
crawler_has_tag(ua, ["ai-crawler", "seo"])      # False
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

Two complementary strategies: use either or both.

#### FCrDNS (forward-confirmed reverse DNS)

rDNS → suffix check → forward lookup → IP match. Catches UA spoofing. `socket` only, no deps.

```python
from is_crawler.ip import verify_crawler_ip, forward_confirmed_rdns, reverse_dns

verify_crawler_ip("Googlebot/2.1 (+http://www.google.com/bot.html)", "66.249.66.1")
# True → rDNS ends in .googlebot.com AND forward lookup returns same IP

verify_crawler_ip("Googlebot/2.1", "8.8.8.8")               # False (spoof)
reverse_dns("8.8.8.8")                                       # 'dns.google'
forward_confirmed_rdns("66.249.66.1", (".googlebot.com",))   # hostname or None
```

Built-in suffixes: Googlebot, Bingbot, Applebot, DuckDuckBot, YandexBot, Baiduspider, FacebookBot, and 80+ more. Crawler name taken from `crawler_name(ua)`.

#### IP range lookup

Check whether an IP belongs to any known crawler's published CIDR range. Requires building the range database first (see **Tools** below).

```python
from is_crawler.ip import ip_in_range, known_crawler_ip, known_crawler_rdns

ip_in_range("66.249.66.1")    # True : in Googlebot ranges
ip_in_range("8.8.8.8")        # False: not a known crawler range
known_crawler_ip("66.249.66.1")  # alias for ip_in_range
known_crawler_rdns("66.249.66.1")  # True: reverse DNS matches a known crawler domain
```

Results are LRU-cached. The file is optional: if absent, `ip_in_range` returns `False` rather than raising.

### Tools

Scripts in `tools/` build the data files shipped inside the package.

#### `build_user_agents.py`

Compiles `is_crawler/crawler-user-agents.json` from the upstream [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents) source plus local extras.

```bash
python3 tools/build_user_agents.py
python3 tools/build_user_agents.py --input crawler-user-agents.json --output is_crawler/crawler-user-agents.json
```

#### `build_ip_ranges.py`

Fetches live IP range data from 39 official sources (Google, Bing, DuckDuckGo, Apple, OpenAI, Anthropic, Perplexity, Common Crawl, Cloudflare, Fastly, AWS, Azure, Oracle Cloud, GitHub, Telegram, Ahrefs, Yandex, Facebook, Kagi, Amazon, UptimeRobot, Pingdom, Stripe, and more) and writes a flat `is_crawler/crawler-ip-ranges.json` mapping each source name to its CIDR list.

```bash
python3 tools/build_ip_ranges.py
python3 tools/build_ip_ranges.py --timeout 30 --skip-errors
```

Source definitions live in `tools/crawler-ip-ranges.json` (name → `{url, pattern}`) and can be extended independently of the build script.

### CLI

```bash
python -m is_crawler "Googlebot/2.1 (+http://www.google.com/bot.html)"
tail -f access.log | awk -F'"' '{print $6}' | python -m is_crawler
```

One JSON object per UA (arg or stdin line) with `is_crawler`, `name`, `version`, `url`, `signals`, `info`.

### Caching

Every public function has a 32k-entry LRU cache. Repeat UAs hit in ~40 ns.

## Benchmarks

Python 3.14, Linux x86_64. `cua` = [`crawler-user-agents`](https://pypi.org/project/crawler-user-agents/) v1.44.

### Synthetic corpus

Corpus: 1,231 crawler UAs + 15,812 browser UAs.

| Scenario   | `is_crawler` | `crawler_info` | `cua.is_crawler` | `cua.crawler_info` |
| ---------- | ------------ | -------------- | ---------------- | ------------------ |
| Warm cache | 0.05 µs      | 0.60 µs        | 158.9 µs         | 732.0 µs           |
| Cold cache | 1.85 µs      | 2.07 µs        | 176.94 µs        | 733.4 µs           |

That is roughly `3000×` faster for hot `is_crawler`, `96×` faster for cold `is_crawler`, and `354×` faster for cold `crawler_info`.

### Real Apache logs

Corpus: `42,512` UA entries from two Apache access logs (`8,942` crawlers, `33,570` browsers, `21.0%` crawler ratio).

| Scenario   | `is_crawler` (all) | `crawler_info` (all) | `cua.is_crawler` (all) | `cua.crawler_info` (all) |
| ---------- | ------------------ | -------------------- | ---------------------- | ------------------------ |
| Warm cache | 0.044 µs           | 0.115 µs             | 64.121 µs              | 1513.618 µs              |
| Cold cache | 0.143 µs           | 0.970 µs             | -                      | -                        |

Full-log classify time:

| Log                   | Time    | Crawlers found |
| --------------------- | ------- | -------------- |
| `apache_access_1.txt` | 2.22 ms | 6,462          |
| `apache_access_2.txt` | 0.77 ms | 2,480          |
| Combined              | 2.16 ms | 8,942          |

### IP verification

First-call rDNS latency is network-dependent.

| Function                 | Warm cache |
| ------------------------ | ---------- |
| `ip_in_range`            | 0.06 µs    |
| `known_crawler_ip`       | 0.08 µs    |
| `reverse_dns`            | 0.48 µs    |
| `forward_confirmed_rdns` | 3.69 µs    |
| `known_crawler_rdns`     | 4.27 µs    |
| `verify_crawler_ip`      | 3.23 µs    |

### Notes

- Warm cache reflects repeated lookups with LRU hits.
- Cold cache clears the public API caches between benchmark runs.
- DB patterns compile lazily per 48-entry chunk on first match.

## Implementation Notes

### Why regex-free?

Crawler detection runs on every request, so predictable runtime matters. `is-crawler` implements its hot-path heuristics with `str.find` plus char scans instead of regex backtracking. That keeps `is_crawler()` fast and avoids the usual ReDoS footguns from hostile user-agent strings.

`crawler_info()` does use `re`, but only against curated upstream patterns from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents), and those patterns are simple enough to avoid catastrophic backtracking in practice.

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
