#!/usr/bin/env python3
"""Gera config/portugal/dorks.yaml a partir do mapa v2 (11 canais activos, ~48 dorks).

Portal da Queixa (portal_queixa) fica FORA até haver NIPC — monitorar sem resposta lá é ruído.
Para reactivar: descomente o bloco PORTAL_DA_QUEIXA em DORKS_SPEC.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "config" / "portugal" / "dorks.yaml"
EXAMPLE = ROOT / "config" / "portugal" / "dorks.yaml.example"

# (canal, grupo_keywords, query) — queries são modelos; refine localmente (CONFIDENCIAL.md)
#
# --- PORTAL_DA_QUEIXA (desactivado até NIPC) — descomente quando a marca estiver verificada ---
# ("portal_queixa", "pt_telecom", 'site:portaldaqueixa.com MEO OR NOS OR Vodafone cancelar fidelização'),
# ("portal_queixa", "pt_telecom", 'site:portaldaqueixa.com aumento preço telecomunicações'),
# ... (+ 10 dorks portaldaqueixa.com no histórico v2)
#
DORKS_SPEC: list[tuple[str, str, str]] = [
    # Reddit r/portugal (7) — também via subreddit directo
    ("reddit_portugal", "pt_burla", 'site:reddit.com/r/portugal burla golpe'),
    ("reddit_portugal", "pt_cancelamento", 'site:reddit.com/r/portugal cancelar contrato fidelização'),
    ("reddit_portugal", "pt_telecom", 'site:reddit.com/r/portugal MEO NOS Vodafone'),
    ("reddit_portugal", "pt_logistica", 'site:reddit.com/r/portugal CTT encomenda'),
    ("reddit_portugal", "pt_banco", 'site:reddit.com/r/portugal banco reclamação'),
    ("reddit_portugal", "pt_ecommerce", 'site:reddit.com/r/portugal reembolso compra online'),
    ("reddit_portugal", "pt_cancelamento", 'site:reddit.com/r/portugal direitos consumidor'),
    # Reddit financaspessoaispt (3)
    ("reddit_financas", "pt_banco", 'site:reddit.com/r/financaspessoaispt banco comissão'),
    ("reddit_financas", "pt_banco", 'site:reddit.com/r/financaspessoaispt crédito habitação'),
    ("reddit_financas", "pt_saude_seguro", 'site:reddit.com/r/financaspessoaispt seguro'),
    # DECO Proteste (2)
    ("deco_proteste", "pt_cancelamento", 'site:deco.proteste.pt reclamação consumidor'),
    ("deco_proteste", "pt_ecommerce", 'site:deco.proteste.pt compras online'),
    # Trustpilot PT (4)
    ("trustpilot", "pt_telecom", 'site:trustpilot.com MEO Portugal review'),
    ("trustpilot", "pt_logistica", 'site:trustpilot.com CTT Portugal'),
    ("trustpilot", "pt_ecommerce", 'site:trustpilot.com Worten OR Fnac Portugal'),
    ("trustpilot", "pt_banco", 'site:trustpilot.com Millennium OR Novo Banco'),
    # Reguladores (3)
    ("reguladores", "pt_telecom", 'site:anacom.pt reclamação consumidor'),
    ("reguladores", "pt_cancelamento", 'site:consumidor.gov.pt livro reclamações'),
    ("reguladores", "pt_energia", 'site:erse.pt reclamação energia'),
    # Blogs jurídicos (6)
    ("blogs_juridicos", "pt_cancelamento", 'site:consumerlab.nova-sbe.pt direitos consumidor'),
    ("blogs_juridicos", "pt_banco", 'site:cgd.pt blog consumidor banca'),
    ("blogs_juridicos", "pt_banco", 'site:santander.pt consumidor'),
    ("blogs_juridicos", "pt_ecommerce", 'site:observador.pt direitos consumidor compras'),
    ("blogs_juridicos", "pt_habitacao", 'site:publico.pt arrendamento senhorio'),
    ("blogs_juridicos", "pt_telecom", 'site:dn.pt telecomunicações reclamação'),
    # Fóruns tech PT (3)
    ("forums_pt", "pt_ecommerce", 'site:forum.zwame.pt loja online problema'),
    ("forums_pt", "pt_ecommerce", 'site:forum.cfdistribuidos.com compra online'),
    ("forums_pt", "pt_telecom", 'site:forum.hardware.com.pt operadora'),
    # Google Reviews (2)
    ("google_reviews", "pt_telecom", 'site:google.com/maps MEO Lisboa reviews'),
    ("google_reviews", "pt_logistica", 'site:google.com/maps CTT reviews'),
    # Facebook grupos (4)
    ("facebook", "pt_burla", 'site:facebook.com burlas Portugal grupo'),
    ("facebook", "pt_cancelamento", 'site:facebook.com reclamações consumidor Portugal'),
    ("facebook", "pt_cancelamento", 'site:facebook.com brasileiros Portugal direitos'),
    ("facebook", "pt_ecommerce", 'site:facebook.com compras online Portugal problema'),
    # LinkedIn (1)
    ("linkedin", "pt_banco", 'site:linkedin.com/posts Portugal banco cliente reclamação'),
    # Notícias PT (3)
    ("noticias", "pt_ecommerce", 'site:publico.pt consumidor loja online'),
    ("noticias", "pt_telecom", 'site:dn.pt ANACOM telecom'),
    ("noticias", "pt_burla", 'site:observador.pt burla consumidor'),
    # Extras cobertura
    ("reddit_portugal", "pt_energia", 'site:reddit.com/r/portugal EDP Galp fatura'),
    ("reddit_portugal", "pt_habitacao", 'site:reddit.com/r/portugal senhorio arrendamento'),
    ("trustpilot", "pt_energia", 'site:trustpilot.com EDP Portugal'),
    ("reguladores", "pt_saude_seguro", 'site:ans.pt seguro saúde reclamação'),
    ("reddit_portugal", "pt_cobranca_indevida", 'site:reddit.com/r/portugal cobrança indevida'),
    ("trustpilot", "pt_cancelamento", 'site:trustpilot.com operadora Portugal cancelar'),
    ("noticias", "pt_logistica", 'site:expresso.pt CTT consumidor'),
    ("forums_pt", "pt_burla", 'site:4pda.to OR site:techpowerup.com Portugal compra golpe'),
]


def build_config() -> dict:
    dorks = []
    for i, (canal, grupo, query) in enumerate(DORKS_SPEC, start=1):
        dorks.append({
            "id": f"pt_v2_{i:03d}",
            "canal": canal,
            "grupo": grupo,
            "query": query,
        })
    return {
        "meta": {
            "tenant": "lex_portugal",
            "versao": "2.1",
            "portal_queixa": "desactivado_ate_nipc",
            "max_results_por_dork": 6,
            "delay_segundos_entre_dorks": 4,
        },
        "fontes": ["duckduckgo", "reddit"],
        "reddit": {
            "subreddits": ["portugal", "financaspessoaispt"],
            "limit": 20,
        },
        "hackernews": {"queries": []},
        "rss": {"feeds": []},
        "dorks": dorks,
    }


def main() -> None:
    import sys

    cfg = build_config()
    text = (
        "# Gerado por scripts/gerar_dorks_portugal_v2.py — NÃO commitar dorks.yaml real\n"
        "# Copie para dorks.yaml e refine queries (CONFIDENCIAL.md)\n\n"
    )
    text += yaml.dump(cfg, allow_unicode=True, sort_keys=False, width=120)
    EXAMPLE.write_text(text, encoding="utf-8")
    print(f"Escrito: {EXAMPLE} ({len(cfg['dorks'])} dorks, sem portal_queixa)")
    if OUT.exists() and "--sobrescrever" not in sys.argv:
        print(f"AVISO: {OUT} já existe — use --sobrescrever para actualizar a cópia local.")
    else:
        OUT.write_text(text.replace("# Gerado por", "# Local — gerado por"), encoding="utf-8")
        print(f"Escrito: {OUT}")


if __name__ == "__main__":
    main()
