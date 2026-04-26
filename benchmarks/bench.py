"""
Benchmarks for is_crawler.

Run:
    python benchmarks/bench.py
    python benchmarks/bench.py --with-cua
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from statistics import mean, stdev
import time
from typing import Callable

import is_crawler as _ic
from is_crawler import _bare_compat, _bot_signal, _browser, _known_tool

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
CRAWLERS = [
    line.strip()
    for line in (FIXTURES / "crawler_user_agents.txt").read_text().splitlines()
    if line.strip()
]
BROWSERS = [
    line.strip()
    for line in (FIXTURES / "browser_user_agents.txt").read_text().splitlines()
    if line.strip()
]
ALL_UAS = CRAWLERS + BROWSERS


def _timeit(
    fn: Callable, args: list, iterations: int = 5, warmup: int = 2
) -> tuple[float, float]:
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


def _timeit_cold(fn: Callable, args: list, iterations: int = 5) -> tuple[float, float]:
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
    return f"{us:7.2f} µs ± {sd_us:.2f}"


def _cold_time(fn: Callable, iterations: int = 10) -> tuple[float, float]:
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return mean(times), stdev(times) if len(times) > 1 else 0.0


def bench_cold_start(with_cua: bool = False):
    print("\n── Cold-start (JSON parse + chunk build) ──")

    def _reload_and_init():
        from is_crawler import database as _db

        importlib.reload(_db)
        importlib.reload(_ic)

        _db.crawler_info.cache_clear()
        _db._load_chunks()

    m, sd = _cold_time(_reload_and_init)
    print(f"  is_crawler        : {m * 1000:7.2f} ms ± {sd * 1000:.2f}")

    if with_cua:
        import crawleruseragents

        m, sd = _cold_time(lambda: importlib.reload(crawleruseragents))
        print(f"  crawleruseragents : {m * 1000:7.2f} ms ± {sd * 1000:.2f}")


def bench_hot():
    ic = _ic.is_crawler
    ci = _ic.crawler_info
    cs = _ic.crawler_signals
    cn = _ic.crawler_name
    cv = _ic.crawler_version
    cu = _ic.crawler_url
    cht = _ic.crawler_has_tag

    rows: list[tuple[str, Callable, list]] = [
        ("is_crawler  (crawlers)", ic, CRAWLERS),
        ("is_crawler  (browsers)", ic, BROWSERS),
        ("is_crawler  (mixed)   ", ic, ALL_UAS),
        ("crawler_signals        ", cs, ALL_UAS),
        ("crawler_name           ", cn, ALL_UAS),
        ("crawler_version        ", cv, ALL_UAS),
        ("crawler_url            ", cu, ALL_UAS),
        ("crawler_info           ", ci, ALL_UAS),
        ("crawler_has_tag(seo)   ", lambda ua: cht(ua, "seo"), ALL_UAS),
        ("crawler_has_tag(ai)    ", lambda ua: cht(ua, "ai-crawler"), ALL_UAS),
    ]

    print("\n── Hot-path (warm cache) ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_cold_cache(with_cua: bool = False):
    ic = _ic.is_crawler
    ci = _ic.crawler_info
    cn = _ic.crawler_name
    cv = _ic.crawler_version
    cu = _ic.crawler_url

    rows: list[tuple[str, Callable, list]] = [
        ("is_crawler  (crawlers)", ic, CRAWLERS),
        ("is_crawler  (browsers)", ic, BROWSERS),
        ("is_crawler  (mixed)   ", ic, ALL_UAS),
        ("crawler_info           ", ci, ALL_UAS),
        ("crawler_name           ", cn, ALL_UAS),
        ("crawler_version        ", cv, ALL_UAS),
        ("crawler_url            ", cu, ALL_UAS),
    ]

    cua_rows: list[tuple[str, Callable, list]] = []
    if with_cua:
        import crawleruseragents

        def _cua_info(ua: str):
            indices = crawleruseragents.matching_crawlers(ua)
            return (
                crawleruseragents.CRAWLER_USER_AGENTS_DATA[indices[0]]
                if indices
                else None
            )

        cua_rows = [
            ("cua.is_crawler (crawlers)  ", crawleruseragents.is_crawler, CRAWLERS),
            ("cua.is_crawler (browsers)  ", crawleruseragents.is_crawler, BROWSERS),
            ("cua.is_crawler (mixed)     ", crawleruseragents.is_crawler, ALL_UAS),
            ("cua.crawler_info (mixed)   ", _cua_info, ALL_UAS),
        ]

    print("\n── Cold-cache (per-call, no lru hits) ──")
    for name, fn, args in rows:
        m, sd = _timeit_cold(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")

    if cua_rows:
        print("\n── Cold-cache [crawleruseragents] ──")
        for name, fn, args in cua_rows:
            m, sd = _timeit_cold(fn, args)
            print(f"  {name}: {_fmt(m, sd)}")


def bench_internals():
    rows: list[tuple[str, Callable]] = [
        ("_bot_signal (crawlers) ", _bot_signal),
        ("_bot_signal (browsers) ", _bot_signal),
        ("_known_tool (mixed)    ", _known_tool),
        ("_browser    (mixed)    ", _browser),
        ("_bare_compat (mixed)   ", _bare_compat),
    ]
    datasets = [CRAWLERS, BROWSERS, ALL_UAS, ALL_UAS, ALL_UAS]

    print("\n── Internal helpers (no cache) ──")
    for (name, fn), args in zip(rows, datasets):
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            for ua in args:
                fn(ua)
            times.append((time.perf_counter() - t0) / len(args))
        m, sd = mean(times), stdev(times)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_cua():
    import crawleruseragents

    def _cua_info(ua: str):
        indices = crawleruseragents.matching_crawlers(ua)
        return crawleruseragents.CRAWLER_USER_AGENTS_DATA[indices[0]] if indices else None

    rows: list[tuple[str, Callable, list]] = [
        ("cua.is_crawler (crawlers)        ", crawleruseragents.is_crawler, CRAWLERS),
        ("cua.is_crawler (browsers)        ", crawleruseragents.is_crawler, BROWSERS),
        ("cua.is_crawler (mixed)           ", crawleruseragents.is_crawler, ALL_UAS),
        (
            "cua.matching_crawlers (mixed)    ",
            crawleruseragents.matching_crawlers,
            ALL_UAS,
        ),
        ("cua.crawler_info equiv (mixed)   ", _cua_info, ALL_UAS),
    ]

    print("\n── Hot-path [crawleruseragents] ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_accuracy():
    import crawleruseragents

    ic = _ic.is_crawler
    print("\n── Accuracy vs crawleruseragents ground truth ──")

    tp = fp = fn = tn = 0
    fn_examples: list[str] = []
    fp_examples: list[str] = []

    for ua in CRAWLERS:
        cua = crawleruseragents.is_crawler(ua)
        ours = ic(ua)
        if cua and ours:
            tp += 1
        elif not cua and ours:
            fp += 1
            fp_examples.append(ua)
        elif cua and not ours:
            fn += 1
            fn_examples.append(ua)
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    print(f"  crawler UAs ({len(CRAWLERS)} samples)")
    print(f"    TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"    precision={precision:.3f}  recall={recall:.3f}  F1={f1:.3f}")

    if fn_examples:
        print(f"\n  False negatives (ours missed) [{len(fn_examples)}]:")
        for ua in fn_examples[:5]:
            print(f"    {ua!r}")
    if fp_examples:
        print(f"\n  False positives (ours flagged, cua missed) [{len(fp_examples)}]:")
        for ua in fp_examples[:5]:
            print(f"    {ua!r}")

    tp2 = fp2 = fn2 = tn2 = 0
    for ua in BROWSERS:
        cua = crawleruseragents.is_crawler(ua)
        ours = ic(ua)
        if not cua and not ours:
            tn2 += 1
        elif not cua and ours:
            fp2 += 1
        elif cua and not ours:
            fn2 += 1
        else:
            tp2 += 1

    specificity = tn2 / (tn2 + fp2) if (tn2 + fp2) else 1.0
    print(f"\n  browser UAs ({len(BROWSERS)} samples)")
    print(f"    TP={tp2}  FP={fp2}  FN={fn2}  TN={tn2}")
    print(f"    specificity={specificity:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-cua",
        action="store_true",
        help="also run crawleruseragents comparison benchmarks",
    )
    args = parser.parse_args()

    print(f"crawlers={len(CRAWLERS)}  browsers={len(BROWSERS)}")
    bench_cold_start(with_cua=args.with_cua)
    bench_hot()
    bench_cold_cache(with_cua=args.with_cua)
    bench_internals()
    if args.with_cua:
        bench_cua()
        bench_accuracy()
