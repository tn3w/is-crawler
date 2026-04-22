from __future__ import annotations

import json
import sys

from . import (
    crawler_info,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
)


def _analyze(user_agent: str) -> dict:
    info = crawler_info(user_agent)
    return {
        "user_agent": user_agent,
        "is_crawler": is_crawler(user_agent),
        "name": crawler_name(user_agent),
        "version": crawler_version(user_agent),
        "url": crawler_url(user_agent),
        "signals": crawler_signals(user_agent),
        "info": info._asdict() if info else None,
    }


def _iter_inputs(argv: list[str]):
    if len(argv) > 1:
        yield " ".join(argv[1:])
        return

    for line in sys.stdin:
        line = line.strip()
        if line:
            yield line


def main() -> int:
    for user_agent in _iter_inputs(sys.argv):
        print(json.dumps(_analyze(user_agent), ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
