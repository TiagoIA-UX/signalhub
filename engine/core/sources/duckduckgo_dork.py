"""Executa Google Dorks via DuckDuckGo (sem API paga)."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from core.sources.link_resolver import normalizar_link_origem

logger = logging.getLogger(__name__)


def _load_ddgs():
    try:
        from ddgs import DDGS

        return DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS

            logger.warning("Pacote legado duckduckgo_search — migre: pip install ddgs")
            return DDGS
        except ImportError:
            logger.error("Instale: pip install ddgs")
            return None


def _search_sync(query: str, max_results: int) -> list[dict[str, str]]:
    DDGS = _load_ddgs()
    if DDGS is None:
        return []

    proxy = os.environ.get("DDGS_PROXY", "").strip() or None
    posts: list[dict[str, str]] = []
    try:
        with DDGS(proxy=proxy) as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                href = r.get("href") or r.get("link") or ""
                body = r.get("body") or r.get("snippet") or ""
                title = r.get("title") or ""
                if not href:
                    continue
                href = normalizar_link_origem(href)
                if not href:
                    continue
                posts.append({
                    "autor": "web",
                    "texto": f"{title}\n{body}".strip(),
                    "link": href,
                    "fonte": "varredura:web",
                })
    except Exception as e:
        logger.warning(f"Varredura web falhou: {e}")
    return posts


async def run_dorks(
    dorks: list[dict[str, Any]],
    max_per_dork: int = 8,
    delay_sec: float = 3.0,
) -> list[dict]:
    all_posts: list[dict] = []
    seen: set[str] = set()

    for i, dork in enumerate(dorks):
        q = dork.get("query", "")
        if not q:
            continue
        logger.info(f"Varredura [{i+1}/{len(dorks)}]: consulta activa...")
        batch = await asyncio.to_thread(_search_sync, q, max_per_dork)
        for p in batch:
            if p["link"] not in seen:
                seen.add(p["link"])
                p["dork_id"] = dork.get("id", f"dork_{i}")
                if dork.get("canal"):
                    p["canal"] = dork["canal"]
                if dork.get("grupo"):
                    p["grupo_hint"] = dork["grupo"]
                all_posts.append(p)
        if i < len(dorks) - 1:
            await asyncio.sleep(delay_sec)

    logger.info(f"Varredura web: {len(all_posts)} resultados unicos")
    return all_posts
