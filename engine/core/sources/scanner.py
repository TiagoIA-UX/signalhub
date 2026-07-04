"""
DorkScanner — varredura geral multi-fonte.
Executa todos os dorks do YAML + Reddit + HN + RSS.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from core.sources.duckduckgo_dork import run_dorks
from core.sources.hackernews import HackerNewsSource
from core.sources.reddit_source import RedditSource
from core.sources.rss_source import RssSource

logger = logging.getLogger(__name__)


class DorkScanner:
    def __init__(self, dorks_config_path: Path) -> None:
        self.cfg = yaml.safe_load(dorks_config_path.read_text(encoding="utf-8"))
        self.meta = self.cfg.get("meta", {})
        self.fontes = self.cfg.get("fontes", ["duckduckgo", "reddit"])

    async def scan(self, *, offset: int = 0, limite: int | None = None) -> list[dict]:
        """Varredura completa — todas as fontes configuradas."""
        all_posts: list[dict] = []
        seen: set[str] = set()

        def merge(batch: list[dict]) -> None:
            for p in batch:
                link = p.get("link", "")
                if link and link not in seen:
                    seen.add(link)
                    all_posts.append(p)

        max_per = int(self.meta.get("max_results_por_dork", 8))
        delay = float(self.meta.get("delay_segundos_entre_dorks", 3))
        dorks: list[dict[str, Any]] = list(self.cfg.get("dorks", []))
        if offset or limite is not None:
            fim = offset + limite if limite is not None else None
            dorks = dorks[offset:fim]
            logger.info(
                f"Lote varredura: {len(dorks)} consultas (offset={offset}"
                + (f", limite={limite}" if limite is not None else "")
                + ")"
            )

        if "duckduckgo" in self.fontes and dorks:
            logger.info(f"Varredura web: {len(dorks)} consultas...")
            merge(await run_dorks(dorks, max_per, delay))

        if "reddit" in self.fontes:
            rc = self.cfg.get("reddit", {})
            subs = rc.get("subreddits", ["brasil"])
            limit = int(rc.get("limit", 15))
            merge(await RedditSource(subs, limit).fetch())

        if "hackernews" in self.fontes:
            hn = self.cfg.get("hackernews", {})
            queries = hn.get("queries", [])
            if queries:
                merge(await HackerNewsSource(queries).fetch())

        if "rss" in self.fontes:
            feeds = self.cfg.get("rss", {}).get("feeds", [])
            merge(await RssSource(feeds).fetch())

        logger.info(f"Varredura total: {len(all_posts)} oportunidades unicas")
        return all_posts
