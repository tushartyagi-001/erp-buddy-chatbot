"""Daily chat limit — local SQLite (ERP DB par write nahi)."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from app.config import settings

_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = _DB_DIR / "chat_usage.sqlite"


def _connect() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_usage (
            usage_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            branch_id INTEGER NOT NULL,
            chat_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (usage_date, user_id, branch_id)
        )
        """
    )
    return conn


def check_and_record(user_id: int, branch_id: int) -> tuple[bool, int, int]:
    """
    Returns (allowed, used_count, daily_limit).
    Super admin (role_id <= 1) — unlimited.
    """
    limit = settings.CHAT_DAILY_LIMIT
    if limit <= 0:
        return True, 0, limit

    today = date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT chat_count FROM chat_usage WHERE usage_date=? AND user_id=? AND branch_id=?",
            (today, user_id, branch_id),
        ).fetchone()
        used = int(row[0]) if row else 0
        if used >= limit:
            return False, used, limit
        if row:
            conn.execute(
                "UPDATE chat_usage SET chat_count = chat_count + 1 WHERE usage_date=? AND user_id=? AND branch_id=?",
                (today, user_id, branch_id),
            )
        else:
            conn.execute(
                "INSERT INTO chat_usage (usage_date, user_id, branch_id, chat_count) VALUES (?, ?, ?, 1)",
                (today, user_id, branch_id),
            )
        conn.commit()
        return True, used + 1, limit


def remaining_today(user_id: int, branch_id: int) -> int:
    limit = settings.CHAT_DAILY_LIMIT
    if limit <= 0:
        return limit
    today = date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT chat_count FROM chat_usage WHERE usage_date=? AND user_id=? AND branch_id=?",
            (today, user_id, branch_id),
        ).fetchone()
        used = int(row[0]) if row else 0
        return max(0, limit - used)


def get_usage(user_id: int, branch_id: int, usage_date: str | None = None) -> dict:
    """Current usage for one user + branch (default: today)."""
    limit = settings.CHAT_DAILY_LIMIT
    day = usage_date or date.today().isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT chat_count FROM chat_usage WHERE usage_date=? AND user_id=? AND branch_id=?",
            (day, user_id, branch_id),
        ).fetchone()
        used = int(row[0]) if row else 0
    remaining = max(0, limit - used) if limit > 0 else limit
    return {
        "usage_date": day,
        "user_id": user_id,
        "branch_id": branch_id,
        "used": used,
        "limit": limit,
        "remaining": remaining,
    }


def reset_usage(
    *,
    user_id: int | None = None,
    branch_id: int | None = None,
    usage_date: str | None = None,
    all_dates: bool = False,
) -> int:
    """
    Reset chat usage counters.

    - user_id + branch_id + date: one user/branch for that day
    - branch_id only + date: all users in branch for that day
    - all_dates=True: ignore date filter (full reset for given user/branch or branch or all)
    - no filters + all_dates: wipe entire chat_usage table

    Returns number of rows deleted.
    """
    day = usage_date or date.today().isoformat()
    clauses: list[str] = []
    params: list[object] = []

    if not all_dates:
        clauses.append("usage_date=?")
        params.append(day)

    if user_id is not None:
        clauses.append("user_id=?")
        params.append(user_id)
    if branch_id is not None:
        clauses.append("branch_id=?")
        params.append(branch_id)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"DELETE FROM chat_usage{where}"

    with _connect() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return int(cur.rowcount)
