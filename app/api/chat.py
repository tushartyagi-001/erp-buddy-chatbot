from fastapi import APIRouter, Depends, Header, HTTPException

from app.agent.agent_service import run_chat
from app.api.schemas import ChatRequest, ChatResponse, FileAttachment
from app.auth.context import ChatContext
from app.auth.jwt_validator import context_from_token
from app.services.chat_limit import check_and_record
from app.utils.language import detect_language, msg as lang_msg, set_reply_language
from app.utils.user_errors import to_user_message

router = APIRouter(prefix="/api", tags=["Chat"])


def get_context(authorization: str = Header(default="")) -> ChatContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required")
    token = authorization[7:].strip()
    try:
        return context_from_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid session") from e


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest, ctx: ChatContext = Depends(get_context)):
    if not ctx.is_super_admin:
        allowed, used, limit = check_and_record(ctx.user_id, ctx.branch_id)
        if not allowed:
            set_reply_language(detect_language(body.message))
            return ChatResponse(
                reply=lang_msg("chat_limit", used=str(used), limit=str(limit))
            )

    set_reply_language(detect_language(body.message))

    try:
        result = run_chat(
            ctx,
            body.message,
            history=[m.model_dump() for m in body.history],
            selected_student_reg_no=body.selected_student_reg_no,
        )
        attachments = None
        if result.get("attachments"):
            attachments = [
                FileAttachment(
                    file_id=a["file_id"],
                    filename=a["filename"],
                    label=a.get("label") or f"Download {a['filename']}",
                    download_url=f"/ChatBridge/DownloadExport?id={a['file_id']}",
                )
                for a in result["attachments"]
            ]
        return ChatResponse(
            reply=result["reply"],
            reply_type=result.get("reply_type") or "text",
            options=result.get("options"),
            attachments=attachments,
        )
    except Exception as e:
        return ChatResponse(reply=to_user_message(e))
