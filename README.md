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
from is_crawler import is_crawler, crawler_info, crawler_has_tag

ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"

is_crawler(ua)                              # True
crawler_has_tag(ua, "search-engine")        # True
crawler_has_tag(ua, ["ai-crawler", "seo"])  # False

info = crawler_info(ua)
# CrawlerInfo(url='http://www.google.com/bot.html',
#             description="Google's main web crawling bot...",
#             tags=('search-engine',))
info.url          # 'http://www.google.com/bot.html'
info.description  # "Google's main web crawling bot for search indexing"
info.tags         # ('search-engine',)
```

The module is also callable directly, no named import required:

```python
import is_crawler
is_crawler("Googlebot/2.1 (+http://www.google.com/bot.html)")  # True
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

**`is_crawler` / `crawler_signals`**: five heuristic regex checks, no lookup:

1. **Bot signals**: common keywords (`bot`, `crawl`, `spider`, `scrape`, ...), URL/email patterns, `headless`
2. **Missing browser signature**: real browsers always include engine tokens like `WebKit`, `Gecko`, or `Trident`
3. **Bare `(compatible; ...)` block**: classic bot pattern without OS tokens
4. **Known tools**: `playwright`, `selenium`, `wget`, `lighthouse`, `sqlmap`, and more
5. **URL in UA**: an embedded `http://` or `https://` URL, a near-universal bot convention

**`crawler_info` / `crawler_has_tag`**: pattern database loaded lazily on first call (no import-time I/O), built from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents) with supplemental tags. Returns url, description, and tags for 646 known crawlers.

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

## Formatting

```bash
pip install black isort
isort . && black .
npx prtfm
```

## License

[Apache-2.0](LICENSE)
