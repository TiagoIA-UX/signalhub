"""Hacker News — busca via Algolia API (gratis)."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class HackerNewsSource:
    API = "https://hn.algolia.com/api/v1/search"

    def __init__(self, queries: list[str], hits_per_page: int = 10) -> None:
        self.queries = queries
        self.hits_per_page = hits_per_page

    async def fetch(self) -> list[dict]:
        posts: list[dict] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for q in self.queries:
                posts.extend(await self._search(client, q))
        logger.info(f"HackerNews: {len(posts)} posts")
        return posts

    async def _search(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        try:
            r = await client.get(
                self.API,
                params={
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": self.hits_per_page,
                },
            )
            r.raise_for_status()
        except httpx.HTTPError:
            return []

        out: list[dict] = []
        for hit in r.json().get("hits", []):
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            title = hit.get("title") or ""
            out.append({
                "autor": hit.get("author", "hn"),
                "texto": title,
                "link": url,
                "fonte": "hackernews",
                "dork_id": f"hn:{query[:30]}",
            })
        return out
