"""
Benchmarks for is_crawler vs crawler-user-agents (PyPI).

Compares stdlib re vs google-re2 (if available), and benchmarks
each public function against the equivalent crawleruseragents operation.

Run:
    python benchmarks/bench.py
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import time
from pathlib import Path
from statistics import mean, stdev
from typing import Callable

import crawleruseragents

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
CRAWLERS = [
    l.strip()
    for l in (FIXTURES / "crawler_user_agents.txt").read_text().splitlines()
    if l.strip()
]
BROWSERS = [
    l.strip()
    for l in (FIXTURES / "browser_user_agents.txt").read_text().splitlines()
    if l.strip()
]
ALL_UAS = CRAWLERS + BROWSERS

_HAS_RE2 = importlib.util.find_spec("re2") is not None


# ---------------------------------------------------------------------------
# timing helpers
# ---------------------------------------------------------------------------


def _timeit(
    fn: Callable, args: list, iterations: int = 5, warmup: int = 2
) -> tuple[float, float]:
    """Return (mean, stdev) seconds-per-call over `iterations` passes."""
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


# ---------------------------------------------------------------------------
# module reload helpers (switch re vs re2 backend)
# ---------------------------------------------------------------------------


def _load_ic_with(use_re2: bool):
    """Reload is_crawler forcing a specific regex backend. Returns the module."""
    # block or restore re2 in sys.modules before reload
    re2_backup = sys.modules.get("re2", _sentinel := object())
    if use_re2:
        if not _HAS_RE2:
            return None
        sys.modules.pop("re2", None)  # let natural import succeed
    else:
        sys.modules["re2"] = None  # type: ignore[assignment]  # ImportError sentinel

    try:
        import is_crawler as _ic

        _ic._load_crawler_db.cache_clear()
        for fn_name in (
            "is_crawler",
            "crawler_info",
            "crawler_signals",
            "crawler_name",
            "crawler_version",
            "crawler_url",
            "crawler_has_tag",
            "_crawler_has_tag_cached",
        ):
            fn = getattr(_ic, fn_name, None)
            if fn and hasattr(fn, "cache_clear"):
                fn.cache_clear()
        mod = importlib.reload(_ic)
        mod._load_crawler_db()
        return mod
    finally:
        if re2_backup is _sentinel:
            sys.modules.pop("re2", None)
        else:
            sys.modules["re2"] = re2_backup  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# cold-start
# ---------------------------------------------------------------------------


def bench_cold_start(ic_re2, ic_re):
    print("\n── Cold-start (CSV parse + regex compile) ──")

    for label, mod in [("stdlib re ", ic_re), ("re2       ", ic_re2)]:
        if mod is None:
            continue

        def _reload(mod=mod):
            mod._load_crawler_db.cache_clear()
            mod._load_crawler_db()

        m, sd = _cold_time(_reload)
        ms, sd_ms = m * 1000, sd * 1000
        print(f"  is_crawler ({label}): {ms:7.2f} ms ± {sd_ms:.2f}")

    def _reload_cua():
        importlib.reload(crawleruseragents)

    m, sd = _cold_time(_reload_cua)
    ms, sd_ms = m * 1000, sd * 1000
    print(f"  crawleruseragents    : {ms:7.2f} ms ± {sd_ms:.2f}")


# ---------------------------------------------------------------------------
# hot-path benchmarks per backend
# ---------------------------------------------------------------------------


def _cua_info(ua: str):
    indices = crawleruseragents.matching_crawlers(ua)
    return crawleruseragents.CRAWLER_USER_AGENTS_DATA[indices[0]] if indices else None


def _cua_is_crawler(ua: str) -> bool:
    return crawleruseragents.is_crawler(ua)


def bench_hot(mod, label: str):
    ic = mod.is_crawler
    ci = mod.crawler_info
    cs = mod.crawler_signals
    cn = mod.crawler_name
    cv = mod.crawler_version
    cu = mod.crawler_url
    cht = mod.crawler_has_tag

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

    print(f"\n── Hot-path per-call [{label}] ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


def bench_cua():
    rows: list[tuple[str, Callable, list]] = [
        ("cua.is_crawler (crawlers)        ", _cua_is_crawler, CRAWLERS),
        ("cua.is_crawler (browsers)        ", _cua_is_crawler, BROWSERS),
        ("cua.is_crawler (mixed)           ", _cua_is_crawler, ALL_UAS),
        (
            "cua.matching_crawlers (mixed)    ",
            crawleruseragents.matching_crawlers,
            ALL_UAS,
        ),
        ("cua.crawler_info equiv (mixed)   ", _cua_info, ALL_UAS),
    ]

    print("\n── Hot-path per-call [crawleruseragents] ──")
    for name, fn, args in rows:
        m, sd = _timeit(fn, args)
        print(f"  {name}: {_fmt(m, sd)}")


# ---------------------------------------------------------------------------
# accuracy
# ---------------------------------------------------------------------------


def bench_accuracy(mod):
    ic = mod.is_crawler
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


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(
        f"crawlers={len(CRAWLERS)}  browsers={len(BROWSERS)}  "
        f"re2={'available' if _HAS_RE2 else 'not installed'}"
    )

    ic_re2 = _load_ic_with(use_re2=True)
    ic_re = _load_ic_with(use_re2=False)

    backends = [(ic_re, "stdlib re")]
    if ic_re2 is not None:
        backends.append((ic_re2, "re2      "))

    bench_cold_start(ic_re2, ic_re)

    for mod, label in backends:
        bench_hot(mod, label)

    bench_cua()
    bench_accuracy(ic_re)
