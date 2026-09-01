from __future__ import annotations

from app.auth.context import get_chat_context
from app.permissions.checker import PermissionDenied
from app.presentation.envelope import format_service_result


def run_tool(func, **kwargs) -> str:
    ctx = get_chat_context()
    try:
        result = func(ctx, **kwargs)
        return format_service_result(func.__name__, result)
    except PermissionDenied as e:
        return format_service_result("", {"allowed": False, "message": e.user_message})
