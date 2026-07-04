"""Handler de callbacks inline — polling Telegram em background."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import httpx

from src.retry import retry_call

if TYPE_CHECKING:
    from src.deduper import Deduper

logger = logging.getLogger(__name__)


class TelegramCallbackPoller:
    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str, chat_id: str, deduper: Deduper) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.deduper = deduper
        self._offset = 0
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="tg-callbacks")
        self._thread.start()
        logger.info("Callback poller Telegram iniciado")

    def stop(self) -> None:
        self._stop.set()

    def _api(self, method: str, payload: dict) -> dict:
        url = f"{self.API_BASE.format(token=self.bot_token)}/{method}"

        def _post() -> dict:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()

        return retry_call(_post, exceptions=(httpx.HTTPError,), label=f"telegram.{method}")

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            try:
                data = self._get_updates()
                for update in data.get("result", []):
                    self._offset = update["update_id"] + 1
                    self._handle_update(update)
            except httpx.HTTPError as exc:
                logger.error("Polling Telegram falhou: %s", exc)
                self._stop.wait(5)

    def _get_updates(self) -> dict:
        url = f"{self.API_BASE.format(token=self.bot_token)}/getUpdates"
        payload = {
            "offset": self._offset,
            "timeout": 25,
            "allowed_updates": ["callback_query"],
        }

        def _fetch() -> dict:
            with httpx.Client(timeout=35.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()

        return retry_call(_fetch, exceptions=(httpx.HTTPError,), label="telegram.getUpdates")

    def _handle_update(self, update: dict) -> None:
        query = update.get("callback_query")
        if not query:
            return

        data = query.get("data", "")
        query_id = query["id"]
        message = query.get("message") or {}
        chat_id = str((message.get("chat") or {}).get("id", ""))

        if chat_id and chat_id != str(self.chat_id):
            self._api("answerCallbackQuery", {"callback_query_id": query_id, "text": "Chat não autorizado"})
            return

        if data.startswith("approve:"):
            self._handle_approve(query_id, data, message)
        elif data.startswith("discard:"):
            self._handle_discard(query_id, data, message)
        else:
            self._api("answerCallbackQuery", {"callback_query_id": query_id, "text": "Ação desconhecida"})

    def _handle_approve(self, query_id: str, data: str, message: dict) -> None:
        parts = data.split(":", 2)
        if len(parts) != 3:
            return
        _, variant, uid = parts
        pending = self.deduper.get_pending_responses(uid)
        if not pending:
            self._api(
                "answerCallbackQuery",
                {"callback_query_id": query_id, "text": "Alerta expirado — copie do texto acima"},
            )
            return

        response_text = pending.get(variant, "")
        if not response_text:
            self._api("answerCallbackQuery", {"callback_query_id": query_id, "text": "Resposta inválida"})
            return

        self.deduper.update_alert_status(pending["url"], "aprovado")
        self._api("answerCallbackQuery", {"callback_query_id": query_id, "text": f"✅ {variant.upper()} selecionada"})
        self._api(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": (
                    f"📋 Resposta {variant.upper()} — copie e cole no post:\n\n"
                    f"{response_text}\n\n"
                    f"🔗 {pending['url']}"
                ),
            },
        )
        self._edit_message_status(message, f"✅ Aprovado ({variant.upper()})")

    def _handle_discard(self, query_id: str, data: str, message: dict) -> None:
        parts = data.split(":", 1)
        if len(parts) != 2:
            return
        _, uid = parts
        pending = self.deduper.get_pending_responses(uid)
        if pending:
            self.deduper.update_alert_status(pending["url"], "descartado")
        self._api("answerCallbackQuery", {"callback_query_id": query_id, "text": "❌ Descartado"})
        self._edit_message_status(message, "❌ Descartado")

    def _edit_message_status(self, message: dict, status: str) -> None:
        chat = message.get("chat", {}).get("id")
        msg_id = message.get("message_id")
        text = message.get("text", "")
        if not chat or not msg_id or not text:
            return
        if status in text:
            return
        new_text = f"{text}\n\n──────────\n{status}"[:4090]
        self._api(
            "editMessageText",
            {
                "chat_id": chat,
                "message_id": msg_id,
                "text": new_text,
                "reply_markup": {"inline_keyboard": []},
            },
        )
