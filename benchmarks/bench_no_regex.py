from __future__ import annotations

import time
from pathlib import Path

from is_crawler import crawler_name as rx_name
from is_crawler import crawler_url as rx_url
from is_crawler import crawler_version as rx_version
from is_crawler import is_crawler as rx_is_crawler
from is_crawler.no_regex import crawler_name as nr_name
from is_crawler.no_regex import crawler_url as nr_url
from is_crawler.no_regex import crawler_version as nr_version
from is_crawler.no_regex import is_crawler as nr_is_crawler

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures"


def load_uas() -> list[str]:
    uas = []
    for name in ("crawler_user_agents.txt", "browser_user_agents.txt"):
        uas += [
            l.strip() for l in (FIXTURES / name).read_text().splitlines() if l.strip()
        ]
    return uas


def bench(label: str, fn, uas: list[str], iters: int, clear_cache: bool) -> float:
    cache_clear = getattr(fn, "cache_clear", None)
    if cache_clear:
        cache_clear()
    start = time.perf_counter()
    for _ in range(iters):
        if clear_cache and cache_clear:
            cache_clear()
        for ua in uas:
            fn(ua)
    elapsed = time.perf_counter() - start
    total = iters * len(uas)
    per_call_ns = elapsed / total * 1e9
    print(f"  {label:24s} {elapsed:7.3f}s  {per_call_ns:8.0f} ns/call")
    return elapsed


def compare(name: str, rx_fn, nr_fn, uas: list[str], iters: int, clear: bool) -> None:
    mode = "cold cache" if clear else "warm cache"
    print(f"\n{name} - {mode} ({iters} × {len(uas)} = {iters * len(uas):,} calls)")
    rx_time = bench("regex", rx_fn, uas, iters, clear)
    nr_time = bench("no_regex", nr_fn, uas, iters, clear)
    ratio = nr_time / rx_time
    faster = "slower" if ratio > 1 else "faster"
    print(f"  → no_regex is {abs(ratio - 1) * 100:.1f}% {faster} ({ratio:.2f}x)")


def main() -> None:
    uas = load_uas()
    print(f"Loaded {len(uas):,} UAs from fixtures")

    for clear in (True, False):
        compare("is_crawler", rx_is_crawler, nr_is_crawler, uas, 3, clear)
        compare("crawler_name", rx_name, nr_name, uas, 3, clear)
        compare("crawler_version", rx_version, nr_version, uas, 3, clear)
        compare("crawler_url", rx_url, nr_url, uas, 3, clear)


if __name__ == "__main__":
    main()
