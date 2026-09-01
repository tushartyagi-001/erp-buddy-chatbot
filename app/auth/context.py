from __future__ import annotations

from dataclasses import dataclass
from contextvars import ContextVar

_current_context: ContextVar["ChatContext | None"] = ContextVar("chat_context", default=None)


@dataclass(frozen=True)
class ChatContext:
    user_id: int
    role_id: int
    branch_id: int
    org_id: int
    fy_id: int
    branch_collection: str
    is_head_branch: bool
    user_name: str = ""

    @property
    def is_super_admin(self) -> bool:
        return self.role_id <= 1

    @property
    def allowed_branch_ids(self) -> set[int]:
        ids = {self.branch_id}
        if self.branch_collection:
            for part in self.branch_collection.split(","):
                part = part.strip()
                if part.isdigit():
                    ids.add(int(part))
        return ids


def set_chat_context(ctx: ChatContext) -> None:
    _current_context.set(ctx)


def get_chat_context() -> ChatContext:
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError("Chat context missing")
    return ctx
