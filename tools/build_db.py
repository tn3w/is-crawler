#!/usr/bin/env python3
"""
Build is_crawler/crawler-user-agents.json from the upstream source,
merging tags from a local flags mapping.

The upstream source (monperrus/crawler-user-agents) does not include tags, so
tools/crawler-user-agents-flags.json maps each pattern to its tag list.

Output format: JSON array of [pattern, url, description, [tags]].
Instances are omitted to keep the file small.

Usage:
    python3 tools/build_db.py \\
        [--input  crawler-user-agents.json] \\
        [--output is_crawler/crawler-user-agents.json] \\
        [--flags  tools/crawler-user-agents-flags.json]
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DEFAULT_INPUT = REPO_ROOT / "crawler-user-agents.json"
DEFAULT_OUTPUT = REPO_ROOT / "is_crawler" / "crawler-user-agents.json"
DEFAULT_FLAGS = REPO_ROOT / "tools" / "crawler-user-agents-flags.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--input", default=DEFAULT_INPUT, type=Path, metavar="FILE")
    p.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, metavar="FILE")
    p.add_argument("--flags", default=DEFAULT_FLAGS, type=Path, metavar="FILE")
    return p.parse_args()


def load_flags(flags_path: Path) -> dict[str, list[str]]:
    if not flags_path.exists():
        print(f"Warning: flags file not found at {flags_path}", file=sys.stderr)
        return {}
    with flags_path.open(encoding="utf-8") as f:
        return json.load(f)


def build_db(input_path: Path, output_path: Path, flags_path: Path) -> None:
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    flags = load_flags(flags_path)

    rows = [
        [
            entry.get("pattern", ""),
            entry.get("url", ""),
            entry.get("description", ""),
            entry.get("tags") or flags.get(entry.get("pattern", ""), []),
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
    build_db(args.input, args.output, args.flags)
