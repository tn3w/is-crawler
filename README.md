# is-crawler

Tiny, zero-dependency Python library that detects bots and crawlers from user-agent strings. Fast, lightweight, and ready to drop into any web app or API.

**Docs & live demo:** [is-crawler.tn3w.dev](https://is-crawler.tn3w.dev)

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
from is_crawler import is_crawler

is_crawler("Googlebot/2.1 (+http://www.google.com/bot.html)")  # True
is_crawler("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36")  # False
```

The module itself is also callable, so you can skip the named import:

```python
import is_crawler

is_crawler("Googlebot/2.1 (+http://www.google.com/bot.html)")  # True
```

Works great as middleware, rate-limiter input, or analytics filter:

```python
from is_crawler import is_crawler

@app.before_request
def block_bots():
    if is_crawler(request.headers.get("User-Agent", "")):
        abort(403)
```

## How it works

Four fast regex checks, no database or external lookups:

1. **Bot signals** -- common keywords (`bot`, `crawl`, `spider`, `scrape`, ...), URL/email patterns, `headless`
2. **Missing browser signature** -- real browsers always include engine tokens like `WebKit`, `Gecko`, or `Trident`
3. **Bare `(compatible; ...)` block** -- classic bot pattern without OS tokens
4. **Known tools** -- `playwright`, `selenium`, `wget`, `lighthouse`, `sqlmap`, and more

## Need more?

If you need deeper user-agent analysis -- device type, OS, browser version, or full bot fingerprinting -- check out [cr-ua](https://github.com/tn3w/crua).

## License

Apache-2.0
