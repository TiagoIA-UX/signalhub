"""Obtém TELEGRAM_CHAT_ID após você enviar /start ao bot."""

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
    if not token or token.startswith("[PREENCHER]"):
        print("ERRO: Preencha TELEGRAM_BOT_TOKEN no arquivo .env primeiro.")
        print("Guia: GUIA_SETUP_BOT_TELEGRAM.md")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    print("Buscando mensagens enviadas ao bot...")
    print("(Se vazio: abra o Telegram, busque seu bot e envie /start)\n")

    try:
        resp = httpx.get(url, timeout=15.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"ERRO ao conectar Telegram: {exc}")
        print("Verifique se o TELEGRAM_BOT_TOKEN está correto.")
        sys.exit(1)

    data = resp.json()
    if not data.get("ok"):
        print(f"ERRO API Telegram: {data}")
        sys.exit(1)

    updates = data.get("result", [])
    if not updates:
        print("Nenhuma mensagem encontrada.")
        print("\nFaça isto agora:")
        print("  1. Abra o Telegram no celular")
        print("  2. Busque o username do seu bot")
        print("  3. Envie: /start")
        print("  4. Rode este script de novo")
        sys.exit(1)

    seen: set[int] = set()
    for upd in reversed(updates):
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            name = chat.get("first_name", "") or chat.get("title", "Chat")
            username = chat.get("username", "")
            user_label = f"@{username}" if username else name
            print(f"Chat encontrado: {user_label}")
            print(f"\nCole no seu .env:\n")
            print(f"TELEGRAM_CHAT_ID={chat_id}")
            print()

    if not seen:
        print("Nenhum chat_id válido nos updates. Envie /start ao bot e tente de novo.")


if __name__ == "__main__":
    main()
