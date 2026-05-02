import socket


def fcrdns_verify(ip: str, allowed_suffixes: tuple[str, ...]) -> bool:
    try:
        hostname = socket.gethostbyaddr(ip)[0].lower()
    except (socket.herror, socket.gaierror):
        return False

    if not any(
        hostname == suffix or hostname.endswith("." + suffix)
        for suffix in allowed_suffixes
    ):
        return False

    try:
        forward_ips = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return False

    return ip in forward_ips


GOOGLEBOT_SUFFIXES = ("googlebot.com", "google.com")
BINGBOT_SUFFIXES = ("search.msn.com",)
APPLEBOT_SUFFIXES = ("applebot.apple.com",)
