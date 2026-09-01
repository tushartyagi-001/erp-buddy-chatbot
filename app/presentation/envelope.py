from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import ToolMessage

from app.presentation.payloads import FMT_MARKER, html_payload, text_payload


def format_service_result(func_name: str, data: dict[str, Any]) -> str:
    from app.presentation.formatters import FORMATTERS, format_generic

    if data.get("allowed") is False:
        return json.dumps(text_payload(data.get("message") or "Access denied."), ensure_ascii=False)

    formatter = FORMATTERS.get(func_name, format_generic)
    payload = formatter(data)
    if isinstance(payload, str):
        return json.dumps(text_payload(payload), ensure_ascii=False)
    return json.dumps(payload, ensure_ascii=False, default=str)


def _parse_tool_content(content: str) -> dict | None:
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(data, dict) and data.get(FMT_MARKER):
        return data
    return None


def extract_formatted_from_messages(messages: list) -> dict[str, Any] | None:
    html_parts: list[str] = []
    text_parts: list[str] = []
    options: list[dict] = []
    attachments: list[dict] = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        parsed = _parse_tool_content(str(message.content))
        if not parsed:
            continue
        if parsed.get("reply_type") == "html":
            html_parts.append(parsed.get("content") or "")
        else:
            text_parts.append(parsed.get("content") or "")
        for opt in parsed.get("options") or []:
            if isinstance(opt, dict) and opt.get("student_reg_no"):
                options.append(opt)
        for att in parsed.get("attachments") or []:
            if isinstance(att, dict) and att.get("file_id"):
                attachments.append(att)

    if not html_parts and not text_parts:
        return None

    if html_parts:
        return {
            "reply": "".join(html_parts),
            "reply_type": "html",
            "options": options or None,
            "attachments": attachments or None,
        }

    return {
        "reply": "\n\n".join(text_parts),
        "reply_type": "text",
        "options": options or None,
        "attachments": attachments or None,
    }
