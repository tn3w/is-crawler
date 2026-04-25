#!/usr/bin/env python3
"""
Fetch IP ranges for known crawlers and build is_crawler/crawler-ip-ranges.json.

Reads source definitions from tools/crawler-ip-ranges.json (name → {url, pattern}),
fetches each URL, extracts all CIDRs via the regex pattern, and writes a flat
JSON object mapping each source name to a sorted list of CIDR strings.

Usage:
    python3 tools/build_ip_ranges.py \\
        [--sources tools/crawler-ip-ranges.json] \\
        [--output  is_crawler/crawler-ip-ranges.json] \\
        [--timeout 20] \\
        [--skip-errors]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import urllib.request

REPO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent

DEFAULT_SOURCES = TOOLS_DIR / "crawler-ip-ranges.json"
DEFAULT_OUTPUT = REPO_ROOT / "is_crawler" / "crawler-ip-ranges.json"
DEFAULT_TIMEOUT = 20

_UA = "is-crawler-build/1.0 (+https://github.com/tn3w/is-crawler)"


def fetch(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_cidrs(body: str, pattern: str) -> list[str]:
    raw = re.findall(pattern, body)
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        item = item.strip().strip('"').strip("'").strip("`")
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return sorted(result)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--sources", default=DEFAULT_SOURCES, type=Path, metavar="FILE")
    p.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, metavar="FILE")
    p.add_argument("--timeout", default=DEFAULT_TIMEOUT, type=int, metavar="SECS")
    p.add_argument(
        "--skip-errors",
        action="store_true",
        help="continue on fetch/parse errors instead of aborting",
    )
    return p.parse_args()


def build_ip_ranges(
    sources_path: Path,
    output_path: Path,
    timeout: int,
    skip_errors: bool,
) -> None:
    with sources_path.open(encoding="utf-8") as f:
        sources: dict[str, dict[str, str]] = json.load(f)

    result: dict[str, list[str]] = {}
    total = 0

    for name, entry in sources.items():
        url = entry["url"]
        pattern = entry["pattern"]
        try:
            body = fetch(url, timeout)
            cidrs = extract_cidrs(body, pattern)
            result[name] = cidrs
            total += len(cidrs)
            print(f"  {name}: {len(cidrs)} ranges")
        except Exception as exc:
            msg = f"  {name}: FAILED ({exc})"
            if skip_errors:
                print(msg, file=sys.stderr)
                result[name] = []
            else:
                print(msg, file=sys.stderr)
                sys.exit(1)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, separators=(",", ":"))

    print(
        f"\nWrote {len(result)} sources / {total} total ranges to "
        f"{output_path} ({output_path.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    args = parse_args()
    build_ip_ranges(args.sources, args.output, args.timeout, args.skip_errors)
