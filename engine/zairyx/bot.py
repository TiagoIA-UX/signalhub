#!/usr/bin/env python3
"""
zairyx/bot.py — ZairyxBot (Delivery)
  python zairyx/bot.py detectar
  python zairyx/bot.py teste
  python zairyx/bot.py teste-live
  python zairyx/bot.py
"""

import asyncio
import logging
import os
import re
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.engine import SignalHubEngine
from core.sources import DorkScanner

BOT_DIR = Path(__file__).parent
ROOT_DIR = BOT_DIR.parent
CONFIG_PATH = ROOT_DIR / "config" / "zairyx" / "keywords.yaml"
DORKS_PATH = ROOT_DIR / "config" / "zairyx" / "dorks.yaml"
ENV_PATH = BOT_DIR / ".env"
LOG_PATH = ROOT_DIR / "logs" / "zairyx.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ZAIRYX] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
log = logging.getLogger("zairyxbot")

env = {**os.environ, **dotenv_values(ENV_PATH)}
engine = SignalHubEngine(CONFIG_PATH, env, log)

POSTS_MOCK = [
    {
        "autor": "João D.",
        "texto": "Comissão ifood alta destruindo margem. Tenho motoboy próprio. Como montar canal próprio whatsapp?",
        "link": "https://reddit.com/r/restaurantes/mock-zai-001",
    },
    {
        "autor": "Fernanda O.",
        "texto": "Não apareço no maps. Google meu negócio cadastrar não valida código.",
        "link": "https://reddit.com/r/restaurantes/mock-zai-002",
    },
    {
        "autor": "Silvia T.",
        "texto": "Alguém vende embalagem de pizza no atacado?",
        "link": "https://reddit.com/r/restaurantes/mock-zai-003",
    },
]


async def detectar_chat_id():
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.error("TELEGRAM_BOT_TOKEN ausente em zairyx/.env")
        return

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://api.telegram.org/bot{token}/getMe")
        user = r.json().get("result", {}).get("username", "?")

    log.info(f"Bot: @{user} — https://t.me/{user}")
    log.info("Envie /start no Telegram agora (90s)...")

    offset = 0
    deadline = time.time() + 90

    async with httpx.AsyncClient(timeout=15) as c:
        while time.time() < deadline:
            try:
                r = await c.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset": offset, "timeout": 5},
                )
                for upd in r.json().get("result", []):
                    offset = upd["update_id"] + 1
                    chat_id = upd.get("message", {}).get("chat", {}).get("id")
                    if chat_id:
                        txt = ENV_PATH.read_text(encoding="utf-8")
                        if "TELEGRAM_CHAT_ID=" in txt:
                            txt = re.sub(
                                r"TELEGRAM_CHAT_ID=.*",
                                f"TELEGRAM_CHAT_ID={chat_id}",
                                txt,
                            )
                        else:
                            txt += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
                        ENV_PATH.write_text(txt, encoding="utf-8")
                        env["TELEGRAM_CHAT_ID"] = str(chat_id)
                        log.info(f"zairyx/.env → TELEGRAM_CHAT_ID={chat_id}")
                        await c.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "🚀 ZairyxBot conectado! Alertas Delivery ativos.",
                            },
                        )
                        return chat_id
            except Exception as e:
                log.error(f"Polling: {e}")
            await asyncio.sleep(2)

    log.warning("Timeout — envie /start em https://t.me/tiago_a_rocha_alertas_zai_bot")


def _scanner() -> DorkScanner:
    return DorkScanner(DORKS_PATH)


async def scan_loop():
    interval = int(env.get("SCAN_INTERVAL_SECONDS", 300))
    scanner = _scanner()
    log.info(f"ZairyxBot produção — dorks multi-fonte a cada {interval}s")

    while True:
        posts = await scanner.scan()
        log.info(f"Varredura: {len(posts)} oportunidades")
        for post in posts:
            await engine.processar(post)
            await asyncio.sleep(0.5)
        await asyncio.sleep(interval)


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "detectar":
        await detectar_chat_id()
    elif cmd == "teste":
        log.info("Teste mock — dry-run")
        for post in POSTS_MOCK:
            await engine.processar(post, dry_run=True)
    elif cmd == "teste-live":
        if not env.get("TELEGRAM_CHAT_ID"):
            log.error("Configure TELEGRAM_CHAT_ID (rode: python zairyx/bot.py detectar)")
            return
        log.info("Teste mock — envia Telegram")
        for post in POSTS_MOCK:
            await engine.processar(post)
    elif cmd in ("scan", "dork", "dorks"):
        posts = await _scanner().scan()
        log.info(f"Dork scan: {len(posts)} resultados")
        for p in posts[:10]:
            s, g = engine.score(p["texto"])
            log.info(f"  [{p.get('fonte','?')}] score={s} grupo={g} | {p['texto'][:70]}")
    else:
        if not env.get("TELEGRAM_CHAT_ID"):
            log.error("TELEGRAM_CHAT_ID vazio. Rode: python zairyx/bot.py detectar")
            return
        await scan_loop()


if __name__ == "__main__":
    asyncio.run(main())
