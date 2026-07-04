"""Testes — Camada 1: deduper + prefilter + config."""

from pathlib import Path

import pytest

from src.config_loader import CONFIG_DIR, load_yaml
from src.deduper import Deduper
from src.prefilter import KeywordPrefilter


class TestConfig:
    def test_tenants_yaml_loads(self):
        data = load_yaml(CONFIG_DIR / "tenants.yaml")
        assert "lexrocha" in data
        assert "zairyx" in data
        assert data["lexrocha"]["base_url"].startswith("https://")

    def test_lexrocha_keywords_have_10_groups(self):
        data = load_yaml(CONFIG_DIR / "keywords_lexrocha.yaml")
        assert len(data["groups"]) == 10

    def test_zairyx_keywords_have_6_groups(self):
        data = load_yaml(CONFIG_DIR / "keywords_zairyx.yaml")
        assert len(data["groups"]) == 6


class TestDeduper:
    @pytest.fixture
    def deduper(self, tmp_path: Path):
        return Deduper(tmp_path / "test.sqlite")

    def test_url_not_seen_initially(self, deduper: Deduper):
        assert deduper.is_seen("https://reddit.com/r/brasil/abc") is False

    def test_mark_seen_prevents_duplicate(self, deduper: Deduper):
        url = "https://reddit.com/r/brasil/post-123"
        deduper.mark_seen(url)
        assert deduper.is_seen(url) is True
        assert deduper.is_seen(url.upper()) is True

    def test_hash_url_deterministic(self, deduper: Deduper):
        h1 = deduper.hash_url("https://example.com/a")
        h2 = deduper.hash_url("https://example.com/a")
        assert h1 == h2

    def test_daily_alert_limit(self, deduper: Deduper):
        assert deduper.can_send_alert(30) is True
        deduper.increment_daily_alerts()
        assert deduper.alerts_today() == 1

    def test_log_alert(self, deduper: Deduper):
        deduper.log_alert(
            url="https://reddit.com/x",
            tenant="lexrocha",
            tema="g1_vicio_produto",
            score=8,
        )
        assert deduper.alerts_today() >= 0


class TestPrefilter:
    @pytest.fixture
    def prefilter(self):
        return KeywordPrefilter()

    def test_lexrocha_conta_bloqueada(self, prefilter: KeywordPrefilter):
        text = "Minha conta bloqueada no app e não consigo reativar, o que fazer?"
        matches = prefilter.match(text)
        assert any(m.tenant == "lexrocha" for m in matches)
        assert any(m.tema == "g6_contratos_digitais" for m in matches)

    def test_lexrocha_produto_defeito(self, prefilter: KeywordPrefilter):
        text = "Comprei celular e veio quebrado, garantia negada"
        matches = prefilter.match(text)
        assert any(m.tema == "g1_vicio_produto" for m in matches)

    def test_zairyx_comissao_ifood(self, prefilter: KeywordPrefilter):
        text = "A comissão ifood alta está comendo minha margem, tenho motoboy próprio"
        matches = prefilter.match(text)
        tenants = {m.tenant for m in matches}
        assert "zairyx" in tenants

    def test_zairyx_google_meu_negocio(self, prefilter: KeywordPrefilter):
        text = "Alguém sabe cadastrar google meu negócio para delivery?"
        matches = prefilter.match(text)
        assert any(m.tema == "z4_google_meu_negocio" for m in matches)

    def test_no_match_politics(self, prefilter: KeywordPrefilter):
        text = "Eleições 2026 e reforma tributária no congresso"
        assert prefilter.has_match(text) is False

    def test_orientacao_consumidor(self, prefilter: KeywordPrefilter):
        text = "Alguém já passou por isso? Vale a pena procon ou juizado especial?"
        matches = prefilter.match(text)
        assert any(m.tema == "g9_orientacao_consumidor" for m in matches)
