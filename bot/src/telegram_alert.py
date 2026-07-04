"""Camada 3 — formatação de alertas Telegram."""

from __future__ import annotations

from dataclasses import dataclass

from src.classifier import Classification
from src.responder import Responses


@dataclass
class RawPost:
    url: str
    title: str
    body: str
    source: str
    subreddit: str | None = None


@dataclass
class AlertPayload:
    post: RawPost
    classification: Classification
    responses: Responses
    cta_url: str

    def format_message(self) -> str:
        c = self.classification
        p = self.post
        sub = f" r/{p.subreddit}" if p.subreddit else ""
        citacao = c.citacao or p.body[:280]

        lines = [
            f"🔔 OPORTUNIDADE {c.score}/10 — {c.tenant.upper()}",
            f"📂 Tema: {c.tema} | Urgência: {c.urgencia}",
            f"🌐 Fonte: {p.source}{sub}",
            f"🔗 {p.url}",
            "",
            "💬 Fala do cliente:",
            f'"{citacao}"',
            "",
            "─────────────────",
            "📝 RESPOSTA 1 (empática):",
            self.responses.r1,
            "",
            "📝 RESPOSTA 2 (técnica):",
            self.responses.r2,
            "",
            "📝 RESPOSTA 3 (curta):",
            self.responses.r3,
            "",
            "─────────────────",
            f"🎯 CTA: {self.cta_url}",
            "",
            "Copie a resposta escolhida e cole manualmente no post.",
        ]
        msg = "\n".join(lines)
        return msg[:4090]

    def callback_id(self) -> str:
        from src.deduper import Deduper

        return Deduper.hash_url(self.post.url)[:16]

    def inline_keyboard(self) -> list[list[dict[str, str]]]:
        uid = self.callback_id()
        return [
            [
                {"text": "✅ R1", "callback_data": f"approve:r1:{uid}"},
                {"text": "✅ R2", "callback_data": f"approve:r2:{uid}"},
                {"text": "✅ R3", "callback_data": f"approve:r3:{uid}"},
            ],
            [{"text": "❌ Descartar", "callback_data": f"discard:{uid}"}],
        ]


def sanitize_for_groq(text: str) -> str:
    """Remove padrões comuns de PII antes de enviar ao Groq."""
    import re

    t = text
    t = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "[CPF]", t)
    t = re.sub(r"\b\d{2}\s?\d{4,5}-?\d{4}\b", "[TEL]", t)
    t = re.sub(r"[\w.-]+@[\w.-]+\.\w+", "[EMAIL]", t)
    return t
