"""Testes de normalização de links do dorking."""

from core.sources.link_resolver import (
    desembrulhar_redirect_busca,
    link_parece_valido,
    normalizar_link_origem,
    normalizar_reddit,
)


def test_desembrulhar_duckduckgo():
    dest = "https://www.reddit.com/r/portugal/comments/abc/title"
    wrapped = (
        "https://duckduckgo.com/l/?uddg="
        "https%3A%2F%2Fwww.reddit.com%2Fr%2Fportugal%2Fcomments%2Fabc%2Ftitle"
    )
    assert desembrulhar_redirect_busca(wrapped) == dest


def test_normalizar_reddit():
    assert normalizar_reddit(
        "https://reddit.com/r/portugal/comments/xyz/post/"
    ) == "https://www.reddit.com/r/portugal/comments/xyz/post"


def test_rejeita_mock():
    assert link_parece_valido("https://reddit.com/r/portugal/mock-pt-001") is False
    assert link_parece_valido(
        "https://www.reddit.com/r/portugal/comments/abc123/title"
    ) is True


def test_normalizar_link_origem_pipeline():
    url = normalizar_link_origem(
        "https://duckduckgo.com/l/?uddg="
        "https%3A%2F%2Freddit.com%2Fr%2Fportugal%2Fcomments%2F1%2Fx"
    )
    assert "www.reddit.com" in url
    assert "/comments/" in url
