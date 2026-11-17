from __future__ import annotations

import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "169.254.169.254"}
MAX_URL_LENGTH = 2048
MAX_REDIRECTS = 5
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024


class SSRFError(ValueError):
    pass


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_url(url: str) -> str:
    if not url or len(url) > MAX_URL_LENGTH:
        raise SSRFError("invalid url length")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFError("scheme not allowed")
    if not parsed.hostname:
        raise SSRFError("missing host")
    host = parsed.hostname.lower()
    if host in BLOCKED_HOSTS:
        raise SSRFError("blocked host")
    # Resolve DNS and block private/loopback/link-local targets.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise SSRFError("dns resolution failed")
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            raise SSRFError("invalid ip")
        if _is_blocked_ip(ip):
            raise SSRFError(f"blocked ip {addr}")
    return url.strip()


def safe_join_url(base: str, path: str) -> str:
    # Not used heavily; kept for future.
    return base.rstrip("/") + "/" + path.lstrip("/")