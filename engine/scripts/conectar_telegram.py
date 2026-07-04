#!/usr/bin/env python3
"""
Conecta Lex + Zairyx ao seu Telegram (um passo só).

1. Execute este script (ou CONECTAR_TELEGRAM.bat)
2. O navegador abre os dois bots — em cada um toque INICIAR (ou envie /start)
3. O script grava TELEGRAM_CHAT_ID e envia mensagem de confirmação
"""

from __future__ import annotations

import asyncio
import re
import sys
import time
import webbrowser
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
MONOREPO = ROOT.parent
LEX_ENV = MONOREPO / "Lex-Rocha" / "signalhub-br" / ".env"
if not LEX_ENV.exists():
    LEX_ENV = ROOT / "lex" / ".env"
ZAIRYX_ENV = ROOT / "zairyx" / ".env"

BOTS = [
    ("Lex", LEX_ENV, "https://t.me/tiago_a_rocha_alertas_lex_bot?start=conectar"),
    ("Zairyx", ZAIRYX_ENV, "https://t.me/tiago_a_rocha_alertas_zai_bot?start=conectar"),
]


def salvar_chat_id(env_path: Path, chat_id: int) -> None:
    txt = env_path.read_text(encoding="utf-8")
    if "TELEGRAM_CHAT_ID=" in txt:
        txt = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={chat_id}", txt)
    else:
        txt += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
    env_path.write_text(txt, encoding="utf-8")


async def capturar(token: str, nome: str, segundos: int = 180) -> int | None:
    print(f"\n[{nome}] Aguardando /start por {segundos}s...")
    offset = 0
    fim = time.time() + segundos
    async with httpx.AsyncClient(timeout=20) as c:
        while time.time() < fim:
            try:
                r = await c.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset": offset, "timeout": 8},
                )
                for upd in r.json().get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message") or upd.get("edited_message") or {}
                    chat = msg.get("chat", {})
                    cid = chat.get("id")
                    if cid and chat.get("type") in ("private", "group", "supergroup"):
                        await c.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={
                                "chat_id": cid,
                                "text": f"✅ {nome} conectado! Alertas ativos.",
                            },
                        )
                        return int(cid)
            except Exception as e:
                print(f"  aviso: {e}")
            restante = int(fim - time.time())
            if restante % 15 == 0 and restante > 0:
                print(f"  ... ainda aguardando ({restante}s)")
    return None


async def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("  SignalHub — Conectar Telegram (Lex + Zairyx)")
    print("=" * 60)
    print("\nAbrindo os dois bots no navegador...")
    print("Em CADA aba: toque INICIAR ou envie /start\n")

    for _, _, url in BOTS:
        webbrowser.open(url)
        await asyncio.sleep(1)

    chat_ids: dict[str, int] = {}

    for nome, env_path, _ in BOTS:
        env = dotenv_values(env_path)
        token = env.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            print(f"[{nome}] ERRO: token ausente em {env_path.name}")
            continue
        cid = await capturar(token, nome, 180)
        if cid:
            salvar_chat_id(env_path, cid)
            chat_ids[nome] = cid
            print(f"[{nome}] OK → TELEGRAM_CHAT_ID={cid}")
        else:
            print(f"[{nome}] Timeout — abra manualmente e rode de novo.")

    if len(chat_ids) == 2 and chat_ids["Lex"] == chat_ids["Zairyx"]:
        print("\n✅ Mesmo usuário nos dois bots — pronto para teste-live.")
    elif len(chat_ids) == 1:
        print("\n⚠️ Só um bot conectou. Abra o outro link e rode o script novamente.")
    else:
        print("\n❌ Nenhum bot recebeu /start.")
        print("   Links diretos:")
        print("   https://t.me/tiago_a_rocha_alertas_lex_bot")
        print("   https://t.me/tiago_a_rocha_alertas_zai_bot")
        sys.exit(1)

    # Teste rápido Lex
    print("\nEnviando alerta de teste (Lex)...")
    env = {**dotenv_values(LEX_ENV)}
    token = env["TELEGRAM_BOT_TOKEN"]
    chat_id = env["TELEGRAM_CHAT_ID"]
    async with httpx.AsyncClient(timeout=15) as c:
        await c.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "⚖️ LexBot — teste de conexão OK. Sistema pronto.",
                "parse_mode": "HTML",
            },
        )
    print("Verifique o Telegram. Depois: python Lex-Rocha/signalhub-br/hub.py teste-live")


if __name__ == "__main__":
    asyncio.run(main())
