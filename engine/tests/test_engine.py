import logging
from pathlib import Path

import pytest

from core.engine import SignalHubEngine

ROOT = Path(__file__).parent.parent


@pytest.fixture
def lex_engine():
    env = {
        "GROQ_API_KEY": "test",
        "TELEGRAM_BOT_TOKEN": "test",
        "TELEGRAM_CHAT_ID": "123",
        "MAX_ALERTAS_POR_HORA": "50",
    }
    log = logging.getLogger("test")
    return SignalHubEngine(ROOT / "tests" / "fixtures" / "keywords_lex.yaml", env, log)


@pytest.fixture
def zairyx_engine():
    env = {"MAX_ALERTAS_POR_HORA": "50"}
    log = logging.getLogger("test")
    return SignalHubEngine(ROOT / "tests" / "fixtures" / "keywords_zairyx.yaml", env, log)


def test_lex_score_produto_defeito(lex_engine):
    s, g = lex_engine.score("Produto com defeito, garantia negada")
    assert s >= 7
    assert g == "G1_produto_defeito"


def test_lex_score_procon(lex_engine):
    s, g = lex_engine.score("Vale a pena procon? Alguém já passou por isso?")
    assert s >= 7


def test_zairyx_score_ifood(zairyx_engine):
    s, g = zairyx_engine.score("Comissão ifood alta, tenho motoboy próprio")
    assert s >= 7
    assert g.startswith("Z")


def test_zairyx_ignore_irrelevant(zairyx_engine):
    s, g = zairyx_engine.score("Qual time ganhou o campeonato?")
    assert s < 7
