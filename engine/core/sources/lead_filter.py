"""Filtra resultados do dorking — só leads onde se pode contactar uma pessoa."""

from __future__ import annotations

import re

# Páginas agregadas (empresa/marca) — não são posts de consumidores
_AGGREGADO_TRUSTPILOT = re.compile(
    r"trustpilot\.com/review/[\w.-]+/?(?:\?page=\d+)?$",
    re.I,
)
_HOMEPAGE_TRUSTPILOT = re.compile(r"trustpilot\.com/?$", re.I)
_AGGREGADO_RECLAME = re.compile(
    r"reclameaqui\.com\.br/empresa/[\w-]+/?(?:lista-reclamacoes)?/?$",
    re.I,
)

# URLs típicas de publicação individual (respondível)
_POST_PATTERNS = (
    re.compile(r"reddit\.com/r/\w+/comments/", re.I),
    re.compile(r"portaldaqueixa\.com/", re.I),
    re.compile(r"forum\.(zwame|hardware|cfdistribuidos)\.", re.I),
    re.compile(r"deco\.proteste\.pt/", re.I),
    re.compile(r"facebook\.com/.+/posts/", re.I),
    re.compile(r"trustpilot\.com/reviews/[a-f0-9]{24}", re.I),
    re.compile(r"reclameaqui\.com\.br/.*/reclamacao/", re.I),
    re.compile(r"consumidor\.gov\.br/", re.I),
    re.compile(r"jusbrasil\.com\.br/", re.I),
)


def _texto_parece_pedido_consumidor(texto: str) -> bool:
    t = (texto or "").strip()
    if len(t) < 80:
        return False
    return bool(
        re.search(
            r"\b(eu|minha|meu|minhas|reclama|cancelar|devolu|reembolso|"
            r"encomenda|fatura|burla|ajuda|como\s+posso|vale\s+a\s+pena|"
            r"procon|cobran|defeito|indeniza)\b",
            t,
            re.I,
        )
    )


def eh_lead_acionavel(link: str, texto: str = "") -> bool:
    """
    True se o URL parece uma publicação onde um consumidor pede ajuda
    (não página institucional nem ficha agregada de marca).
    """
    if not link:
        return False
    lower = link.lower().rstrip("/")

    if _HOMEPAGE_TRUSTPILOT.search(lower):
        return False

    if _AGGREGADO_TRUSTPILOT.search(lower):
        return _texto_parece_pedido_consumidor(texto)

    if _AGGREGADO_RECLAME.search(lower):
        return _texto_parece_pedido_consumidor(texto)

    for pat in _POST_PATTERNS:
        if pat.search(lower):
            return True

    # DDG genérico: exige texto com sinais de pedido real
    return _texto_parece_pedido_consumidor(texto)
