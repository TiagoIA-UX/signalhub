"""Camada 3 — geração de respostas via Groq."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from src.config_loader import CONFIG_DIR, load_yaml
from src.retry import retry_call

RESPONDER_SYSTEM = """Você gera 3 respostas para comunidade online (Reddit/Facebook/forum) em PT-BR.

PRINCÍPIOS:
1. Reciprocidade: insight útil ANTES do link
2. Autoridade calma, sem arrogância
3. Transparência: disclosure de vínculo
4. NUNCA prometa resultado, indenização ou vitória judicial
5. Lex Rocha = pesquisa documental, NÃO advogado
6. Zairyx = cardápio digital, zero comissão/pedido, ebook Google Meu Negócio incluso

PROIBIDO: "contrate agora", "garantido", "100%"

SAÍDA JSON (sem markdown):
{"r1": "empática max 800 chars", "r2": "técnica max 800 chars", "r3": "curta max 400 chars"}
"""


@dataclass
class Responses:
    r1: str
    r2: str
    r3: str


def parse_responses(raw: str) -> Responses:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    return Responses(
        r1=data.get("r1", "")[:800],
        r2=data.get("r2", "")[:800],
        r3=data.get("r3", "")[:400],
    )


def build_cta_url(tenant: str, fonte: str, tema: str) -> str:
    tenants = load_yaml(CONFIG_DIR / "tenants.yaml")
    cfg = tenants.get(tenant, {})
    base = cfg.get("base_url", "https://example.com")
    from datetime import date

    campaign = f"sig_{date.today().isoformat().replace('-', '')}"
    return (
        f"{base}?utm_source={fonte}&utm_medium=community"
        f"&utm_campaign={campaign}&tema={tema}"
    )


class GroqResponder:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b") -> None:
        from groq import Groq

        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(
        self,
        tenant: str,
        tema: str,
        post_excerpt: str,
        cta_url: str,
    ) -> Responses:
        tenants = load_yaml(CONFIG_DIR / "tenants.yaml")
        disclosure = tenants.get(tenant, {}).get("disclosure", "")

        user_msg = (
            f"Tenant: {tenant}\nTema: {tema}\n"
            f"Post: {post_excerpt[:1500]}\n"
            f"Link CTA: {cta_url}\nDisclosure: {disclosure}"
        )

        def _generate() -> Responses:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESPONDER_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.6,
                max_tokens=1200,
            )
            content = response.choices[0].message.content or "{}"
            return parse_responses(content)

        return retry_call(_generate, label="groq.generate")


class MockResponder:
    """Respostas offline para testes."""

    def generate(
        self,
        tenant: str,
        tema: str,
        post_excerpt: str,
        cta_url: str,
    ) -> Responses:
        if tenant == "lexrocha":
            return Responses(
                r1=(
                    "Situações assim costumam ter prazos no CDC que muita gente só descobre "
                    "no Procon. Pesquisa documental de precedentes públicos ajuda na 1ª "
                    f"consulta com advogado (material informativo). Modelo: {cta_url}"
                ),
                r2=(
                    f"Para {tema}, vale reunir comprovantes e protocolos antes de ajuizar. "
                    "A Lex Rocha consulta tribunais e entrega PDF com referências — "
                    f"não substitui OAB. A partir de R$49: {cta_url}"
                ),
                r3=f"CDC tem regras pra isso. Modelo grátis do relatório: {cta_url}",
            )
        return Responses(
            r1=(
                "Com entregador próprio, comissão de marketplace pesa. Canal WhatsApp + "
                f"cardápio digital sem taxa por pedido ajuda. Trial + ebook GMB: {cta_url}"
            ),
            r2=(
                "Google Meu Negócio (grátis) + pedido direto = margem melhor. Zairyx inclui "
                f"ebook passo a passo GMB em qualquer plano: {cta_url}"
            ),
            r3=f"Canal próprio sem comissão/pedido. Teste 7 dias: {cta_url}",
        )
