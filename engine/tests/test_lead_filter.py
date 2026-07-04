"""Testes do filtro de leads acionáveis."""

from core.sources.lead_filter import eh_lead_acionavel


def test_rejeita_trustpilot_marca():
    assert not eh_lead_acionavel(
        "https://www.trustpilot.com/review/meo.pt",
        "MEO Reviews | Read Customer Service Reviews",
    )


def test_aceita_reddit_post():
    assert eh_lead_acionavel(
        "https://www.reddit.com/r/portugal/comments/abc123/nao_consigo_cancelar/",
        "Eu tenho fidelização com a MEO e não consigo cancelar o contrato. Alguém já passou?",
    )


def test_rejeita_reclameaqui_empresa():
    assert not eh_lead_acionavel(
        "https://www.reclameaqui.com.br/empresa/tim/",
        "TIM — Reclamações e avaliações",
    )


def test_aceita_reddit_brasil():
    assert eh_lead_acionavel(
        "https://www.reddit.com/r/brasil/comments/abc123/cobranca_indevida/",
        "Eu tenho cobrança indevida na fatura e o banco não resolve. Alguém já passou no procon?",
    )


def test_trustpilot_com_texto_consumidor():
    texto = (
        "Eu comprei um telemóvel e a encomenda não chegou há 3 semanas. "
        "Já reclamei e não me respondem. Como posso cancelar e pedir reembolso?"
    )
    assert eh_lead_acionavel("https://www.trustpilot.com/review/meo.pt", texto)
