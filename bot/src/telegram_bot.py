"""Camada 4 — envio Telegram."""

from __future__ import annotations

import logging

import httpx

from src.retry import retry_call
from src.telegram_alert import AlertPayload

logger = logging.getLogger(__name__)


class TelegramNotifier:
    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_alert(self, alert: AlertPayload) -> bool:
        url = f"{self.API_BASE.format(token=self.bot_token)}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": alert.format_message(),
            "disable_web_page_preview": False,
            "reply_markup": {"inline_keyboard": alert.inline_keyboard()},
        }

        def _send() -> bool:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
            return True

        try:
            return retry_call(_send, exceptions=(httpx.HTTPError,), label="telegram.sendMessage")
        except httpx.HTTPError as exc:
            logger.error("Telegram send failed após retries: %s", exc)
            return False

    def send_text(self, text: str) -> bool:
        url = f"{self.API_BASE.format(token=self.bot_token)}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}

        def _send() -> bool:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
            return True

        try:
            return retry_call(_send, exceptions=(httpx.HTTPError,), label="telegram.sendText")
        except httpx.HTTPError as exc:
            logger.error("Telegram send_text failed: %s", exc)
            return False
