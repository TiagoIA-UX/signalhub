"""Normaliza URLs vindas do dorking para o link real da publicação."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

_DDG_HOSTS = ("duckduckgo.com", "duck.com", "html.duckduckgo.com")


def desembrulhar_redirect_busca(url: str) -> str:
    """Extrai destino real de redirects DuckDuckGo / Google / Bing."""
    if not url:
        return url
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if any(h in host for h in _DDG_HOSTS) and "/l/" in parsed.path:
            qs = parse_qs(parsed.query)
            if uddg := qs.get("uddg", [None])[0]:
                return unquote(uddg)
        if "google." in host and parsed.path == "/url":
            qs = parse_qs(parsed.query)
            if dest := qs.get("q", [None])[0]:
                return unquote(dest)
        if "bing.com" in host and parsed.path == "/ck/a":
            qs = parse_qs(parsed.query)
            if dest := qs.get("u", [None])[0]:
                return unquote(dest)
    except Exception:
        pass
    return url


def normalizar_reddit(url: str) -> str:
    """Garante permalink estável do Reddit (www + /comments/)."""
    if not url or "reddit.com" not in url.lower():
        return url
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host in ("reddit.com", "old.reddit.com", "np.reddit.com"):
        netloc = "www.reddit.com"
    else:
        netloc = parsed.netloc
    path = parsed.path.rstrip("/")
    # /r/sub/comments/id/title → manter; /r/sub/comments/id → ok
    return urlunparse((parsed.scheme or "https", netloc, path, "", "", ""))


def normalizar_link_origem(url: str) -> str:
    """Link final para abrir a publicação e contactar a pessoa certa."""
    u = (url or "").strip()
    if not u:
        return u
    u = desembrulhar_redirect_busca(u)
    u = normalizar_reddit(u)
    return u


def link_parece_valido(url: str) -> bool:
    """Rejeita placeholders de mock e URLs vazias."""
    if not url or not url.startswith(("http://", "https://")):
        return False
    lower = url.lower()
    if re.search(r"/mock[-_]|mock-\d|/mock$|/teste-", lower):
        return False
    if "example.com" in lower or "localhost" in lower:
        return False
    return True
