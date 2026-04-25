"""
IP verification benchmark for is_crawler.ip.

Run:
    python benchmarks/bench_ip.py
"""

from __future__ import annotations

from statistics import mean, stdev
import time
from typing import Callable

from is_crawler.ip import (
    forward_confirmed_rdns,
    ip_in_range,
    known_crawler_ip,
    known_crawler_rdns,
    reverse_dns,
    verify_crawler_ip,
)

CRAWLER_IPS = [
    "66.249.66.1",
    "66.249.64.1",
    "66.249.68.1",
    "157.55.39.1",
    "40.77.167.1",
    "199.21.99.1",
    "17.0.0.1",
]

NON_CRAWLER_IPS = [
    "8.8.8.8",
    "1.1.1.1",
    "192.168.1.1",
    "10.0.0.1",
    "172.16.0.1",
    "93.184.216.34",
    "151.101.1.1",
]

ALL_IPS = CRAWLER_IPS + NON_CRAWLER_IPS

GOOGLEBOT_UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"
BINGBOT_UA = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
FAKE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

VERIFY_PAIRS = [
    (GOOGLEBOT_UA, "66.249.66.1"),
    (BINGBOT_UA, "157.55.39.1"),
    (GOOGLEBOT_UA, "8.8.8.8"),
    (FAKE_UA, "66.249.66.1"),
]


def _timeit(
    fn: Callable, args: list, iterations: int = 5, warmup: int = 2
) -> tuple[float, float]:
    reps = max(1, (iterations * 500) // len(args))
    all_args = args * reps
    total = len(all_args)

    for a in all_args[:50]:
        fn(*a) if isinstance(a, tuple) else fn(a)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        for a in all_args:
            fn(*a) if isinstance(a, tuple) else fn(a)
        times.append((time.perf_counter() - t0) / total)

    return mean(times), stdev(times) if len(times) > 1 else 0.0


def _fmt(m: float, sd: float) -> str:
    us, sd_us = m * 1e6, sd * 1e6
    return f"{us:8.3f} µs ± {sd_us:.3f}"


def bench_ip_range():
    rows = [
        ("ip_in_range     (crawlers)", ip_in_range, CRAWLER_IPS),
        ("ip_in_range     (non-crawl)", ip_in_range, NON_CRAWLER_IPS),
        ("ip_in_range     (mixed)   ", ip_in_range, ALL_IPS),
        ("known_crawler_ip (mixed)  ", known_crawler_ip, ALL_IPS),
    ]

    print("\n── IP range lookup (warm cache) ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_rdns_cached():
    print("\n── rDNS / FCrDNS (warm cache — network already resolved) ──")

    for ip in ALL_IPS:
        reverse_dns(ip)

    m, sd = _timeit(lambda ip: reverse_dns(ip), ALL_IPS)
    print(f"  reverse_dns       (mixed)   : {_fmt(m, sd)}")

    for ip in ALL_IPS:
        forward_confirmed_rdns(ip, (".googlebot.com",))

    m, sd = _timeit(lambda ip: forward_confirmed_rdns(ip, (".googlebot.com",)), ALL_IPS)
    print(f"  forward_conf_rdns (mixed)   : {_fmt(m, sd)}")

    for ip in ALL_IPS:
        known_crawler_rdns(ip)

    m, sd = _timeit(lambda ip: known_crawler_rdns(ip), ALL_IPS)
    print(f"  known_crawler_rdns (mixed)  : {_fmt(m, sd)}")


def bench_verify_cached():
    for ua, ip in VERIFY_PAIRS:
        verify_crawler_ip(ua, ip)

    print("\n── verify_crawler_ip (warm cache) ──")
    m, sd = _timeit(verify_crawler_ip, VERIFY_PAIRS)
    print(f"  verify_crawler_ip (mixed)   : {_fmt(m, sd)}")


def bench_network_note():
    print("\n── Note ──")
    print("  rDNS / FCrDNS first-call latency depends on network + DNS.")
    print("  Warm-cache numbers above reflect repeated lookups via lru_cache.")
    print("  ip_in_range is purely in-memory (no network calls).")


if __name__ == "__main__":
    print(f"crawler IPs={len(CRAWLER_IPS)}  non-crawler IPs={len(NON_CRAWLER_IPS)}")
    bench_ip_range()
    bench_rdns_cached()
    bench_verify_cached()
    bench_network_note()
