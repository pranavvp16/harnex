"""Shared SSRF (Server-Side Request Forgery) protection utilities.

Used by both the connection test wizard and the spec fetcher to validate
that user-supplied URLs resolve to public IP addresses and not internal
services, cloud metadata endpoints, or other private resources.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse


def is_blocked_destination_ip(ip: str) -> bool:
    """Return True when the IP must not be reached (SSRF guard).

    Blocks private, loopback, link-local, multicast, reserved, and
    unspecified addresses.
    """
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


def bracket_ip(ip: str) -> str:
    """Format IP for URL netloc (IPv6 must be bracketed)."""
    try:
        if ipaddress.ip_address(ip).version == 6:
            return f"[{ip}]"
    except ValueError:
        pass
    return ip


def stable_public_ips_sync(hostname: str) -> tuple[list[str] | None, str | None]:
    """Resolve twice on the same thread; reject flaky DNS (mitigates rebinding races).

    Returns ``(ips, None)`` on success, or ``(None, error_message)``.
    """

    def lookup_once() -> list[str]:
        try:
            infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        except socket.gaierror:
            return []
        out: list[str] = []
        seen: set[str] = set()
        for info in infos:
            ip_s = str(info[4][0])
            if ip_s not in seen:
                seen.add(ip_s)
                out.append(ip_s)
        return out

    a = lookup_once()
    b = lookup_once()
    if not a:
        return None, "could not resolve hostname"
    if sorted(a) != sorted(b):
        return None, "dns resolution changed between checks — refusing to connect"
    pub = [ip for ip in a if not is_blocked_destination_ip(ip)]
    if not pub:
        return None, "hostname resolves to a non-public IP address"
    return pub, None


async def guard_public_http_url(url: str) -> tuple[bool, str, list[str] | None]:
    """Validate origin is HTTP(S) with a public destination.

    For hostname origins, returns the ordered list of resolved public IPs
    (two identical lookups) so plain-HTTP probes can connect by IP with a
    Host header, avoiding a separate DNS lookup inside httpx (DNS rebinding).
    HTTPS probes still use the hostname URL (certificate validation);
    redirects are disabled to avoid bypassing this check.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "only http and https URLs can be tested", None
    host = parsed.hostname
    if not host:
        return False, "missing host in URL", None

    try:
        literal = ipaddress.ip_address(host)
        if is_blocked_destination_ip(str(literal)):
            return False, "target uses a non-public IP address", None
        return True, "", None
    except ValueError:
        pass

    ips, err = await asyncio.to_thread(stable_public_ips_sync, hostname=host)
    if err:
        return False, err, None
    return True, "", ips


__all__ = [
    "bracket_ip",
    "guard_public_http_url",
    "is_blocked_destination_ip",
    "stable_public_ips_sync",
]