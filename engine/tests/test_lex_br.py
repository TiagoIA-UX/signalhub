"""Camada Lex/BR — valida a config de PRODUÇÃO que o hub canônico carrega.

O bot real (Lex-Rocha/signalhub-br/hub.py) lê esta config, não os fixtures.
Garantimos que ela carrega, aponta para o domínio do Lex Rocha e pontua
corretamente posts típicos de direito do consumidor (CDC).
"""
import logging
from pathlib import Path

import pytest
import yaml

from core.engine import SignalHubEngine

ROOT = Path(__file__).parent.parent
CONFIG_BR = ROOT.parent / "Lex-Rocha" / "signalhub-br" / "config" / "keywords.yaml"

_skip = pytest.mark.skipif(not CONFIG_BR.exists(), reason="config BR canônica ausente")


def _engine() -> SignalHubEngine:
    env = {
        "GROQ_API_KEY": "test",
        "TELEGRAM_BOT_TOKEN": "test",
        "TELEGRAM_CHAT_ID": "123",
        "MAX_ALERTAS_POR_HORA": "50",
    }
    return SignalHubEngine(CONFIG_BR, env, logging.getLogger("test-br"))


@_skip
def test_br_config_carrega_e_cta_lexrocha():
    cfg = yaml.safe_load(CONFIG_BR.read_text(encoding="utf-8"))
    nicho = cfg["nichos"]["lex_rocha"]
    assert "lexrocha.com.br" in nicho["cta_link"]
    assert nicho.get("score_minimo", 0) >= 7
    assert nicho["grupos"], "deve haver grupos de keywords"


@_skip
def test_br_score_cobranca_indevida():
    eng = _engine()
    s, g = eng.score("Tive uma cobrança indevida, me cobraram duas vezes no cartão")
    assert s >= eng.score_min
    assert g == "G3_cobranca_indevida"


@_skip
def test_br_score_plano_saude_alto():
    eng = _engine()
    s, g = eng.score("Plano de saúde negou cirurgia — negativa de cobertura")
    assert s >= 9
    assert g == "G5_saude_plano"


@_skip
def test_br_ignora_irrelevante():
    eng = _engine()
    s, _ = eng.score("Qual o melhor time de futebol do brasil?")
    assert s < eng.score_min
