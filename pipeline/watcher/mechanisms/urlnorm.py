"""URL canonicalization for listing-page mechanisms (html_diff today,
sitemap_diff later) whose only identity signal is a URL they discovered
themselves, rather than a guid the source declares.

Two different hrefs that resolve to the same resource must canonicalize to
the same string, or the ledger's URL-as-guid identity (see
pipeline/watcher/hashing.py's identity_key_for_item -- guid wins over the
link+title fallback whenever guid is set) would spawn a duplicate ledger
entry every time a listing page linked the same item with a differently
-cased host or a trailing default port.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}


def canonicalize(href: str, base_url: str) -> str:
    """Resolve href against base_url (handles a relative href exactly as a
    browser would; an already-absolute href passes through urljoin
    unchanged), then normalize: lowercase scheme and host, strip an
    explicit port that matches the scheme's default, strip any fragment.
    Path and query are preserved verbatim (untouched, not even
    percent-normalized) -- both can be case-sensitive on the origin
    server, so touching them would risk canonicalizing two genuinely
    different resources onto the same identity.
    """
    absolute = urljoin(base_url, href)
    parts = urlsplit(absolute)

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    port = parts.port
    if port is not None and _DEFAULT_PORTS.get(scheme) == port:
        port = None

    netloc = hostname
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo = f"{userinfo}:{parts.password}"
        netloc = f"{userinfo}@{netloc}"
    if port is not None:
        netloc = f"{netloc}:{port}"

    return urlunsplit((scheme, netloc, parts.path, parts.query, ""))
