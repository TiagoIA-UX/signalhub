"""Camada 4 — fonte Reddit (JSON público)."""

from __future__ import annotations

import logging

import httpx

from src.retry import retry_call
from src.telegram_alert import RawPost

logger = logging.getLogger(__name__)


class RedditSource:
    BASE = "https://www.reddit.com"

    def __init__(self, subreddits: list[str], limit: int = 25) -> None:
        self.subreddits = subreddits
        self.limit = limit
        self.headers = {"User-Agent": "SignalHub/0.1 (monitor público; +https://lexrocha.com.br)"}

    def fetch_new(self) -> list[RawPost]:
        posts: list[RawPost] = []
        with httpx.Client(timeout=20.0, headers=self.headers, follow_redirects=True) as client:
            for sub in self.subreddits:
                posts.extend(self._fetch_subreddit(client, sub))
        return posts

    def _fetch_subreddit(self, client: httpx.Client, subreddit: str) -> list[RawPost]:
        url = f"{self.BASE}/r/{subreddit}/new.json?limit={self.limit}"

        def _get() -> httpx.Response:
            resp = client.get(url)
            resp.raise_for_status()
            return resp

        try:
            resp = retry_call(_get, exceptions=(httpx.HTTPError,), label=f"reddit.r/{subreddit}")
        except httpx.HTTPError as exc:
            logger.warning("Reddit r/%s indisponível após retries: %s", subreddit, exc)
            return []

        data = resp.json()
        children = data.get("data", {}).get("children", [])
        results: list[RawPost] = []

        for child in children:
            post = child.get("data", {})
            if post.get("stickied") or post.get("over_18"):
                continue
            permalink = post.get("permalink", "")
            if not permalink:
                continue
            results.append(
                RawPost(
                    url=f"{self.BASE}{permalink}",
                    title=post.get("title", ""),
                    body=post.get("selftext", "") or post.get("title", ""),
                    source="Reddit",
                    subreddit=subreddit,
                )
            )
        return results
