"""Compat: RedditFetcher → RedditSource (use DorkScanner em produção)."""

from core.sources.reddit_source import RedditSource as RedditFetcher

__all__ = ["RedditFetcher"]
