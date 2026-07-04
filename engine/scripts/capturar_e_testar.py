"""Captura CHAT_ID (90s) e roda teste-live nos dois bots."""

import asyncio
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
BOTS = [
    ("Lex", "8531949198:AAF5sL8bcWEVqwhhHrBCNJLqutou9As-6DI", ROOT / "lex" / ".env"),
    ("Zai", "8911885159:AAH6-ww5fmyS9jqn_oBWyfumNQtGxTkiVc8", ROOT / "zairyx" / ".env"),
]


async def poll_bot(name: str, token: str, env_path: Path) -> int | None:
    offset = 0
    deadline = time.time() + 90
    async with httpx.AsyncClient(timeout=25) as c:
        me = await c.get(f"https://api.telegram.org/bot{token}/getMe")
        username = me.json().get("result", {}).get("username", "?")
        print(f"\n{name}: https://t.me/{username} — envie /start AGORA")

        while time.time() < deadline:
            r = await c.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": offset, "timeout": 8},
            )
            for u in r.json().get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                cid = m.get("chat", {}).get("id")
                frm = m.get("from", {})
                if cid and not frm.get("is_bot"):
                    txt = env_path.read_text(encoding="utf-8")
                    txt = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={cid}", txt)
                    env_path.write_text(txt, encoding="utf-8")
                    await c.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": cid, "text": f"{name} conectado! Alertas ativos."},
                    )
                    print(f"{name} CHAT_ID={cid} salvo")
                    return cid
            await asyncio.sleep(0.5)
    print(f"{name} timeout (sem /start recebido)")
    return None


async def main() -> None:
    results = await asyncio.gather(*[poll_bot(n, t, p) for n, t, p in BOTS])
    chat_ids = [r for r in results if r]
    if not chat_ids:
        print("\nNenhum CHAT_ID capturado. Envie /start nos dois bots e rode de novo.")
        sys.exit(1)

    # Mesmo usuario -> mesmo ID nos dois; se capturou um, copia pro outro
    cid = chat_ids[0]
    for _, _, p in BOTS:
        txt = p.read_text(encoding="utf-8")
        txt = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={cid}", txt)
        p.write_text(txt, encoding="utf-8")

    print(f"\nCHAT_ID unificado: {cid}")
    print("Rodando teste-live...\n")

    for folder in ("lex", "zairyx"):
        r = subprocess.run(
            [sys.executable, f"{folder}/bot.py", "teste-live"],
            cwd=ROOT,
            capture_output=False,
        )
        if r.returncode != 0:
            print(f"{folder} teste-live falhou")
    print("\nConcluido. Verifique alertas no Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
