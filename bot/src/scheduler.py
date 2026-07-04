"""Scheduler — loop a cada N minutos + callbacks Telegram + watchdog."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from src.config_loader import ROOT_DIR
from src.pipeline import SignalPipeline
from src.telegram_callback import TelegramCallbackPoller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_last_cycle_at: float | None = None
_watchdog_notified = False


def main() -> None:
    global _last_cycle_at, _watchdog_notified

    load_dotenv(ROOT_DIR / ".env")
    interval = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))
    watchdog_minutes = int(os.getenv("WATCHDOG_MINUTES", "70"))
    pipeline = SignalPipeline()

    callback_poller: TelegramCallbackPoller | None = None
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        callback_poller = TelegramCallbackPoller(token, chat_id, pipeline.deduper)
        callback_poller.start()

    def job() -> None:
        global _last_cycle_at, _watchdog_notified
        try:
            alerts = pipeline.run_cycle()
            _last_cycle_at = time.time()
            _watchdog_notified = False
            logger.info("Ciclo concluído: %d alertas", len(alerts))
        except Exception:
            logger.exception("Erro no ciclo")

    def watchdog() -> None:
        global _watchdog_notified
        if _last_cycle_at is None or _watchdog_notified:
            return
        elapsed_min = (time.time() - _last_cycle_at) / 60
        if elapsed_min < watchdog_minutes:
            return
        if pipeline.telegram:
            ts = datetime.fromtimestamp(_last_cycle_at, tz=timezone.utc).strftime("%H:%M UTC")
            pipeline.telegram.send_text(
                f"⚠️ SignalHub: sem ciclo bem-sucedido há {int(elapsed_min)} min "
                f"(último OK: {ts}). Verifique PM2/logs."
            )
            _watchdog_notified = True
            logger.warning("Watchdog: alerta enviado após %d min sem ciclo OK", int(elapsed_min))

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", minutes=interval, id="signalhub_poll")
    scheduler.add_job(watchdog, "interval", minutes=10, id="signalhub_watchdog")
    logger.info("SignalHub rodando — poll a cada %d min", interval)
    job()
    scheduler.start()


if __name__ == "__main__":
    main()
