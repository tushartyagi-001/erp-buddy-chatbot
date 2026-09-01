from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from pathlib import Path

EXPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "exports"
TTL_SECONDS = 60 * 60  # 1 hour


@dataclass
class ExportRecord:
    file_id: str
    path: Path
    filename: str
    branch_id: int
    user_id: int
    created_at: float


_records: dict[str, ExportRecord] = {}


def _cleanup() -> None:
    now = time.time()
    expired = [fid for fid, rec in _records.items() if now - rec.created_at > TTL_SECONDS]
    for fid in expired:
        rec = _records.pop(fid, None)
        if rec and rec.path.exists():
            rec.path.unlink(missing_ok=True)


def register_export(branch_id: int, user_id: int, path: Path, filename: str) -> str:
    _cleanup()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_id = secrets.token_urlsafe(12)
    _records[file_id] = ExportRecord(
        file_id=file_id,
        path=path,
        filename=filename,
        branch_id=branch_id,
        user_id=user_id,
        created_at=time.time(),
    )
    return file_id


def get_export(file_id: str, branch_id: int, user_id: int) -> ExportRecord | None:
    _cleanup()
    rec = _records.get(file_id)
    if not rec:
        return None
    if rec.branch_id != branch_id or rec.user_id != user_id:
        return None
    if not rec.path.exists():
        _records.pop(file_id, None)
        return None
    return rec
