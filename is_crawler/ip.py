from __future__ import annotations

import json
import socket
from functools import lru_cache
from pathlib import Path

from . import crawler_name

__all__ = ["verify_crawler_ip", "reverse_dns", "forward_confirmed_rdns"]

_CACHE = 4096

_RDNS_DOMAINS: dict[str, tuple[str, ...]] | None = None


def _load_domains() -> dict[str, tuple[str, ...]]:
    global _RDNS_DOMAINS
    if _RDNS_DOMAINS is not None:
        return _RDNS_DOMAINS

    path = Path(__file__).parent / "crawler-rdns.json"
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)

    mapping: dict[str, tuple[str, ...]] = {}
    for suffix_key, names in raw.items():
        suffixes = tuple(suffix_key.split())
        for name in names:
            mapping[name.lower()] = suffixes

    _RDNS_DOMAINS = mapping
    return mapping


def _domains_for(name: str) -> tuple[str, ...] | None:
    mapping = _load_domains()
    key = name.lower()
    if key in mapping:
        return mapping[key]

    base = key.split("/", 1)[0].split()[0] if key else ""
    return mapping.get(base)


@lru_cache(maxsize=_CACHE)
def reverse_dns(ip: str) -> str | None:
    try:
        host, _, _ = socket.gethostbyaddr(ip)
    except (OSError, socket.herror):
        return None
    return host.lower().rstrip(".")


@lru_cache(maxsize=_CACHE)
def _forward_ips(host: str) -> frozenset[str]:
    try:
        infos = socket.getaddrinfo(host, None)
    except (OSError, socket.gaierror):
        return frozenset()
    return frozenset(str(info[4][0]) for info in infos)


def forward_confirmed_rdns(ip: str, suffixes: tuple[str, ...]) -> str | None:
    host = reverse_dns(ip)
    if not host:
        return None

    if not any(host == s.lstrip(".") or host.endswith(s) for s in suffixes):
        return None

    return host if ip in _forward_ips(host) else None


def verify_crawler_ip(user_agent: str, ip: str) -> bool:
    name = crawler_name(user_agent)
    if not name:
        return False

    suffixes = _domains_for(name)
    if not suffixes:
        return False

    return forward_confirmed_rdns(ip, suffixes) is not None
