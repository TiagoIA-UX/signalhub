"""Camada 1 — deduplicação por URL (SQLite)."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


class Deduper:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    seen_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    tenant TEXT,
                    tema TEXT,
                    score INTEGER,
                    status TEXT DEFAULT 'pendente',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_alerts (
                    day TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_responses (
                    callback_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    r1 TEXT NOT NULL,
                    r2 TEXT NOT NULL,
                    r3 TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

    @staticmethod
    def hash_url(url: str) -> str:
        return hashlib.sha256(url.strip().lower().encode()).hexdigest()

    def is_seen(self, url: str) -> bool:
        url_hash = self.hash_url(url)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen WHERE url_hash = ?", (url_hash,)
            ).fetchone()
        return row is not None

    def mark_seen(self, url: str) -> None:
        url_hash = self.hash_url(url)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen (url_hash, url) VALUES (?, ?)",
                (url_hash, url),
            )

    def save_pending_responses(
        self,
        callback_id: str,
        url: str,
        r1: str,
        r2: str,
        r3: str,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pending_responses (callback_id, url, r1, r2, r3)
                VALUES (?, ?, ?, ?, ?)
                """,
                (callback_id, url, r1, r2, r3),
            )

    def get_pending_responses(self, callback_id: str) -> dict[str, str] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT url, r1, r2, r3 FROM pending_responses WHERE callback_id = ?",
                (callback_id,),
            ).fetchone()
        if not row:
            return None
        return {"url": row[0], "r1": row[1], "r2": row[2], "r3": row[3]}

    def update_alert_status(self, url: str, status: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE alert_log SET status = ?
                WHERE id = (
                    SELECT id FROM alert_log WHERE url = ? ORDER BY id DESC LIMIT 1
                )
                """,
                (status, url),
            )

    def log_alert(
        self,
        url: str,
        tenant: str,
        tema: str,
        score: int,
        status: str = "pendente",
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO alert_log (url, tenant, tema, score, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, tenant, tema, score, status),
            )

    def alerts_today(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT count FROM daily_alerts WHERE day = date('now')"
            ).fetchone()
        return row[0] if row else 0

    def increment_daily_alerts(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO daily_alerts (day, count) VALUES (date('now'), 1)
                ON CONFLICT(day) DO UPDATE SET count = count + 1
                """
            )
            row = conn.execute(
                "SELECT count FROM daily_alerts WHERE day = date('now')"
            ).fetchone()
        return row[0] if row else 0

    def can_send_alert(self, max_per_day: int) -> bool:
        return self.alerts_today() < max_per_day
