"""User-facing errors — technical details hide."""

import logging

from app.utils.language import get_reply_language, msg

logger = logging.getLogger(__name__)


def to_user_message(exc: Exception) -> str:
    logger.exception("Chat error: %s", exc)
    text = str(exc).lower()
    if "permission" in text or "access" in text:
        return str(exc)
    if "jwt" in text or "token" in text or "context" in text:
        return msg("session_expired")
    if "database" in text or "db_" in text or "pymssql" in text:
        return msg("db_error")
    return msg("generic_error")
