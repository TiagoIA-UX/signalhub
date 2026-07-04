"""Envia mensagem de teste ao Telegram — valida token + chat_id."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    missing = []
    if not token or token.startswith("[PREENCHER]"):
        missing.append("TELEGRAM_BOT_TOKEN")
    if not chat_id or chat_id.startswith("[PREENCHER]"):
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"ERRO: Preencha no .env: {', '.join(missing)}")
        print("Guia: GUIA_SETUP_BOT_TELEGRAM.md")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = (
        "✅ SignalHub OK\n\n"
        "Bot configurado corretamente.\n"
        "Alertas de Lex Rocha e Zairyx chegarão aqui.\n\n"
        "Próximo passo: python run_once.py"
    )

    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=15.0,
        )
        resp.raise_for_status()
        body = resp.json()
    except httpx.HTTPError as exc:
        print(f"ERRO ao enviar: {exc}")
        sys.exit(1)

    if body.get("ok"):
        print("SUCESSO! Verifique o Telegram — mensagem 'SignalHub OK' deve ter chegado.")
    else:
        print(f"ERRO Telegram: {body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
