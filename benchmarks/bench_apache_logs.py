"""
Apache access log benchmark for is_crawler.

Run:
    python benchmarks/bench_apache_logs.py
    python benchmarks/bench_apache_logs.py --with-cua
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from statistics import mean, stdev
import sys
import time
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import is_crawler as _ic
from is_crawler import database as _ic_db

_FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
_LOG_PATTERN = re.compile(r'"[^"]*" \d+ \d+ "[^"]*" "([^"]*)"$')


def _parse_user_agents(log_file: Path) -> list[str]:
    agents = []
    for line in log_file.read_text(errors="replace").splitlines():
        match = _LOG_PATTERN.search(line)
        if match:
            ua = match.group(1)
            if ua and ua != "-":
                agents.append(ua)
    return agents


def _timeit(fn, args: list, iterations: int = 5, warmup: int = 2) -> tuple[float, float]:
    for ua in args[:500]:
        fn(ua)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        for ua in args:
            fn(ua)
        times.append((time.perf_counter() - t0) / len(args))

    return mean(times), stdev(times) if len(times) > 1 else 0.0


def _timeit_cold(
    fn: Callable, args: list[str], iterations: int = 5
) -> tuple[float, float]:
    times = []
    for _ in range(iterations):
        _clear_ic_caches()
        t0 = time.perf_counter()
        for ua in args:
            fn(ua)
        times.append((time.perf_counter() - t0) / len(args))

    return mean(times), stdev(times) if len(times) > 1 else 0.0


def _fmt(m: float, sd: float) -> str:
    us, sd_us = m * 1e6, sd * 1e6
    return f"{us:7.3f} µs ± {sd_us:.3f}  ({1 / m:,.0f} calls/s)"


def _clear_ic_caches() -> None:
    _ic.crawler_signals.cache_clear()
    _ic.is_crawler.cache_clear()
    _ic.crawler_info.cache_clear()
    _ic.crawler_name.cache_clear()
    _ic.crawler_version.cache_clear()
    _ic.crawler_url.cache_clear()
    _ic_db._load_chunks.cache_clear()


def bench_apache_logs(all_agents: list[str], crawlers: list[str], browsers: list[str]):
    ic = _ic.is_crawler
    ci = _ic.crawler_info
    cn = _ic.crawler_name
    cv = _ic.crawler_version
    cu = _ic.crawler_url
    cs = _ic.crawler_signals

    rows = [
        ("is_crawler  (all)     ", ic, all_agents),
        ("is_crawler  (crawlers)", ic, crawlers),
        ("is_crawler  (browsers)", ic, browsers),
        ("crawler_info  (all)   ", ci, all_agents),
        ("crawler_name  (all)   ", cn, all_agents),
        ("crawler_version (all) ", cv, all_agents),
        ("crawler_url  (all)    ", cu, all_agents),
        ("crawler_signals (all) ", cs, all_agents),
    ]

    print("\n── Apache logs — hot-path throughput (warm cache) ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_apache_logs_cold_cache(
    all_agents: list[str], crawlers: list[str], browsers: list[str]
):
    ic = _ic.is_crawler
    ci = _ic.crawler_info
    cn = _ic.crawler_name
    cv = _ic.crawler_version
    cu = _ic.crawler_url
    cs = _ic.crawler_signals

    rows = [
        ("is_crawler  (all)     ", ic, all_agents),
        ("is_crawler  (crawlers)", ic, crawlers),
        ("is_crawler  (browsers)", ic, browsers),
        ("crawler_info  (all)   ", ci, all_agents),
        ("crawler_name  (all)   ", cn, all_agents),
        ("crawler_version (all) ", cv, all_agents),
        ("crawler_url  (all)    ", cu, all_agents),
        ("crawler_signals (all) ", cs, all_agents),
    ]

    print("\n── Apache logs — cold-cache throughput ──")
    for name, fn, args in rows:
        m, sd = _timeit_cold(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_cua_comparison(all_agents: list[str], crawlers: list[str], browsers: list[str]):
    import crawleruseragents

    def _cua_info(ua: str):
        indices = crawleruseragents.matching_crawlers(ua)
        return crawleruseragents.CRAWLER_USER_AGENTS_DATA[indices[0]] if indices else None

    rows = [
        ("cua.is_crawler (all)      ", crawleruseragents.is_crawler, all_agents),
        ("cua.is_crawler (crawlers) ", crawleruseragents.is_crawler, crawlers),
        ("cua.is_crawler (browsers) ", crawleruseragents.is_crawler, browsers),
        ("cua.crawler_info (all)    ", _cua_info, all_agents),
    ]

    print("\n── crawleruseragents comparison (Apache logs) ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_full_log_timing(log1: list[str], log2: list[str], all_agents: list[str]):
    ic = _ic.is_crawler
    print("\n── Full-log parse + classify timing ──")
    for label, agents in [
        ("apache_access_1.txt", log1),
        ("apache_access_2.txt", log2),
        ("combined", all_agents),
    ]:
        times = []
        detected = 0
        for _ in range(5):
            t0 = time.perf_counter()
            detected = sum(1 for ua in agents if ic(ua))
            times.append(time.perf_counter() - t0)
        m = mean(times)
        print(f"  {label:<22}: {m * 1000:6.2f} ms  ({detected:,} crawlers found)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-cua",
        action="store_true",
        help="also run crawleruseragents comparison benchmarks",
    )
    args = parser.parse_args()

    log1 = _parse_user_agents(_FIXTURES / "apache_access_1.txt")
    log2 = _parse_user_agents(_FIXTURES / "apache_access_2.txt")
    all_agents = log1 + log2

    crawlers = [ua for ua in all_agents if _ic.is_crawler(ua)]
    browsers = [ua for ua in all_agents if not _ic.is_crawler(ua)]

    print(f"apache_access_1.txt : {len(log1):,} UA entries")
    print(f"apache_access_2.txt : {len(log2):,} UA entries")
    print(
        f"total               : {len(all_agents):,}"
        f"  ({len(crawlers):,} crawlers, {len(browsers):,} browsers)"
    )
    print(f"crawler ratio       : {len(crawlers) / len(all_agents):.1%}")

    bench_apache_logs(all_agents, crawlers, browsers)
    bench_apache_logs_cold_cache(all_agents, crawlers, browsers)
    bench_full_log_timing(log1, log2, all_agents)

    if args.with_cua:
        bench_cua_comparison(all_agents, crawlers, browsers)


if __name__ == "__main__":
    main()
