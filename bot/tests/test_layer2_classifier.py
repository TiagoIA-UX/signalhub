"""Testes — Camada 2: classifier."""

import json

import pytest

from src.classifier import Classification, MockClassifier, parse_classification


class TestParseClassification:
    def test_parse_json(self):
        raw = json.dumps(
            {
                "tenant": "lexrocha",
                "tema": "g1_vicio_produto",
                "score": 8,
                "urgencia": "alta",
                "razao": "Busca orientação",
                "citacao": "produto com defeito",
            }
        )
        c = parse_classification(raw)
        assert c.tenant == "lexrocha"
        assert c.score == 8
        assert c.is_actionable is True

    def test_parse_markdown_fence(self):
        raw = '```json\n{"tenant":"ignore","tema":"x","score":3,"urgencia":"baixa","razao":"","citacao":""}\n```'
        c = parse_classification(raw)
        assert c.tenant == "ignore"
        assert c.is_actionable is False


class TestMockClassifier:
    @pytest.fixture
    def clf(self):
        return MockClassifier()

    def test_lexrocha_case(self, clf: MockClassifier):
        c = clf.classify("Ajuda", "produto com defeito, vale procon?")
        assert c.tenant == "lexrocha"
        assert c.score >= 7

    def test_zairyx_case(self, clf: MockClassifier):
        c = clf.classify("Delivery", "comissão ifood alta demais")
        assert c.tenant == "zairyx"
        assert c.score >= 7

    def test_ignore_case(self, clf: MockClassifier):
        c = clf.classify("Futebol", "Palmeiras campeão")
        assert c.tenant == "ignore"
