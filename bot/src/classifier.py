"""Camada 2 — classificação via Groq."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from src.retry import retry_call

CLASSIFIER_SYSTEM = """Você classifica posts públicos brasileiros por INTENÇÃO REAL de solução.

SAÍDA JSON estrita (sem markdown):
{
  "tenant": "lexrocha" | "zairyx" | "ignore",
  "tema": "codigo_snake_case",
  "score": 1-10,
  "urgencia": "baixa" | "media" | "alta",
  "razao": "1 frase",
  "citacao": "trecho literal max 280 chars"
}

REGRAS:
- score >= 7 apenas se pessoa BUSCA AJUDA/SOLUÇÃO
- lexrocha: CDC, consumidor, digital, LGPD
- zairyx: delivery, comissão marketplace, canal próprio, Google Meu Negócio
- ignore: política, humor, spam
- NUNCA inferir dados pessoais
"""


@dataclass
class Classification:
    tenant: str
    tema: str
    score: int
    urgencia: str
    razao: str
    citacao: str

    @property
    def is_actionable(self) -> bool:
        return self.tenant != "ignore" and self.score >= 7


def parse_classification(raw: str) -> Classification:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    return Classification(
        tenant=data.get("tenant", "ignore"),
        tema=data.get("tema", "unknown"),
        score=int(data.get("score", 0)),
        urgencia=data.get("urgencia", "baixa"),
        razao=data.get("razao", ""),
        citacao=data.get("citacao", "")[:280],
    )


class GroqClassifier:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b") -> None:
        from groq import Groq

        self.client = Groq(api_key=api_key)
        self.model = model

    def classify(self, title: str, body: str, hint_tenant: str | None = None) -> Classification:
        hint = f"\nDica pré-filtro: tenant provável = {hint_tenant}" if hint_tenant else ""
        user_msg = f"Título: {title}\n\nCorpo: {body[:2000]}{hint}"

        def _classify() -> Classification:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLASSIFIER_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            content = response.choices[0].message.content or "{}"
            return parse_classification(content)

        return retry_call(_classify, label="groq.classify")


class MockClassifier:
    """Classificador offline para testes sem API."""

    def classify(self, title: str, body: str, hint_tenant: str | None = None) -> Classification:
        text = f"{title} {body}".lower()
        if "ifood" in text or "comissão" in text:
            return Classification(
                tenant="zairyx",
                tema="z1_comissao_ifood",
                score=8,
                urgencia="media",
                razao="Dono de delivery busca alternativa à comissão",
                citacao=body[:200],
            )
        if any(w in text for w in ("defeito", "procon", "conta bloqueada", "cdc")):
            return Classification(
                tenant="lexrocha",
                tema="g9_orientacao_consumidor",
                score=9,
                urgencia="alta",
                razao="Consumidor busca orientação sobre direitos",
                citacao=body[:200],
            )
        return Classification(
            tenant="ignore",
            tema="unknown",
            score=2,
            urgencia="baixa",
            razao="Sem intenção clara",
            citacao="",
        )
