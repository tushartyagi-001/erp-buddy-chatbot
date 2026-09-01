from __future__ import annotations

import jwt

from app.auth.context import ChatContext
from app.config import settings


def context_from_token(token: str) -> ChatContext:
    if not settings.JWT_SECRET:
        raise RuntimeError("JWT_SECRET not configured")

    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=["HS256"],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
    )

    def _int(key: str, default: int = 0) -> int:
        val = payload.get(key, default)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    return ChatContext(
        user_id=_int("ADID"),
        role_id=_int("RoleID"),
        branch_id=_int("Brid"),
        org_id=_int("OrgId"),
        fy_id=_int("Fyid"),
        branch_collection=str(payload.get("BridCollection") or ""),
        is_head_branch=str(payload.get("IsHeadBranch") or "0") in ("1", "True", "true"),
        user_name=str(payload.get("UserName") or payload.get("sub") or ""),
    )
