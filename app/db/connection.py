"""
READ ONLY database access — sirf EXEC stored procedures.
"""

from __future__ import annotations

from contextlib import contextmanager

import pymssql

from app.config import settings


def _connect():
    if not all([settings.DB_SERVER, settings.DB_NAME, settings.DB_USER, settings.DB_PASSWORD]):
        raise RuntimeError("Database credentials not configured")
    return pymssql.connect(
        server=settings.DB_SERVER,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        as_dict=True,
    )


@contextmanager
def get_connection():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def exec_sp(proc_name: str, params: tuple = ()) -> list[dict]:
    """Stored procedure execute karo — READ ONLY."""
    placeholders = ", ".join(["%s"] * len(params))
    sql = f"EXEC {proc_name} {placeholders}" if params else f"EXEC {proc_name}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return list(rows or [])


def exec_sp_result_sets(proc_name: str, params: tuple = ()) -> list[list[dict]]:
    """Multi result-set SP — e.g. USP_GetNewExamResult."""
    placeholders = ", ".join(["%s"] * len(params))
    sql = f"EXEC {proc_name} {placeholders}" if params else f"EXEC {proc_name}"
    sets: list[list[dict]] = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            while True:
                sets.append(list(cur.fetchall() or []))
                if not cur.nextset():
                    break
    return sets


def exec_readonly_query(sql: str, params: tuple = ()) -> list[dict]:
    """Whitelisted read-only SELECT queries only."""
    normalized = " ".join(sql.strip().split()).upper()
    if not normalized.startswith("SELECT"):
        raise RuntimeError("Only SELECT queries allowed")
    blocked = ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "EXEC ", "TRUNCATE ")
    if any(token in normalized for token in blocked):
        raise RuntimeError("Unsafe query blocked")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall() or [])


def exec_sp_scalar(proc_name: str, params: tuple = ()):
    rows = exec_sp(proc_name, params)
    if not rows:
        return None
    first = rows[0]
    if isinstance(first, dict):
        return next(iter(first.values()))
    return first
