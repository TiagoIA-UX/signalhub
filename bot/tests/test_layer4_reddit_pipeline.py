"""Testes — Camada 4: Reddit + pipeline integração."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import SignalPipeline
from src.sources.reddit import RedditSource
from src.telegram_alert import RawPost


SAMPLE_REDDIT_JSON = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "Comissão ifood alta — tenho entregador próprio",
                    "selftext": "Alguém sabe como fazer canal próprio whatsapp?",
                    "permalink": "/r/restaurantes/comments/abc123/test/",
                    "stickied": False,
                    "over_18": False,
                }
            },
            {
                "data": {
                    "title": "Sticky mod",
                    "selftext": "",
                    "permalink": "/r/restaurantes/comments/sticky/",
                    "stickied": True,
                    "over_18": False,
                }
            },
        ]
    }
}


class TestRedditSource:
    @patch("src.sources.reddit.httpx.Client")
    def test_fetch_parses_posts(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_REDDIT_JSON
        mock_resp.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        source = RedditSource(subreddits=["restaurantes"], limit=5)
        posts = source.fetch_new()
        assert len(posts) == 1
        assert posts[0].subreddit == "restaurantes"
        assert "ifood" in posts[0].title.lower()

    @patch("src.sources.reddit.httpx.Client")
    def test_fetch_handles_http_error(self, mock_client_cls):
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.HTTPError("fail")
        mock_client_cls.return_value = mock_client

        source = RedditSource(subreddits=["brasil"], limit=5)
        posts = source.fetch_new()
        assert posts == []


class TestPipelineIntegration:
    @pytest.fixture
    def pipeline(self, tmp_path: Path):
        return SignalPipeline(use_mock_ai=True, dedup_path=tmp_path / "test.sqlite")

    def test_full_flow_lexrocha(self, pipeline: SignalPipeline):
        post = RawPost(
            url="https://reddit.com/r/brasil/integration-test-001",
            title="Produto com defeito e garantia negada",
            body="Alguém já passou por isso? Vale a pena procon?",
            source="Reddit",
            subreddit="brasil",
        )
        alert = pipeline.process_post(post, send_telegram=False)
        assert alert is not None
        assert alert.classification.tenant == "lexrocha"
        assert alert.classification.score >= 7
        assert "lexrocha.com.br" in alert.cta_url

    def test_full_flow_zairyx(self, pipeline: SignalPipeline):
        post = RawPost(
            url="https://reddit.com/r/restaurantes/integration-test-002",
            title="Comissão ifood alta",
            body="Tenho motoboy próprio, quero cardápio digital whatsapp",
            source="Reddit",
            subreddit="restaurantes",
        )
        alert = pipeline.process_post(post, send_telegram=False)
        assert alert is not None
        assert alert.classification.tenant == "zairyx"

    def test_duplicate_skipped(self, pipeline: SignalPipeline):
        post = RawPost(
            url="https://reddit.com/r/brasil/dup-test",
            title="conta bloqueada procon",
            body="preciso saber meus direitos produto com defeito",
            source="Reddit",
            subreddit="brasil",
        )
        first = pipeline.process_post(post, send_telegram=False)
        second = pipeline.process_post(post, send_telegram=False)
        assert first is not None
        assert second is None

    def test_irrelevant_filtered(self, pipeline: SignalPipeline):
        post = RawPost(
            url="https://reddit.com/r/brasil/irrelevant",
            title="Gol do Neymar",
            body="Que jogada incrível ontem",
            source="Reddit",
            subreddit="brasil",
        )
        alert = pipeline.process_post(post, send_telegram=False)
        assert alert is None
