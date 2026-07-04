"""Testes — Camada 3: responder + telegram alert."""

from unittest.mock import MagicMock, patch

import pytest

from src.classifier import Classification
from src.responder import MockResponder, build_cta_url
from src.telegram_alert import AlertPayload, RawPost, sanitize_for_groq


class TestSanitize:
    def test_removes_cpf(self):
        text = "Meu CPF 123.456.789-00 foi usado"
        assert "[CPF]" in sanitize_for_groq(text)
        assert "123.456" not in sanitize_for_groq(text)

    def test_removes_email(self):
        text = "Contato joao@email.com por favor"
        assert "[EMAIL]" in sanitize_for_groq(text)


class TestCtaUrl:
    def test_lexrocha_utm(self):
        url = build_cta_url("lexrocha", "reddit_brasil", "g7_lgpd")
        assert "lexrocha.com.br" in url
        assert "utm_source=reddit_brasil" in url
        assert "tema=g7_lgpd" in url

    def test_zairyx_utm(self):
        url = build_cta_url("zairyx", "reddit_restaurantes", "z1_comissao_ifood")
        assert "zairyx.com.br" in url


class TestMockResponder:
    def test_lexrocha_responses_have_cta(self):
        r = MockResponder().generate("lexrocha", "g9_orientacao", "texto", "https://lexrocha.com.br/x")
        assert "https://lexrocha.com.br/x" in r.r1
        assert len(r.r3) <= 400

    def test_zairyx_mentions_gmb(self):
        r = MockResponder().generate("zairyx", "z4_google_meu_negocio", "texto", "https://zairyx.com.br/x")
        assert "GMB" in r.r2 or "Google" in r.r2


class TestAlertFormat:
    def test_message_structure(self):
        post = RawPost(
            url="https://reddit.com/r/brasil/x",
            title="Conta bloqueada",
            body="Preciso saber meus direitos",
            source="Reddit",
            subreddit="brasil",
        )
        clf = Classification(
            tenant="lexrocha",
            tema="g6_contratos_digitais",
            score=9,
            urgencia="alta",
            razao="teste",
            citacao="Preciso saber meus direitos",
        )
        from src.responder import Responses

        alert = AlertPayload(
            post=post,
            classification=clf,
            responses=Responses(r1="R1", r2="R2", r3="R3"),
            cta_url="https://lexrocha.com.br",
        )
        msg = alert.format_message()
        assert "OPORTUNIDADE 9/10" in msg
        assert "LEXROCHA" in msg
        assert "RESPOSTA 1" in msg
        assert len(msg) <= 4096

    def test_inline_keyboard(self):
        post = RawPost(url="https://reddit.com/x", title="t", body="b", source="Reddit")
        clf = Classification("lexrocha", "g1", 8, "media", "r", "c")
        from src.responder import Responses

        alert = AlertPayload(post, clf, Responses("a", "b", "c"), "https://x.com")
        kb = alert.inline_keyboard()
        assert len(kb) == 2
        assert kb[0][0]["text"] == "✅ R1"
        uid = alert.callback_id()
        assert len(uid) == 16
        assert kb[0][0]["callback_data"] == f"approve:r1:{uid}"


class TestTelegramSend:
    @patch("src.telegram_bot.httpx.Client")
    def test_send_alert_includes_inline_keyboard(self, mock_client_cls):
        from src.telegram_bot import TelegramNotifier

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        post = RawPost(url="https://reddit.com/x", title="t", body="b", source="Reddit")
        clf = Classification("lexrocha", "g1", 8, "media", "r", "c")
        from src.responder import Responses

        alert = AlertPayload(post, clf, Responses("a", "b", "c"), "https://x.com")
        ok = TelegramNotifier("token", "123").send_alert(alert)
        assert ok is True
        payload = mock_client.post.call_args.kwargs["json"]
        assert "reply_markup" in payload
        assert payload["reply_markup"]["inline_keyboard"][0][0]["text"] == "✅ R1"
