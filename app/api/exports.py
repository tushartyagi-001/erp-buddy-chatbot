from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.chat import get_context
from app.auth.context import ChatContext
from app.services.export_store import get_export

router = APIRouter(prefix="/api/exports", tags=["Exports"])


@router.get("/{file_id}")
def download_export(file_id: str, ctx: ChatContext = Depends(get_context)):
    record = get_export(file_id, ctx.branch_id, ctx.user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Export not found or expired")
    return FileResponse(
        path=record.path,
        filename=record.filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
