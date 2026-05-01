"""
Benchmark is_crawler.parser vs ua-parser against browser_user_agents.txt.

Run:
    python benchmarks/bench_parser.py
"""

from __future__ import annotations

from pathlib import Path
from statistics import mean, stdev
import sys
import time

from is_crawler.parser import parse

WITH_UAP = "--with-uap" in sys.argv

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
BROWSERS = [
    line.strip()
    for line in (FIXTURES / "browser_user_agents.txt").read_text().splitlines()
    if line.strip()
]

if WITH_UAP:
    import ua_parser as _uap

    _ua_parse = _uap.Parser(_uap.BasicResolver(_uap.load_builtins())).parse
else:
    _ua_parse = None


def _timeit(fn, args: list, iterations: int = 5, warmup: int = 2) -> tuple[float, float]:
    reps = max(1, (iterations * 1000) // len(args))
    all_args = args * reps
    total = len(all_args)

    for _ in range(warmup):
        for a in all_args[:200]:
            fn(a)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        for a in all_args:
            fn(a)
        times.append((time.perf_counter() - t0) / total)

    return mean(times), stdev(times) if len(times) > 1 else 0.0


def _timeit_cold(fn, args: list, iterations: int = 5) -> tuple[float, float]:
    cache_clear = getattr(fn, "cache_clear", None)
    times = []
    for _ in range(iterations):
        if cache_clear:
            cache_clear()
        t0 = time.perf_counter()
        for a in args:
            fn(a)
        times.append((time.perf_counter() - t0) / len(args))
    return mean(times), stdev(times) if len(times) > 1 else 0.0


def _fmt(m: float, sd: float) -> str:
    us, sd_us = m * 1e6, sd * 1e6
    return f"{us:8.2f} µs ± {sd_us:.2f}"


def bench_hot():
    print("\n── Hot-path (warm cache) ──")
    rows: list = [("is_crawler.parser.parse", parse)]
    if WITH_UAP:
        rows.append(("ua-parser              ", _ua_parse))
    for name, fn in rows:
        m, sd = _timeit(fn, BROWSERS)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_cold():
    print("\n── Cold-cache (per-call, no lru hits) ──")
    rows: list = [("is_crawler.parser.parse", parse)]
    if WITH_UAP:
        rows.append(("ua-parser              ", _ua_parse))
    for name, fn in rows:
        m, sd = _timeit_cold(fn, BROWSERS)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_fields():
    print("\n── Field coverage on browser_user_agents.txt ──")
    fields = ("browser", "browser_version", "os", "os_version", "device", "device_brand")
    bool_fields = ("is_webview", "is_headless")
    str_fields = ("channel", "app", "app_version")
    totals = {f: 0 for f in (*fields, *str_fields)}
    bool_totals = {f: 0 for f in bool_fields}
    n = len(BROWSERS)

    for ua in BROWSERS:
        result = parse(ua)
        for f in fields:
            if getattr(result, f) is not None:
                totals[f] += 1
        for f in str_fields:
            if getattr(result, f) is not None:
                totals[f] += 1
        for f in bool_fields:
            if getattr(result, f):
                bool_totals[f] += 1

    for f in fields:
        pct = totals[f] / n * 100
        print(f"  {f:<16}: {totals[f]:5}/{n}  ({pct:.1f}%)")

    print()
    for f in bool_fields:
        print(f"  {f:<16}: {bool_totals[f]:5}/{n}  ({bool_totals[f] / n * 100:.1f}%)")
    for f in str_fields:
        pct = totals[f] / n * 100
        print(f"  {f:<16}: {totals[f]:5}/{n}  ({pct:.1f}%)")

    if not WITH_UAP:
        return

    print("\n  ua-parser fields:")
    ua_fields = (
        "family",
        "major",
        "os.family",
        "os.major",
        "device.family",
        "device.brand",
    )
    ua_totals = {f: 0 for f in ua_fields}

    for ua in BROWSERS:
        result = _ua_parse(ua)
        ua = result.user_agent
        os = result.os
        dev = result.device
        ua_totals["family"] += int(ua is not None and ua.family != "Other")
        ua_totals["major"] += int(ua is not None and ua.major is not None)
        ua_totals["os.family"] += int(os is not None and os.family != "Other")
        ua_totals["os.major"] += int(os is not None and os.major is not None)
        ua_totals["device.family"] += int(dev is not None and dev.family != "Other")
        ua_totals["device.brand"] += int(dev is not None and dev.brand is not None)

    label_map = dict(zip(ua_fields, fields))
    for f in ua_fields:
        pct = ua_totals[f] / n * 100
        print(f"  {label_map[f]:<16}: {ua_totals[f]:5}/{n}  ({pct:.1f}%)")


if __name__ == "__main__":
    print(f"browser UAs: {len(BROWSERS)}")
    bench_hot()
    bench_cold()
    bench_fields()
