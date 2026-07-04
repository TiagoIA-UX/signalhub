"""Reddit — complemento aos dorks (subreddits diretos)."""

from __future__ import annotations

import logging

import httpx

from core.sources.link_resolver import normalizar_link_origem

logger = logging.getLogger(__name__)


class RedditSource:
    BASE = "https://www.reddit.com"
    HEADERS = {"User-Agent": "SignalHub/2.0 (public monitor)"}

    def __init__(self, subreddits: list[str], limit: int = 15) -> None:
        self.subreddits = subreddits
        self.limit = limit

    async def fetch(self) -> list[dict]:
        posts: list[dict] = []
        async with httpx.AsyncClient(
            timeout=25.0, headers=self.HEADERS, follow_redirects=True
        ) as client:
            for sub in self.subreddits:
                posts.extend(await self._fetch_sub(client, sub))
        logger.info(f"Reddit: {len(posts)} posts")
        return posts

    async def _fetch_sub(self, client: httpx.AsyncClient, subreddit: str) -> list[dict]:
        url = f"{self.BASE}/r/{subreddit}/new.json?limit={self.limit}"
        try:
            resp = await client.get(url)
            if resp.status_code == 403:
                logger.warning(f"Reddit 403 r/{subreddit} — use dorks site:reddit.com")
                return []
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"Reddit r/{subreddit}: {e}")
            return []

        out: list[dict] = []
        for child in resp.json().get("data", {}).get("children", []):
            p = child.get("data", {})
            if p.get("stickied") or p.get("over_18"):
                continue
            permalink = p.get("permalink", "")
            if not permalink:
                continue
            title = (p.get("title") or "").strip()
            body = (p.get("selftext") or "").strip()
            link = normalizar_link_origem(f"{self.BASE}{permalink}")
            out.append({
                "autor": f"u/{p.get('author', 'anon')}",
                "texto": f"{title}\n{body}".strip(),
                "link": link,
                "fonte": f"reddit:r/{subreddit}",
                "dork_id": "reddit_direct",
            })
        return out
