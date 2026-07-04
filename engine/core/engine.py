"""
core/engine.py — SignalHub Core
Scorer + Groq + Telegram. Importado por cada bot separadamente.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml

from core.sources.lead_filter import eh_lead_acionavel
from core.sources.link_resolver import link_parece_valido, normalizar_link_origem


class RateLimiter:
    def __init__(self, max_por_hora: int):
        self.max = max_por_hora
        self._hist: list[datetime] = []

    def pode(self) -> bool:
        agora = datetime.now()
        self._hist = [t for t in self._hist if t > agora - timedelta(hours=1)]
        return len(self._hist) < self.max

    def registrar(self):
        self._hist.append(datetime.now())


_FALLBACK_PROMPT = (
    "Gere 3 respostas curtas em JSON: {{\"r1\":\"...\",\"r2\":\"...\",\"r3\":\"...\"}}. "
    "Tom profissional. Sem promessas de resultado."
)

# Marcadores típicos de pt-BR (alerta pós-revisão; não bloqueia envio)
_PT_BR_MARCADORES = (
    r"\bvocê\b",
    r"\bvoce\b",
    r"\bcontato\b",
    r"\baplicativo\b",
    r"\bprocon\b",
    r"\bcdc\b",
    r"\breclame aqui\b",
    r"\bnosso time\b",
    r"\bordenado\b",
    r"\bcarteira\b",
    r"\bcelular\b",
)

_CANAL_COMUM: dict[str, str] = {
    "trustpilot": "Trustpilot",
    "google_reviews": "Google Reviews",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "noticias": "Notícias",
    "twitter_x": "X (Twitter)",
}

_CANAL_PT: dict[str, str] = {
    "reddit_portugal": "Reddit — r/portugal",
    "reddit_financas": "Reddit — r/financaspessoaispt",
    "deco_proteste": "DECO Proteste",
    "portal_queixa": "Portal da Queixa",
    "reguladores": "Reguladores PT",
    "blogs_juridicos": "Blogs jurídicos",
    "forums_pt": "Fóruns PT",
}

_CANAL_BR: dict[str, str] = {
    "reddit_brasil": "Reddit — r/brasil",
    "reclame_aqui": "Reclame Aqui",
    "consumidor_gov": "Consumidor.gov.br",
}

_DOMINIO_COMUM: dict[str, str] = {
    "reddit.com": "Reddit",
    "trustpilot.com": "Trustpilot",
    "news.ycombinator.com": "Hacker News",
}

_DOMINIO_PT: dict[str, str] = {
    "portaldaqueixa.com": "Portal da Queixa",
    "deco.proteste.pt": "DECO Proteste",
}

_DOMINIO_BR: dict[str, str] = {
    "reclameaqui.com.br": "Reclame Aqui",
    "consumidor.gov.br": "Consumidor.gov.br",
}


def _regiao_tenant(tenant: str) -> str:
    t = tenant.lower()
    if "portugal" in t:
        return "pt"
    if "rocha" in t or "brasil" in t:
        return "br"
    return ""


def _mapa_canais(tenant: str) -> dict[str, str]:
    m = dict(_CANAL_COMUM)
    regiao = _regiao_tenant(tenant)
    if regiao == "pt":
        m.update(_CANAL_PT)
    elif regiao == "br":
        m.update(_CANAL_BR)
    else:
        m.update(_CANAL_PT)
        m.update(_CANAL_BR)
    return m


def _mapa_dominios(tenant: str) -> dict[str, str]:
    m = dict(_DOMINIO_COMUM)
    regiao = _regiao_tenant(tenant)
    if regiao == "pt":
        m.update(_DOMINIO_PT)
    elif regiao == "br":
        m.update(_DOMINIO_BR)
    else:
        m.update(_DOMINIO_PT)
        m.update(_DOMINIO_BR)
    return m


def _escape_href(url: str) -> str:
    return url.replace("&", "&amp;").replace("'", "&#39;")


def nome_plataforma_origem(
    *,
    link: str,
    fonte: str = "",
    canal: str = "",
    tenant: str = "",
) -> str:
    """Nome legível da plataforma onde o lead foi detectado."""
    canais = _mapa_canais(tenant)
    dominios = _mapa_dominios(tenant)

    if canal and canal in canais:
        return canais[canal]
    if canal and not canais:
        return canal.replace("_", " ").title()

    m = re.match(r"reddit:r/(.+)", fonte or "")
    if m:
        return f"Reddit — r/{m.group(1)}"

    if fonte == "hackernews":
        return "Hacker News"
    if fonte == "rss":
        return "Google Alerts / RSS"

    host = urlparse(link).netloc.lower().removeprefix("www.")
    if host in dominios:
        return dominios[host]
    if host:
        return host
    if fonte and fonte not in ("dork:duckduckgo", "varredura:web"):
        return fonte
    return "Web"


_RE_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_RE_LEI_NUM = re.compile(
    r"\b(?:Lei|DL|Decreto-Lei|Art\.?|Artigo)\s*(?:n\.?º?\s*)?[\d./]+(?:\s*/\s*\d+)?",
    re.I,
)
_RE_INDICACAO_TERCEIROS = re.compile(
    r"\b(?:advogad\w*|solicitador\w*|consulta\s+(?:presencial|jurídica|com)|"
    r"apoio\s+jurídico|procon|deco|anacom|erse|asf|cicap|mediador\w*|"
    r"arbitragem|consumidor\.gov|escalon?\w*|via\s+útil)\b",
    re.I,
)
_LIMPEZA_TERCEIROS = (
    (r"—?\s*uma consulta presencial pode rondar[^.]*\.?", ""),
    (r"pode avaliar com o advogado que escolher\.?", ""),
    (r"No seu tipo de caso,[^.]*via útil\.?", ""),
    (r"[^.]*(?:banco de portugal|anacom|erse|deco)[^.]*\.?", ""),
    (r"para falar com o seu banco ou advogado[^.]*\.?", ""),
    (r"consulta jurídica[^.]*\.?", ""),
    (r"muito abaixo de uma consulta[^.]*\.?", ""),
)


def remover_indicacoes_terceiros(texto: str) -> str:
    """Remove recomendações a advogados, reguladores e outros serviços externos."""
    t = texto
    for pat, repl in _LIMPEZA_TERCEIROS:
        t = re.sub(pat, repl, t, flags=re.I)
    frases = re.split(r"(?<=[.!?])\s+", t)
    mantidas = [f for f in frases if f.strip() and not _RE_INDICACAO_TERCEIROS.search(f)]
    t = " ".join(mantidas).strip()
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([,.;!?])", r"\1", t)
    return t.strip()


def humanizar_resposta_pt(texto: str) -> str:
    """Resposta humana pt-PT: sem links, leis numeradas nem indicação de terceiros."""
    t = _RE_URL.sub("", texto)
    t = re.sub(r"\b(?:dgsi|dre)\.[^\s,;.]+", "", t, flags=re.I)
    t = _RE_LEI_NUM.sub("", t)
    t = remover_indicacoes_terceiros(t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([,.;!?])", r"\1", t)
    return t.strip()


def formatar_linha_origem(
    *,
    link: str,
    fonte: str = "",
    canal: str = "",
    tenant: str = "",
) -> str:
    """Linha HTML com link clicável para a publicação na plataforma de origem."""
    nome = nome_plataforma_origem(
        link=link, fonte=fonte, canal=canal, tenant=tenant
    )
    href = _escape_href(link)
    link_visivel = link.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'📍 <b>Origem:</b> <a href="{href}">{nome}</a>\n'
        f"📎 <code>{link_visivel}</code>"
    )


class SignalHubEngine:
    def __init__(self, config_path: Path, env: dict, log: logging.Logger):
        self.log = log
        self.env = env
        self.config_path = config_path
        self.cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        self._prompts = self._carregar_prompts()

        self.nicho_id = list(self.cfg["nichos"].keys())[0]
        self.nicho_cfg = self.cfg["nichos"][self.nicho_id]
        self.score_min = self.nicho_cfg.get("score_minimo", 7)
        self.rl = RateLimiter(int(env.get("MAX_ALERTAS_POR_HORA", 20)))
        self._seen_urls: set[str] = set()
        self._ultimo_aviso_pt_br: list[str] = []
        self._alertas_telegram: dict[str, dict] = {}

    def _carregar_prompts(self) -> dict:
        path = self.config_path.parent / "prompts.yaml"
        if not path.exists():
            self.log.warning(f"prompts.yaml ausente em {path.parent} — usando fallback genérico")
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def score(self, texto: str) -> tuple[int, str]:
        t = texto.lower()
        bonus = 0
        for frase in self.cfg.get("intencao_alta", []):
            if frase in t:
                bonus = 2
                break

        best_score, best_grupo = 0, ""
        for gid, g in self.nicho_cfg.get("grupos", {}).items():
            peso = g.get("peso", 5)
            for kw in g.get("keywords", []):
                if kw.lower() in t:
                    s = min(peso + bonus, 10)
                    if s > best_score:
                        best_score, best_grupo = s, gid
        return best_score, best_grupo

    def _regras_setor(self, grupo_id: str) -> dict:
        leg = self.nicho_cfg.get("legal_pt") or {}
        setores = leg.get("setores") or {}
        geral = leg.get("geral") or {}
        setor = setores.get(grupo_id) or {}
        prazo = setor.get("prazo") or geral.get("prazo_resposta") or leg.get(
            "prazo_resposta", "15 dias úteis"
        )
        return {
            "prazo": prazo,
            "base_prazo": setor.get("base_prazo")
            or geral.get("base_prazo")
            or leg.get("base_prazo", "DL 156/2005 / Livro de Reclamações"),
            "nota_setor": (setor.get("nota_prazo") or "").strip(),
            "regulatorio": setor.get("regulatorio", ""),
            "detecao": leg.get(
                "instrucao_deteccao",
                "Adaptar o prazo e o órgão ao setor inferido do post; se ambíguo, usar regra geral e mencionar prudência.",
            ),
        }

    def _contexto_legal(self, grupo_id: str) -> str:
        leg = self.nicho_cfg.get("legal_pt") or {}
        if not leg:
            return ""
        grupo = self.nicho_cfg["grupos"][grupo_id]
        setor = self._regras_setor(grupo_id)
        precos = self.nicho_cfg.get("precos") or {}
        sug = grupo.get("plano_sugerido", "padrao")
        preco_map = {
            "essencial": precos.get("essencial"),
            "padrao": precos.get("padrao"),
            "completo": precos.get("completo"),
        }
        preco_sug = preco_map.get(sug, precos.get("padrao"))
        linhas = [
            setor["detecao"],
            f"Setor detectado (scoring): {grupo_id} — {grupo.get('nome', '')}",
            f"Prazo a usar na R2: {setor['prazo']} ({setor['base_prazo']})",
            f"Lei consumidor: {leg.get('lei_base', 'Lei n.º 24/96')}",
        ]
        if setor["regulatorio"]:
            linhas.append(
                f"Contexto setorial interno (não mencionar em R1-R3): {setor['regulatorio']}"
            )
        if setor["nota_setor"]:
            linhas.append(
                f"Nota interna setor (não citar entidades externas): {setor['nota_setor']}"
            )
        linhas.extend([
            f"Plano sugerido: {sug} — €{preco_sug}",
            "Somos trabalho autónomo de pesquisa documental — só o nosso relatório.",
            "PROIBIDO nas respostas: indicar advogados, reguladores, DECO, mediadores "
            "ou qualquer serviço de terceiros; não somos pagos para referenciar ninguém.",
            "Nas respostas públicas: tom humano pt-PT, sem URLs, sem números de diploma.",
            f"Regra fontes: {leg.get('nota_fontes', 'Não citar bases de dados antes do pagamento.')}",
        ])
        roteiro = leg.get("roteiro_obrigatorio")
        if roteiro:
            linhas.append(f"Roteiro:\n{roteiro.strip()}")
        return "\n".join(linhas)

    def _contexto_comercial(self, grupo_id: str) -> str:
        grupo = self.nicho_cfg["grupos"][grupo_id]
        partes: list[str] = []
        legal = self._contexto_legal(grupo_id)
        if legal:
            partes.append(legal)
        if roi := grupo.get("roi_referencia"):
            partes.append(
                f"Referência interna de valor (não citar em R1-R3): {roi.strip()}"
            )
        precos = self.nicho_cfg.get("precos") or {}
        if precos:
            e, p, c = precos.get("essencial"), precos.get("padrao"), precos.get("completo")
            sug = grupo.get("plano_sugerido", "padrao")
            partes.append(
                f"Planos: Essencial €{e} · Padrão €{p} · Completo €{c}. "
                f"Sugerido para este grupo: {sug}."
            )
            if tag := precos.get("tagline"):
                partes.append(str(tag))
        return "\n".join(partes) if partes else "Sem contexto comercial extra."

    def _humanizar_respostas(self, respostas: list[str]) -> list[str]:
        if not self.nicho_cfg.get("legal_pt"):
            return respostas
        return [humanizar_resposta_pt(r) for r in respostas]

    def _fallback_respostas(self, grupo_id: str) -> list[str]:
        leg = self.nicho_cfg.get("legal_pt") or {}
        if not leg:
            marca = self.nicho_cfg.get("marca") or self.nicho_cfg.get("nome", "")
            return self._humanizar_respostas([
                "Olá — a sua situação merece ser analisada com calma.",
                "Há enquadramento aplicável; podemos orientar os próximos passos em linguagem clara.",
                f"Se quiser, a {marca} pode preparar um relatório documental só para o seu caso.",
            ])
        grupo = self.nicho_cfg["grupos"][grupo_id]
        precos = self.nicho_cfg.get("precos") or {}
        sug = grupo.get("plano_sugerido", "padrao")
        preco = precos.get(sug, precos.get("padrao", 39))
        setor = self._regras_setor(grupo_id)
        prazo = setor["prazo"]
        marca = self.nicho_cfg.get("marca") or self.nicho_cfg.get("nome", "")
        return self._humanizar_respostas([
            "Olá — obrigado por partilhar isto connosco. Percebemos o incómodo "
            "e faz sentido querer uma resposta concreta.",
            f"Na prática, depois de uma reclamação formal, a empresa costuma ter de responder "
            f"em cerca de {prazo}. Vale a pena guardar provas e datas do que aconteceu.",
            f"Na {marca}, preparamos um relatório documental só para o seu caso "
            f"(cerca de €{preco}, sempre confirmado por escrito antes de pagar).",
        ])

    def _usar_revisao_groq(self) -> bool:
        if not self.nicho_cfg.get("legal_pt"):
            return False
        if self.env.get("GROQ_REVISAO", "1").strip().lower() in ("0", "false", "nao", "não"):
            return False
        return bool(self._prompts.get("groq_revisao_template"))

    def _detectar_pt_br(self, respostas: list[str]) -> list[str]:
        texto = " ".join(respostas).lower()
        return [p for p in _PT_BR_MARCADORES if re.search(p, texto, re.I)]

    def _parse_respostas_json(self, raw: str) -> list[str]:
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            p = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{[^{}]*\"r1\"[^{}]*\"r3\"[^{}]*\}", raw, re.DOTALL)
            if not m:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                raise
            p = json.loads(m.group(0))
        return [p.get("r1", ""), p.get("r2", ""), p.get("r3", "")]

    async def _groq_completion(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 450,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        model = self.env.get("GROQ_MODEL", "openai/gpt-oss-120b")
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=35) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.env['GROQ_API_KEY']}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

    async def _revisar_respostas_pt(
        self, rascunho: list[str], texto_post: str, grupo_id: str
    ) -> list[str]:
        tpl = self._prompts.get("groq_revisao_template", "")
        leg = self.nicho_cfg.get("legal_pt") or {}
        gloss = "\n".join(f"- {g}" for g in (leg.get("glossario_pt_pt") or []))
        fmt = {
            "marca": self.nicho_cfg.get("marca") or self.nicho_cfg.get("nome", ""),
            "glossario_pt_pt": gloss or "(ver regras no prompt)",
            "r1": rascunho[0],
            "r2": rascunho[1],
            "r3": rascunho[2],
        }
        try:
            system = tpl.format(**fmt)
        except KeyError:
            system = tpl
        user = f'Post original: "{texto_post[:500]}"\nRascunho a rever (JSON).'
        try:
            raw = await self._groq_completion(
                system, user, temperature=0.3, json_mode=True
            )
            revisado = self._parse_respostas_json(raw)
            self.log.info("Groq revisão pt-PT concluída")
            return self._humanizar_respostas(revisado)
        except Exception as e:
            self.log.error(f"Groq revisão falhou: {e} — mantém rascunho")
            return self._humanizar_respostas(rascunho)

    async def gerar_respostas(self, texto: str, grupo_id: str) -> list[str]:
        grupo = self.nicho_cfg["grupos"][grupo_id]
        nicho_nome = self.nicho_cfg["nome"]
        grupo_nome = grupo["nome"]
        cta_link = self.nicho_cfg.get("cta_link", "")
        cta_txt = self.nicho_cfg.get("cta_texto", "")

        template = self._prompts.get("groq_system_template", _FALLBACK_PROMPT)
        leg = self.nicho_cfg.get("legal_pt") or {}
        precos = self.nicho_cfg.get("precos") or {}
        sug = grupo.get("plano_sugerido", "padrao")
        preco_sug = precos.get(sug, precos.get("padrao", ""))
        setor = self._regras_setor(grupo_id)
        fmt = {
            "nicho_nome": nicho_nome,
            "grupo_nome": grupo_nome,
            "cta_txt": cta_txt,
            "cta_link": cta_link,
            "contexto_comercial": self._contexto_comercial(grupo_id),
            "lei_base": leg.get("lei_base", "Lei n.º 24/96"),
            "prazo_resposta": setor["prazo"],
            "base_prazo": setor["base_prazo"],
            "nota_setor": setor["nota_setor"] or "Regra geral do Livro de Reclamações.",
            "preco_sugerido": preco_sug,
        }
        try:
            system = template.format(**fmt)
        except KeyError as err:
            self.log.warning(f"Prompt placeholder ausente: {err}")
            system = template.format(
                nicho_nome=nicho_nome,
                grupo_nome=grupo_nome,
                cta_txt=cta_txt,
                cta_link=cta_link,
                contexto_comercial=self._contexto_comercial(grupo_id),
                lei_base=fmt["lei_base"],
                prazo_resposta=fmt["prazo_resposta"],
                base_prazo=fmt["base_prazo"],
                preco_sugerido=fmt["preco_sugerido"],
                nota_setor=fmt["nota_setor"],
            )

        try:
            raw = await self._groq_completion(
                system,
                f'Post: "{texto[:500]}"',
                max_tokens=400,
                temperature=0.7,
                json_mode=True,
            )
            rascunho = self._humanizar_respostas(self._parse_respostas_json(raw))
            if self._usar_revisao_groq():
                return await self._revisar_respostas_pt(rascunho, texto, grupo_id)
            return rascunho
        except Exception as e:
            self.log.error(f"Groq erro: {e}")
            return self._fallback_respostas(grupo_id)

    def _bloco_comercial_telegram(self, grupo_id: str, score: int) -> str:
        """Preços claros + CTA neurocomportamental quando o caso é favorável."""
        precos = self.nicho_cfg.get("precos") or {}
        if not precos:
            return ""

        e, p, c = precos.get("essencial"), precos.get("padrao"), precos.get("completo")
        grupo = self.nicho_cfg["grupos"][grupo_id]
        sug = grupo.get("plano_sugerido", "padrao")
        labels = {"essencial": "Essencial", "padrao": "Padrão", "completo": "Completo"}
        sug_label = labels.get(sug, sug)
        preco_map = {"essencial": e, "padrao": p, "completo": c}
        preco_sug = preco_map.get(sug, p)
        dominio = self.nicho_cfg.get("dominio", "")
        cta_link = self.nicho_cfg.get("cta_link", "")
        marca = self.nicho_cfg.get("marca") or self.nicho_cfg["nome"]
        dom_link = (
            f"<a href='{_escape_href(cta_link)}'>{dominio}</a>"
            if dominio and cta_link
            else dominio
        )

        media_txt = precos.get(
            "media_investimento",
            f"Investimento médio dos relatórios: €{e} (Essencial) · €{p} (Padrão) · €{c} (Completo)",
        )

        linhas = [
            f"\n\n💶 <b>{marca}</b> — {dom_link}",
            media_txt,
            f"Essencial <b>€{e}</b> · Padrão <b>€{p}</b> · Completo <b>€{c}</b>",
        ]

        caso_favoravel = score >= 8
        if caso_favoravel:
            roi = (grupo.get("roi_referencia") or "").strip()
            setor = self._regras_setor(grupo_id)
            prazo = setor["prazo"]
            linhas.extend([
                f"\n🎯 <b>Caso com potencial</b> (score {score}/10)",
                (
                    f"Para este tipo de situação, um relatório documental organiza factos, "
                    f"prazos (cerca de {prazo}) e enquadramento — evita avançar sem mapa "
                    f"e perder tempo com a empresa."
                ),
                (
                    f"↳ Plano indicado: <b>{sug_label} · €{preco_sug}</b> "
                    f"(triagem gratuita em {dominio or 'direitosconsumidor.com'})"
                ),
                (
                    f"📲 <b>Próximo passo:</b> comentar com acolhimento (R1) e, na R3, "
                    f"convidar para a triagem em {dominio or 'direitosconsumidor.com'} "
                    f"— valor exacto antes de pagar."
                ),
            ])
            if roi:
                linhas.append(f"<i>Referência interna (não citar literal): {roi}</i>")
        else:
            linhas.append(
                f"↳ Sugerido para este grupo: <b>{sug_label} · €{preco_sug}</b> · "
                f"{precos.get('nota', 'Valor confirmado antes do pagamento.')}"
            )

        if tag := precos.get("tagline"):
            linhas.append(str(tag))

        return "\n".join(linhas)

    async def enviar_alerta(
        self,
        texto: str,
        link: str,
        autor: str,
        grupo_id: str,
        score: int,
        respostas: list[str],
        *,
        fonte: str = "",
        canal: str = "",
        dork_id: str = "",
    ) -> bool:
        token = self.env.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = self.env.get("TELEGRAM_CHAT_ID", "")

        if not token or not chat_id:
            self.log.error("BOT_TOKEN ou CHAT_ID ausente no .env")
            return False

        grupo_nome = self.nicho_cfg["grupos"][grupo_id]["nome"]
        emoji = self.nicho_cfg.get("emoji", "📌")
        nicho_nome = self.nicho_cfg.get("marca") or self.nicho_cfg["nome"]

        citacao = texto[:200].replace("<", "&lt;").replace(">", "&gt;")
        if len(texto) > 200:
            citacao += "..."

        r1, r2, r3 = respostas
        linha_origem = formatar_linha_origem(
            link=link,
            fonte=fonte,
            canal=canal,
            tenant=self.nicho_id,
        )
        href = _escape_href(link)

        msg = (
            f"{emoji} <b>{nicho_nome}</b>\n"
            f"📂 {grupo_nome} — Score: <b>{score}/10</b>\n"
            f"{linha_origem}\n"
            f"👤 {autor}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f'<i>"{citacao}"</i>\n'
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>R1 — Acolhimento:</b>\n{r1}\n\n"
            f"<b>R2 — Enquadramento legal:</b>\n{r2}\n\n"
            f"<b>R3 — Relatório reservado:</b>\n{r3}\n\n"
            f'🔗 <a href="{href}">Abrir publicação na plataforma</a>'
        )

        msg += self._bloco_comercial_telegram(grupo_id, score)

        if self._ultimo_aviso_pt_br:
            msg += (
                "\n\n⚠️ <i>Revisar linguagem: possível pt-BR detectado "
                f"({len(self._ultimo_aviso_pt_br)} indício(s))</i>"
            )

        empresa = self.nicho_cfg.get("empresa") or {}
        if empresa.get("cnpj"):
            atuacao = empresa.get("atuacao", "Pesquisa jurídica documental")
            msg += (
                f"\n\n<i>{atuacao} · {empresa.get('forma', '')} "
                f"CNPJ {empresa['cnpj']}</i>"
            )

        callback_key = link[:50]
        kb = {
            "inline_keyboard": [[
                {"text": "✅ R1", "callback_data": f"r1|{callback_key}"},
                {"text": "✅ R2", "callback_data": f"r2|{callback_key}"},
                {"text": "✅ R3", "callback_data": f"r3|{callback_key}"},
                {"text": "🗑 Descartar", "callback_data": f"drop|{callback_key}"},
            ]]
        }

        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                        "reply_markup": kb,
                    },
                )
                if r.status_code != 200:
                    self.log.error(f"Telegram {r.status_code}: {r.text}")
                    return False
                result = r.json().get("result", {})
                self._alertas_telegram[callback_key] = {
                    "r1": r1,
                    "r2": r2,
                    "r3": r3,
                    "html": msg,
                    "message_id": result.get("message_id"),
                    "chat_id": chat_id,
                    "respondido": None,
                }
                return True
        except Exception as e:
            self.log.error(f"Telegram exc: {e}")
            return False

    def ja_viu(self, url: str) -> bool:
        return url in self._seen_urls

    def marcar_visto(self, url: str) -> None:
        self._seen_urls.add(url)

    async def processar(self, post: dict, *, dry_run: bool = False) -> bool:
        post = dict(post)
        link = normalizar_link_origem(post.get("link", ""))
        if not link_parece_valido(link):
            self.log.warning(f"Link inválido ou mock ignorado: {link[:80]}")
            return False
        post["link"] = link

        if self.ja_viu(post["link"]):
            return False

        if not eh_lead_acionavel(post["link"], post.get("texto", "")):
            self.log.debug(f"Não é lead acionável (agregado/sem pedido): {link[:80]}")
            self.marcar_visto(post["link"])
            return False

        score, grupo_id = self.score(post["texto"])
        if score < self.score_min or not grupo_id:
            self.log.debug(f"score={score} ignorado: {post['texto'][:60]}")
            self.marcar_visto(post["link"])
            return False

        if not self.rl.pode():
            self.log.warning("Rate limit — alerta suprimido")
            return False

        self.log.info(f"Qualificado score={score} grupo={grupo_id}")
        respostas = await self.gerar_respostas(post["texto"], grupo_id)
        self._ultimo_aviso_pt_br = self._detectar_pt_br(respostas)
        if self._ultimo_aviso_pt_br:
            self.log.warning(f"Possível pt-BR após revisão: {self._ultimo_aviso_pt_br}")

        if dry_run:
            self.log.info(f"[DRY] {post['link']}")
            return True

        ok = await self.enviar_alerta(
            post["texto"], post["link"], post["autor"],
            grupo_id, score, respostas,
            fonte=post.get("fonte", ""),
            canal=post.get("canal", ""),
            dork_id=post.get("dork_id", ""),
        )
        self.marcar_visto(post["link"])
        if ok:
            self.rl.registrar()
        return ok
