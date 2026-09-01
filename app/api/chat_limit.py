from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.chat import get_context
from app.api.schemas import ChatLimitResetRequest, ChatLimitResetResponse, ChatLimitStatusResponse
from app.auth.context import ChatContext
from app.config import settings
from app.services.chat_limit import get_usage, reset_usage

router = APIRouter(prefix="/api/chat-limit", tags=["Chat Limit"])


def require_limit_admin(
    ctx: ChatContext = Depends(get_context),
    x_chat_limit_key: str = Header(default="", alias="X-Chat-Limit-Key"),
) -> ChatContext:
    admin_key = (settings.CHAT_LIMIT_ADMIN_KEY or "").strip()
    if admin_key and x_chat_limit_key.strip() == admin_key:
        return ctx
    if ctx.is_super_admin:
        return ctx
    raise HTTPException(
        status_code=403,
        detail="Super admin login or valid X-Chat-Limit-Key required",
    )


@router.get("/status", response_model=ChatLimitStatusResponse)
def chat_limit_status(
    user_id: int | None = None,
    branch_id: int | None = None,
    usage_date: str | None = None,
    ctx: ChatContext = Depends(require_limit_admin),
):
    uid = user_id if user_id is not None else ctx.user_id
    bid = branch_id if branch_id is not None else ctx.branch_id
    return get_usage(uid, bid, usage_date)


@router.post("/reset", response_model=ChatLimitResetResponse)
def chat_limit_reset(
    body: ChatLimitResetRequest,
    ctx: ChatContext = Depends(require_limit_admin),
):
    scope = (body.scope or "user").strip().lower()
    if scope not in {"user", "branch", "all"}:
        raise HTTPException(status_code=400, detail="scope must be user, branch, or all")

    user_id: int | None = body.user_id
    branch_id: int | None = body.branch_id

    if scope == "user":
        user_id = user_id if user_id is not None else ctx.user_id
        branch_id = branch_id if branch_id is not None else ctx.branch_id
    elif scope == "branch":
        branch_id = branch_id if branch_id is not None else ctx.branch_id
        user_id = None
    else:
        user_id = None
        branch_id = None

    rows = reset_usage(
        user_id=user_id,
        branch_id=branch_id,
        usage_date=body.usage_date,
        all_dates=body.all_dates,
    )

    if scope == "user":
        msg = f"Reset chat limit for user {user_id} branch {branch_id}"
    elif scope == "branch":
        msg = f"Reset chat limits for branch {branch_id}"
    else:
        msg = "Reset all chat usage records"

    if body.all_dates:
        msg += " (all dates)"
    elif body.usage_date:
        msg += f" (date {body.usage_date})"
    else:
        msg += " (today)"

    return ChatLimitResetResponse(
        success=True,
        scope=scope,
        rows_deleted=rows,
        message=msg,
    )
