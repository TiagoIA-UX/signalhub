"""Testes do tenant Portugal (Direitos do Consumidor)."""

import logging
from pathlib import Path

import pytest
import yaml

from core.engine import (
    SignalHubEngine,
    formatar_linha_origem,
    humanizar_resposta_pt,
    nome_plataforma_origem,
    remover_indicacoes_terceiros,
)

ROOT = Path(__file__).parent.parent
MONOREPO = ROOT.parent
CFG_LEGACY = ROOT / "config" / "portugal"
CFG_PROJECT = MONOREPO / "lex-rocha-pt" / "signalhub-pt" / "config"
CFG_PROJECT_LEGACY = MONOREPO / "lex-rocha-pt" / "config"
FIXTURE = ROOT / "tests" / "fixtures" / "keywords_portugal.yaml"


def _pt_config(name: str) -> Path:
    alt = name.replace("varredura", "dorks") if "varredura" in name else name
    for base in (CFG_PROJECT, CFG_PROJECT_LEGACY, CFG_LEGACY):
        for n in (name, alt):
            p = base / n
            if p.exists():
                return p
    return CFG_PROJECT / name


@pytest.fixture
def pt_engine():
    env = {"GROQ_API_KEY": "x", "MAX_ALERTAS_POR_HORA": "50", "GROQ_REVISAO": "1"}
    kw = _pt_config("keywords.yaml")
    if not kw.exists():
        kw = FIXTURE
    log = logging.getLogger("test")
    engine = SignalHubEngine(kw, env, log)
    if not _pt_config("prompts.yaml").exists():
        engine._prompts = yaml.safe_load(
            (ROOT / "tests" / "fixtures" / "prompts.yaml").read_text(encoding="utf-8")
        )
    return engine


def test_pt_score_telecom(pt_engine):
    s, g = pt_engine.score("MEO fidelização cancelar contrato")
    assert s >= 7
    assert g == "pt_telecom"


def test_pt_contexto_comercial(pt_engine):
    ctx = pt_engine._contexto_comercial("pt_telecom")
    assert "15 dias úteis" in ctx
    assert "ANACOM" in ctx
    assert "€39" in ctx or "padrao" in ctx.lower()
    assert "pt_telecom" in ctx


def test_pt_regras_setor_telecom(pt_engine):
    s = pt_engine._regras_setor("pt_telecom")
    assert s["prazo"] == "15 dias úteis"
    assert s["regulatorio"] == "ANACOM"
    assert "LCE" in s["nota_setor"] or "ANACOM" in s["nota_setor"]


def test_pt_fallback_roteiro(pt_engine):
    r1, r2, r3 = pt_engine._fallback_respostas("pt_telecom")
    texto = " ".join([r1, r2, r3]).lower()
    assert r1.lower().startswith("olá")
    assert "15 dias" in r2
    assert "anacom" not in texto
    assert "advogad" not in texto
    assert "consulta" not in texto
    assert "24/96" not in texto
    assert "http" not in texto
    assert "www." not in texto
    assert "dgsi" not in texto
    assert "connosco" in r1 or "percebemos" in r1
    assert "relatório" in r3.lower()


def test_remover_indicacoes_terceiros():
    bruto = (
        "Após 15 dias úteis, contacte a ANACOM. "
        "Uma consulta presencial pode rondar os €48. "
        "Pode avaliar com o advogado que escolher."
    )
    limpo = remover_indicacoes_terceiros(bruto)
    assert "anacom" not in limpo.lower()
    assert "advogad" not in limpo.lower()
    assert "consulta" not in limpo.lower()


def test_humanizar_remove_links_e_leis():
    bruto = (
        "Pela Lei n.º 24/96 e DL 156/2005 veja https://dgsi.pt/x "
        "ou www.direitosconsumidor.com — 15 dias úteis."
    )
    limpo = humanizar_resposta_pt(bruto)
    assert "http" not in limpo
    assert "www." not in limpo
    assert "24/96" not in limpo
    assert "156/2005" not in limpo
    assert "15 dias" in limpo


def test_pt_revisao_habilitada(pt_engine):
    assert pt_engine._usar_revisao_groq() is True


def test_pt_detecta_voce(pt_engine):
    hits = pt_engine._detectar_pt_br(["Olá", "Você tem direito", "ok"])
    assert hits


def test_pt_prompt_template_placeholders(pt_engine):
    prompts_path = _pt_config("prompts.yaml")
    if not prompts_path.exists():
        prompts = pt_engine._prompts
    else:
        prompts = yaml.safe_load(prompts_path.read_text(encoding="utf-8"))
    tpl = prompts["groq_system_template"]
    for key in ("nicho_nome", "grupo_nome", "contexto_comercial", "preco_sugerido"):
        assert "{" + key + "}" in tpl
    assert "sem urls" in tpl.lower() or "sem URLs" in tpl
    assert "terceiros" in tpl.lower() or "advogados" in tpl.lower()
    assert "groq_revisao_template" in prompts
    assert "{r1}" in prompts["groq_revisao_template"]


def test_pt_keywords_domain_and_cnpj():
    kw_path = _pt_config("keywords.yaml")
    if not kw_path.exists():
        pytest.skip("keywords.yaml local ausente")
    cfg = yaml.safe_load(kw_path.read_text(encoding="utf-8"))
    nicho = cfg["nichos"]["lex_portugal"]
    assert "direitosconsumidor.com" in nicho["cta_link"]
    assert nicho["empresa"]["cnpj"] == "61.699.939/0001-80"
    assert "Tecnologia" not in str(nicho)
    assert "pesquisa jurídica" in nicho["empresa"]["atuacao"].lower()


def test_pt_varredura_example_valid():
    path = _pt_config("varredura.yaml.example")
    if not path.exists():
        path = _pt_config("dorks.yaml.example")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert cfg["meta"]["tenant"] == "lex_portugal"
    assert cfg["meta"].get("versao") == "2.1"
    assert cfg["meta"].get("portal_queixa") == "desactivado_ate_nipc"
    assert len(cfg["dorks"]) >= 45
    canais = {d["canal"] for d in cfg["dorks"] if d.get("canal")}
    assert "portal_queixa" not in canais
    assert len(canais) >= 9
    assert "portugal" in cfg["reddit"]["subreddits"]


def test_pt_nome_plataforma_por_canal():
    tenant = "lex_portugal"
    assert nome_plataforma_origem(
        link="https://reddit.com/r/portugal/x",
        canal="reddit_portugal",
        tenant=tenant,
    ) == "Reddit — r/portugal"
    assert nome_plataforma_origem(
        link="https://portaldaqueixa.com/empresas/ctt/x",
        canal="portal_queixa",
        tenant=tenant,
    ) == "Portal da Queixa"
    assert nome_plataforma_origem(
        link="https://reddit.com/r/portugal/x",
        fonte="reddit:r/portugal",
        tenant=tenant,
    ) == "Reddit — r/portugal"


def test_pt_nao_rotula_reclame_aqui():
    """Reclame Aqui é plataforma BR — não deve aparecer no tenant Portugal."""
    nome = nome_plataforma_origem(
        link="https://reclameaqui.com.br/empresa/x",
        canal="reclame_aqui",
        tenant="lex_portugal",
    )
    assert nome != "Reclame Aqui"
    assert "reclameaqui" in nome.lower()


def test_br_reclame_aqui():
    assert nome_plataforma_origem(
        link="https://reclameaqui.com.br/empresa/x",
        canal="reclame_aqui",
        tenant="lex_rocha",
    ) == "Reclame Aqui"


def test_pt_linha_origem_com_link():
    linha = formatar_linha_origem(
        link="https://portaldaqueixa.com/mock-002",
        canal="portal_queixa",
        tenant="lex_portugal",
    )
    assert "Portal da Queixa" in linha
    assert 'href="https://portaldaqueixa.com/mock-002"' in linha
    assert "<code>https://portaldaqueixa.com/mock-002</code>" in linha
    assert "dork" not in linha.lower()


def test_pt_score_cancelamento(pt_engine):
    s, g = pt_engine.score("como cancelar contrato fidelização MEO")
    assert s >= 7
    assert g in ("pt_cancelamento", "pt_telecom")
