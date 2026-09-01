from __future__ import annotations

from typing import Any

FMT_MARKER = "__erp_buddy_fmt__"


def html_payload(content: str, options: list[dict] | None = None, attachments: list[dict] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        FMT_MARKER: True,
        "reply_type": "html",
        "content": content,
    }
    if options:
        payload["options"] = options
    if attachments:
        payload["attachments"] = attachments
    return payload


def text_payload(content: str) -> dict[str, Any]:
    return {FMT_MARKER: True, "reply_type": "text", "content": content}
