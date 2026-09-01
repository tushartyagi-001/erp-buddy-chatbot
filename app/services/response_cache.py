from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

from app.config import settings

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "response_cache.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_cache (
            cache_key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
        """
    )
    return conn


def _cleanup(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM response_cache WHERE expires_at <= ?", (time.time(),))
    conn.commit()


def make_cache_key(
    *,
    branch_id: int,
    user_id: int,
    route: str,
    message: str,
    selected_student_reg_no: int | None,
) -> str:
    raw = json.dumps(
        {
            "branch_id": branch_id,
            "user_id": user_id,
            "route": route,
            "message": message.strip().lower(),
            "student": selected_student_reg_no or 0,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(cache_key: str) -> dict | None:
    ttl = max(settings.RESPONSE_CACHE_TTL_SECONDS, 0)
    if ttl <= 0:
        return None
    with _connect() as conn:
        _cleanup(conn)
        row = conn.execute(
            "SELECT payload, expires_at FROM response_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        payload, expires_at = row
        if expires_at <= time.time():
            conn.execute("DELETE FROM response_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            return None
        return json.loads(payload)


def set_cached(cache_key: str, response: dict) -> None:
    ttl = max(settings.RESPONSE_CACHE_TTL_SECONDS, 0)
    if ttl <= 0:
        return
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO response_cache(cache_key, payload, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload = excluded.payload,
                expires_at = excluded.expires_at
            """,
            (cache_key, json.dumps(response, ensure_ascii=False), time.time() + ttl),
        )
        conn.commit()
