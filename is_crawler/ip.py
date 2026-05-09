from __future__ import annotations

import bisect
from functools import lru_cache
import ipaddress
import json
from pathlib import Path
import socket

from .database import crawler_info

__all__ = [
    "verify_crawler_ip",
    "reverse_dns",
    "forward_confirmed_rdns",
    "ip_in_range",
    "known_crawler_ip",
    "known_crawler_rdns",
]

_CACHE = 4096


def _parse_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    path = Path(__file__).parent / "crawler-ip-ranges.json"
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as f:
        data: dict[str, list[str]] = json.load(f)

    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidrs in data.values():
        for cidr in cidrs:
            try:
                networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass
    return networks


@lru_cache(maxsize=1)
def _all_rdns_suffixes() -> tuple[str, ...]:
    path = Path(__file__).parent / "crawlers.min.json"
    with path.open(encoding="utf-8") as f:
        entries = json.load(f)
    seen: dict[str, None] = {}
    for e in entries:
        seen.update(dict.fromkeys(e.get("rdns") or []))
    return tuple(seen)


def _parse_ip(
    ip: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    return addr


def _normalized_ip(ip: str) -> str | None:
    addr = _parse_ip(ip)
    return None if addr is None else str(addr)


@lru_cache(maxsize=_CACHE)
def reverse_dns(ip: str) -> str | None:
    normalized_ip = _normalized_ip(ip)
    if normalized_ip is None:
        return None

    try:
        host, _, _ = socket.gethostbyaddr(normalized_ip)
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


@lru_cache(maxsize=_CACHE)
def _suffix_exact(suffixes: tuple[str, ...]) -> frozenset[str]:
    return frozenset(s.lstrip(".") for s in suffixes)


def forward_confirmed_rdns(ip: str, suffixes: tuple[str, ...]) -> str | None:
    normalized_ip = _normalized_ip(ip)
    if normalized_ip is None:
        return None

    host = reverse_dns(normalized_ip)
    if not host:
        return None

    if not host.endswith(suffixes) and host not in _suffix_exact(suffixes):
        return None

    return host if normalized_ip in _forward_ips(host) else None


@lru_cache(maxsize=1)
def _build_index() -> tuple[list[int], list[int], list[int], list[int]]:
    v4: list[ipaddress.IPv4Network] = []
    v6: list[ipaddress.IPv6Network] = []
    for net in _parse_networks():
        if isinstance(net, ipaddress.IPv4Network):
            v4.append(net)
        else:
            v6.append(net)

    collapsed4 = sorted(ipaddress.collapse_addresses(v4)) if v4 else []
    collapsed6 = sorted(ipaddress.collapse_addresses(v6)) if v6 else []

    starts4 = [int(n.network_address) for n in collapsed4]
    ends4 = [int(n.broadcast_address) for n in collapsed4]
    starts6 = [int(n.network_address) for n in collapsed6]
    ends6 = [int(n.broadcast_address) for n in collapsed6]

    return (starts4, ends4, starts6, ends6)


@lru_cache(maxsize=_CACHE)
def ip_in_range(ip: str) -> bool:
    addr = _parse_ip(ip)
    if addr is None:
        return False

    starts4, ends4, starts6, ends6 = _build_index()

    if addr.version == 4:
        starts, ends = starts4, ends4
    else:
        starts, ends = starts6, ends6

    if not starts:
        return False

    n = int(addr)
    i = bisect.bisect_right(starts, n) - 1
    return i >= 0 and ends[i] >= n


def known_crawler_ip(ip: str) -> bool:
    return ip_in_range(ip)


def known_crawler_rdns(ip: str) -> bool:
    return forward_confirmed_rdns(ip, _all_rdns_suffixes()) is not None


def verify_crawler_ip(user_agent: str, ip: str) -> bool:
    info = crawler_info(user_agent)
    if not info or not info.rdns:
        return False

    normalized_ip = _normalized_ip(ip)
    if normalized_ip is None:
        return False

    return forward_confirmed_rdns(normalized_ip, info.rdns) is not None
