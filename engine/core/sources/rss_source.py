"""RSS feeds (Google Alerts, blogs, etc.)."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


class RssSource:
    def __init__(self, feed_urls: list[str]) -> None:
        self.feed_urls = [u for u in feed_urls if u and not u.startswith("#")]

    async def fetch(self) -> list[dict]:
        if not self.feed_urls:
            return []
        posts: list[dict] = []
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            for url in self.feed_urls:
                posts.extend(await self._fetch_feed(client, url))
        logger.info(f"RSS: {len(posts)} items")
        return posts

    async def _fetch_feed(self, client: httpx.AsyncClient, feed_url: str) -> list[dict]:
        try:
            r = await client.get(feed_url)
            r.raise_for_status()
            root = ET.fromstring(r.text)
        except Exception as e:
            logger.warning(f"RSS {feed_url[:50]}: {e}")
            return []

        out: list[dict] = []
        for item in root.iter("item"):
            title = _tag(item, "title")
            link = _tag(item, "link")
            desc = _tag(item, "description")
            desc = re.sub(r"<[^>]+>", "", desc)[:500]
            if link:
                out.append({
                    "autor": "rss",
                    "texto": f"{title}\n{desc}".strip(),
                    "link": link,
                    "fonte": "rss",
                    "dork_id": "google_alerts",
                })
        return out


def _tag(parent: ET.Element, name: str) -> str:
    for el in parent:
        if el.tag.endswith(name):
            return (el.text or "").strip()
    return ""
