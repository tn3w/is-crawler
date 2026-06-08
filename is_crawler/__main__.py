from __future__ import annotations

import json
import sys

from . import (
    __version__,
    build_ai_txt,
    build_robots_txt,
    crawler_contact,
    crawler_info,
    crawler_matches,
    crawler_name,
    crawler_signals,
    crawler_url,
    crawler_version,
    is_crawler,
)
from .ip import known_crawler_ip, known_crawler_rdns, reverse_dns, verify_crawler_ip
from .parser import parse

_USAGE = (
    "Usage: is-crawler [COMMAND] [ARGS...]\n\n"
    "Detect, classify, parse, and verify web crawlers.\n\n"
    "Commands:\n"
    "  detect [UA...]    Analyze user agents (default). One JSON object per UA.\n"
    "  parse [UA...]     Full user-agent parse (browser, OS, device, ...).\n"
    "  verify <UA> <IP>  Forward-confirmed rDNS spoof check for a UA and IP.\n"
    "  ip <IP...>        Check IPs against known crawler ranges and rDNS.\n"
    "  robots            Generate robots.txt from tags.\n"
    "  ai-txt            Generate ai.txt (disallow AI crawlers).\n\n"
    "detect/parse read UAs from stdin when none are given.\n\n"
    "robots options:\n"
    "  --disallow TAGS   Comma-separated tags to disallow.\n"
    "  --allow TAGS      Comma-separated tags to allow.\n"
    "  --path PATH       Path for the directives (default /).\n\n"
    "ai-txt options:\n"
    "  --disallow TAGS   Comma-separated tags (default ai-crawler).\n\n"
    "Options:\n"
    "  -p, --pretty      Pretty-print JSON output.\n"
    "  -h, --help        Show this help and exit.\n"
    "  -V, --version     Show version and exit."
)


def _analyze(user_agent: str) -> dict:
    info = crawler_info(user_agent)
    return {
        "user_agent": user_agent,
        "is_crawler": is_crawler(user_agent),
        "name": crawler_name(user_agent),
        "version": crawler_version(user_agent),
        "url": crawler_url(user_agent),
        "contact": crawler_contact(user_agent),
        "signals": crawler_signals(user_agent),
        "matches": crawler_matches(user_agent),
        "info": info._asdict() if info else None,
    }


def _iter_inputs(operands: list[str]):
    if operands:
        yield " ".join(operands)
        return

    for line in sys.stdin:
        line = line.strip()
        if line:
            yield line


def _dump(obj: object, pretty: bool) -> str:
    indent = 2 if pretty else None
    return json.dumps(obj, ensure_ascii=False, indent=indent)


def _split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _pop_option(operands: list[str], name: str) -> str | None:
    if name not in operands:
        return None
    i = operands.index(name)
    value = operands[i + 1] if i + 1 < len(operands) else None
    del operands[i : i + 2]
    return value


def _cmd_detect(operands: list[str], pretty: bool) -> int:
    for user_agent in _iter_inputs(operands):
        print(_dump(_analyze(user_agent), pretty))
    return 0


def _cmd_parse(operands: list[str], pretty: bool) -> int:
    for user_agent in _iter_inputs(operands):
        print(_dump(parse(user_agent).to_dict(), pretty))
    return 0


def _cmd_verify(operands: list[str], pretty: bool) -> int:
    if len(operands) < 2:
        print("verify requires <USER_AGENT> <IP>", file=sys.stderr)
        return 2

    ip = operands[-1]
    user_agent = " ".join(operands[:-1])
    result = {
        "user_agent": user_agent,
        "ip": ip,
        "verified": verify_crawler_ip(user_agent, ip),
        "in_ip_range": known_crawler_ip(ip),
        "rdns": reverse_dns(ip),
        "rdns_match": known_crawler_rdns(ip),
    }
    print(_dump(result, pretty))
    return 0


def _cmd_ip(operands: list[str], pretty: bool) -> int:
    if not operands:
        print("ip requires at least one IP", file=sys.stderr)
        return 2

    for ip in operands:
        result = {
            "ip": ip,
            "in_ip_range": known_crawler_ip(ip),
            "rdns": reverse_dns(ip),
            "rdns_match": known_crawler_rdns(ip),
        }
        print(_dump(result, pretty))
    return 0


def _cmd_robots(operands: list[str], pretty: bool) -> int:
    disallow = _split_tags(_pop_option(operands, "--disallow"))
    allow = _split_tags(_pop_option(operands, "--allow"))
    path = _pop_option(operands, "--path") or "/"
    sys.stdout.write(build_robots_txt(disallow=disallow, allow=allow, path=path))
    return 0


def _cmd_ai_txt(operands: list[str], pretty: bool) -> int:
    disallow = _split_tags(_pop_option(operands, "--disallow")) or "ai-crawler"
    sys.stdout.write(build_ai_txt(disallow=disallow))
    return 0


_COMMANDS = {
    "detect": _cmd_detect,
    "parse": _cmd_parse,
    "verify": _cmd_verify,
    "ip": _cmd_ip,
    "robots": _cmd_robots,
    "ai-txt": _cmd_ai_txt,
}


def _take_flag(args: list[str], *names: str) -> bool:
    present = False
    for name in names:
        while name in args:
            args.remove(name)
            present = True
    return present


def main() -> int:
    args = sys.argv[1:]

    if _take_flag(args, "-h", "--help"):
        print(_USAGE)
        return 0
    if _take_flag(args, "-V", "--version"):
        print(__version__)
        return 0

    pretty = _take_flag(args, "-p", "--pretty")

    if args and args[0].startswith("-"):
        print(f"is-crawler: unknown option: {args[0]}", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        return 2

    if args and args[0] in _COMMANDS:
        return _COMMANDS[args[0]](args[1:], pretty)
    return _cmd_detect(args, pretty)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
