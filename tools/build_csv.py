#!/usr/bin/env python3
"""
Build crawler-user-agents.csv from a crawler-user-agents.json source,
optionally supplementing missing tags from a local flags mapping.

The upstream crawler-user-agents.json (monperrus/crawler-user-agents) does not
include tags, so a local flags file (crawler-user-agents-flags.json) maps each
regex pattern to its tag list and is merged in before writing the CSV.

Columns in the output CSV:
    pattern     - regex pattern used to identify the crawler
    url         - reference/info URL for the crawler (may be empty)
    description - human-readable description of the crawler
    tags        - semicolon-separated list of tags, e.g. "search-engine;ai-crawler"

Instances are intentionally omitted to keep the file small.

Usage:
    python3 tools/build_csv.py \\
        [--input  crawler-user-agents.json] \\
        [--output crawler-user-agents.csv]  \\
        [--flags  tools/crawler-user-agents-flags.json]
"""

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DEFAULT_INPUT  = REPO_ROOT / "crawler-user-agents.json"
DEFAULT_OUTPUT = REPO_ROOT / "crawler-user-agents.csv"
DEFAULT_FLAGS  = REPO_ROOT / "tools" / "crawler-user-agents-flags.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input",  default=DEFAULT_INPUT,  type=Path, metavar="FILE",
                   help="source JSON file (default: %(default)s)")
    p.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, metavar="FILE",
                   help="output CSV file (default: %(default)s)")
    p.add_argument("--flags",  default=DEFAULT_FLAGS,  type=Path, metavar="FILE",
                   help="supplemental pattern→tags JSON mapping (default: %(default)s)")
    return p.parse_args()


def load_flags(flags_path: Path) -> dict[str, list[str]]:
    if not flags_path.exists():
        print(f"Warning: flags file not found at {flags_path}, tags will be empty", file=sys.stderr)
        return {}
    with flags_path.open(encoding="utf-8") as f:
        return json.load(f)


def build_csv(input_path: Path, output_path: Path, flags_path: Path) -> None:
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    flags = load_flags(flags_path)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pattern", "url", "description", "tags"])
        for entry in data:
            pattern = entry.get("pattern", "")
            # Prefer tags already present in the source; fall back to flags mapping.
            tags = entry.get("tags") or flags.get(pattern, [])
            writer.writerow([
                pattern,
                entry.get("url", ""),
                entry.get("description", ""),
                ";".join(tags),
            ])

    print(f"Wrote {len(data)} entries to {output_path} ({output_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    args = parse_args()
    build_csv(args.input, args.output, args.flags)
