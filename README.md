<div align="center">

# is-crawler

Tiny, zero-dependency Python library that detects bots and crawlers from user-agent strings. Fast, lightweight, and ready to drop into any web app or API.

[![PyPI](https://img.shields.io/pypi/v/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![Python](https://img.shields.io/pypi/pyversions/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)
[![License](https://img.shields.io/github/license/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/issues)
[![Stars](https://img.shields.io/github/stars/tn3w/is-crawler?style=flat-square)](https://github.com/tn3w/is-crawler/stargazers)
[![Downloads](https://img.shields.io/pypi/dm/is-crawler?style=flat-square)](https://pypi.org/project/is-crawler/)

**Docs & live demo:** [is-crawler.tn3w.dev](https://is-crawler.tn3w.dev)

</div>

## Install

```bash
pip install is-crawler
```

## Usage

```python
from is_crawler import (
    is_crawler, crawler_signals, crawler_info,
    crawler_has_tag, crawler_name, crawler_version, crawler_url,
)

ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"

is_crawler(ua)                              # True

crawler_signals(ua)
# ['bot_signal', 'url_in_ua']

info = crawler_info(ua)
# CrawlerInfo(url='http://www.google.com/bot.html',
#             description="Google's main web crawling bot...",
#             tags=('search-engine',))
info.url          # 'http://www.google.com/bot.html'
info.description  # "Google's main web crawling bot for search indexing"
info.tags         # ('search-engine',)

crawler_has_tag(ua, "search-engine")        # True
crawler_has_tag(ua, ["ai-crawler", "seo"])  # False

crawler_name(ua)     # 'Googlebot'
crawler_version(ua)  # '2.1'
crawler_url(ua)      # 'http://www.google.com/bot.html'
```

### API reference

| Function                   | Returns               | Description                                              |
| -------------------------- | --------------------- | -------------------------------------------------------- |
| `is_crawler(ua)`           | `bool`                | Heuristic detection: fast, no DB                         |
| `crawler_signals(ua)`      | `list[str]`           | Which heuristic rules matched                            |
| `crawler_info(ua)`         | `CrawlerInfo \| None` | url, description, tags: DB lookup for 646 known crawlers |
| `crawler_has_tag(ua, tag)` | `bool`                | `tag` can be `str` or `list[str]` (matches any)          |
| `crawler_name(ua)`         | `str \| None`         | Product name extracted from the UA string                |
| `crawler_version(ua)`      | `str \| None`         | Version extracted from the UA string                     |
| `crawler_url(ua)`          | `str \| None`         | URL embedded in the UA string                            |

`crawler_signals` returns a subset of: `bot_signal`, `no_browser_signature`, `bare_compatible`, `known_tool`, `url_in_ua`.

`crawler_info` tags: `search-engine`, `ai-crawler`, `seo`, `social-preview`, `advertising`, `archiver`, `feed-reader`, `monitoring`, `scanner`, `academic`, `http-library`, `browser-automation`.

### Middleware example

```python
from is_crawler import is_crawler, crawler_has_tag

@app.before_request
def gate():
    ua = request.headers.get("User-Agent", "")
    if crawler_has_tag(ua, "ai-crawler"):
        abort(403)        # block AI scrapers
    if is_crawler(ua):
        log_crawler(ua)   # track other bots without blocking
```

## How it works

**`is_crawler`**: three-step short-circuit, no DB lookup.

1. **Positive signal**: one fused regex combining bot keywords (`bot`, `crawl`, `spider`, `scrape`, `headless`, ...), known tools (`playwright`, `selenium`, `wget`, `lighthouse`, `sqlmap`, ...), and URL-in-UA patterns. One hit → crawler.
2. **No browser signature**: missing `WebKit`/`Gecko`/`Trident`/etc. → crawler.
3. **Bare `(compatible; ...)`**: classic bot block without OS tokens → crawler.

**`crawler_signals`**: exposes which of the five individual checks fired (bot_signal, no_browser_signature, bare_compatible, known_tool, url_in_ua). Useful for diagnostics; `is_crawler` does not call it.

**`crawler_info` / `crawler_has_tag`**: gated by `is_crawler` so browser UAs skip the DB entirely. On a crawler hit, patterns (from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents) plus supplemental tags) are sharded into 48-entry chunks; each chunk's combined filter and its per-pattern regexes compile lazily on first match. Returns url, description, and tags.

**Caching**: 32k-entry LRU cache on every public function. Repeat UAs hit in ~40 ns.

## Benchmarks

Measured on Python 3.14, Linux x86_64. Fixture corpus: **1 231 crawler UAs** and **15 812 browser UAs**.
`cua` is the [`crawler-user-agents`](https://pypi.org/project/crawler-user-agents/) PyPI package (v1.42, no caching).

### `is_crawler`: heuristic detection (no DB)

| Corpus        | is_crawler | `cua.is_crawler` | speedup |
| ------------- | ---------- | ---------------- | ------- |
| crawlers only | 0.39 µs    | 61.7 µs          | 158×    |
| browsers only | 3.76 µs    | 182.7 µs         | 49×     |
| mixed         | 0.04 µs    | 167.7 µs         | 4000×   |

Crawler UAs hit a single combined positive regex; browser UAs fall through to a browser-signature check. A 32k-entry LRU cache drives mixed-corpus calls to near-zero amortized cost.

### `crawler_info` / `crawler_has_tag`: DB pattern lookup

|                   | is_crawler | `cua` equivalent | speedup |
| ----------------- | ---------- | ---------------- | ------- |
| `crawler_info`    | 0.53 µs    | 743.0 µs         | 1400×   |
| `crawler_has_tag` | 0.14 µs    | -                | -       |

Browser UAs short-circuit via `is_crawler` before touching the DB. Matching walks 48-entry combined chunks to locate the winning pattern in ~1/25 of the full-scan work. `crawler_has_tag` delegates to cached `crawler_info`; cost is independent of tag cardinality.

### Cold-start

| Module              | Cold-start | Notes                         |
| ------------------- | ---------- | ----------------------------- |
| `is_crawler`        | 0.55 ms    | JSON parse; regexes stay lazy |
| `crawleruseragents` | 0.89 ms    | JSON parse                    |

DB patterns compile lazily per 48-entry chunk on first match, import and `_ensure_db` stay cheap.

### Single-UA uncached benchmark

|                      | is_crawler | `cua.is_crawler` | speedup |
| -------------------- | ---------- | ---------------- | ------- |
| `Googlebot` uncached | 1.710 µs   | 70.419 µs        | 41×     |

Direct apples-to-apples check on one crawler UA. Same `Googlebot/2.1 (+http://www.google.com/bot.html)` over 1,000 runs. `is_crawler` clears caches before each call; `cua` reloads `crawleruseragents` before each call.

## Formatting

```bash
pip install black isort
isort . && black .
npx prtfm
```

## License

[Apache-2.0](LICENSE)
