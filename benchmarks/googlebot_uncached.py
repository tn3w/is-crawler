from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import is_crawler as ic

UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"
RUNS = 1000


def _fmt_us(seconds: float) -> str:
    return f"{seconds * 1e6:7.3f} µs"


def _fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:7.3f} ms"


def clear_ic_caches() -> None:
    ic.crawler_signals.cache_clear()
    ic.is_crawler.cache_clear()
    ic.crawler_info.cache_clear()
    ic.crawler_name.cache_clear()
    ic.crawler_version.cache_clear()
    ic.crawler_url.cache_clear()
    ic._chunks = None


def bench_is_crawler() -> dict[str, float]:
    durations = []

    for _ in range(RUNS):
        clear_ic_caches()
        start = time.perf_counter()
        ic.is_crawler(UA)
        durations.append(time.perf_counter() - start)

    return {
        "total": sum(durations),
        "avg": sum(durations) / RUNS,
        "fastest": min(durations),
        "slowest": max(durations),
    }


def bench_cua() -> dict[str, float]:
    import crawleruseragents

    durations = []

    for _ in range(RUNS):
        mod = importlib.reload(crawleruseragents)
        start = time.perf_counter()
        mod.is_crawler(UA)
        durations.append(time.perf_counter() - start)

    return {
        "total": sum(durations),
        "avg": sum(durations) / RUNS,
        "fastest": min(durations),
        "slowest": max(durations),
    }


def print_result(label: str, result: dict[str, float]) -> None:
    print(f"  {label:<18}: {_fmt_us(result['avg'])}/call")
    print(f"  {'total':<18}: {_fmt_ms(result['total'])}")
    print(f"  {'fastest':<18}: {_fmt_us(result['fastest'])}")
    print(f"  {'slowest':<18}: {_fmt_us(result['slowest'])}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-cua",
        action="store_true",
        help="also benchmark crawleruseragents on the same Googlebot UA",
    )
    args = parser.parse_args()

    print("── Googlebot uncached benchmark ──")
    print(f"  UA                : {UA}")
    print(f"  runs              : {RUNS}")

    print_result("is_crawler", bench_is_crawler())

    if args.with_cua:
        print_result("cua.is_crawler", bench_cua())


if __name__ == "__main__":
    main()
