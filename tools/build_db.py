#!/usr/bin/env python3
"""
Build is_crawler/crawler-user-agents.json from the upstream source.

Output format: JSON array of [pattern, url, description, [tags]].
Instances are omitted to keep the file small.

Usage:
    python3 tools/build_db.py \\
        [--input  crawler-user-agents.json] \\
        [--output is_crawler/crawler-user-agents.json] \\
"""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent

DEFAULT_INPUT = REPO_ROOT / "crawler-user-agents.json"
DEFAULT_EXTRA = TOOLS_DIR / "extra-crawler-user-agents.json"
DEFAULT_OUTPUT = REPO_ROOT / "is_crawler" / "crawler-user-agents.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--input", default=DEFAULT_INPUT, type=Path, metavar="FILE")
    p.add_argument("--extra", default=DEFAULT_EXTRA, type=Path, metavar="FILE")
    p.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, metavar="FILE")
    return p.parse_args()


def build_db(input_path: Path, extra_path: Path, output_path: Path) -> None:
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if extra_path.exists():
        with extra_path.open(encoding="utf-8") as f:
            data = data + json.load(f)

    rows = [
        [
            entry.get("pattern", ""),
            entry.get("url", ""),
            entry.get("description", ""),
            entry.get("tags"),
        ]
        for entry in data
    ]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))

    print(
        f"Wrote {len(rows)} entries to {output_path} ({output_path.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    args = parse_args()
    build_db(args.input, args.extra, args.output)
