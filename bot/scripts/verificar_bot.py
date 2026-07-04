"""Verifica ID e username do bot Telegram via getMe."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local")  # se existir, sobrescreve

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    env_local = ROOT / ".env.local"
    env_file = ROOT / ".env"
    source = ".env.local" if env_local.exists() else ".env"
    print(f"Arquivo carregado: {source}")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    bot_id_from_token = token.split(":")[0] if ":" in token else "invalido"

    print(f"Bot ID (prefixo do token): {bot_id_from_token}")
    print(f"TELEGRAM_CHAT_ID:          {chat_id}")
    print()

    if not token:
        print("ERRO: TELEGRAM_BOT_TOKEN vazio")
        sys.exit(1)

    try:
        resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        data = resp.json()
    except httpx.HTTPError as exc:
        print(f"ERRO getMe: {exc}")
        sys.exit(1)

    if not data.get("ok"):
        print(f"getMe FALHOU: {data.get('description', data)}")
        sys.exit(1)

    bot = data["result"]
    print("getMe OK:")
    print(f"  id:         {bot.get('id')}")
    print(f"  username:   @{bot.get('username')}")
    print(f"  first_name: {bot.get('first_name')}")
    print()

    real_id = str(bot.get("id"))
    if chat_id == real_id:
        print("PROBLEMA: TELEGRAM_CHAT_ID = ID do bot.")
        print("         O chat_id deve ser o SEU user ID (quem recebe alertas).")
        print("         Rode: python scripts/obter_chat_id.py")
    elif bot_id_from_token != real_id:
        print("AVISO: prefixo do token nao bate com getMe.id")
    else:
        print("OK: token valido e chat_id diferente do bot.")


if __name__ == "__main__":
    main()
