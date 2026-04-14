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

For faster regex matching, optionally install [google-re2](https://pypi.org/project/google-re2/). It will be used automatically when available:

```bash
pip install is-crawler google-re2
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
#             description="Google's main web crawling bot for search indexing",
#             tags=['search-engine'])
info.url          # 'http://www.google.com/bot.html'
info.description  # "Google's main web crawling bot for search indexing"
info.tags         # ['search-engine']
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

**`crawler_info` / `crawler_has_tag`**: pattern database loaded lazily on first call, built from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents) with supplemental tags. Returns url, description, and tags for 646 known crawlers.

## Benchmarks

Measured on Python 3.14, Linux x86_64, stdlib `re` and `google-re2` backends.
Fixture corpus: **1 231 crawler UAs** and **15 812 browser UAs** from the test suite.
Each function is timed over the full mixed corpus (17 043 UAs) with `lru_cache(8192)` warm, so results reflect the realistic cache-hit/miss ratio at that corpus size.
`crawleruseragents` is the [`crawler-user-agents`](https://pypi.org/project/crawler-user-agents/) PyPI package (v1.42, no caching).

### `is_crawler`: heuristic detection (no DB)

| Corpus        | stdlib re | re2     | `cua.is_crawler` | vs re2 | vs cua |
| ------------- | --------- | ------- | ---------------- | ------ | ------ |
| crawlers only | 0.78 µs   | 0.26 µs | 61.7 µs          | 3×     | 79×    |
| browsers only | 73.1 µs   | 25.2 µs | 173.3 µs         | 2.9×   | 2.4×   |
| mixed         | 30.8 µs   | 23.8 µs | 163.7 µs         | 1.3×   | 5.3×   |

Speedups are re2 vs stdlib re and is_crawler (stdlib re) vs cua respectively.
`is_crawler` is purely heuristic: no DB involved. Crawler UAs are fast because the first heuristic (`bot_signal`) triggers immediately; browser UAs must exhaust all five checks.

### `crawler_info`: DB pattern lookup

|              | stdlib re | re2     | `cua` equivalent | vs cua |
| ------------ | --------- | ------- | ---------------- | ------ |
| mixed corpus | 75.7 µs   | 75.3 µs | 1 172 µs         | 15×    |

`cua` equivalent = `matching_crawlers(ua)[0]` + `CRAWLER_USER_AGENTS_DATA[idx]` lookup. DB scan timing is dominated by pattern matching, not re2 compile; re2 gives no gain here because most UAs are browsers that scan all 646 patterns before returning `None`.

### `crawler_has_tag`

| Tag                       | stdlib re | re2     | Patterns checked |
| ------------------------- | --------- | ------- | ---------------- |
| `seo` (252 entries)       | 49.5 µs   | 49.6 µs | ≤ 252            |
| `ai-crawler` (22 entries) | 5.4 µs    | 5.4 µs  | ≤ 22             |

Tag index built at load time; only patterns that carry the requested tag are searched.

### Cold-start (JSON parse + 646 `re.compile` calls)

|      | stdlib re | re2     | `crawleruseragents` |
| ---- | --------- | ------- | ------------------- |
| time | 36.2 ms   | 35.7 ms | 3.5 ms              |

`crawleruseragents` is faster to load because it ships pre-compiled data with no regex work at import time.

## Formatting

```bash
pip install black isort
isort . && black .
```

## License

[Apache-2.0](LICENSE)
