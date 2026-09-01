from __future__ import annotations

import json
import re
from typing import Any

from app.presentation.payloads import FMT_MARKER


def parse_tool_payload(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or not data.get(FMT_MARKER):
        return None
    return {
        "reply": data.get("content") or "",
        "reply_type": data.get("reply_type") or "text",
        "options": data.get("options"),
        "attachments": data.get("attachments"),
        "_meta": data.get("_meta"),
    }


def merge_responses(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    if primary.get("reply_type") == "html" and secondary.get("reply_type") == "html":
        reply = (primary.get("reply") or "") + (secondary.get("reply") or "")
    else:
        reply = "\n\n".join(
            part for part in [primary.get("reply"), secondary.get("reply")] if part
        )
    options = (primary.get("options") or []) + (secondary.get("options") or [])
    attachments = (primary.get("attachments") or []) + (secondary.get("attachments") or [])
    return {
        "reply": reply,
        "reply_type": primary.get("reply_type") or secondary.get("reply_type") or "text",
        "options": options or None,
        "attachments": attachments or None,
        "_meta": primary.get("_meta") or secondary.get("_meta"),
    }


def extract_student_name(message: str) -> str | None:
    text = (message or "").strip()
    patterns = [
        r"(?:fee|attendance|profile|result|receipt|installment|overdue|ledger|status|summary|detail|information|info)\s+(?:of|for)\s+(.+?)(?:[\?\.!,]|$)",
        r"(?:about|regarding)\s+(.+?)(?:[\?\.!,]|$)",
        r"(?:student|tell me about)\s+(.+?)(?:[\?\.!,]|$)",
        r"^(.+?)\s+(?:fee|attendance|profile|result)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = match.group(1).strip(" '\"")
            name = re.sub(r"\b(fee|status|summary|student|please|show|tell|give|me)\b", "", name, flags=re.I)
            name = " ".join(name.split())
            if len(name) >= 2:
                return name
    return None


_SEARCH_COMMAND_WORDS = re.compile(
    r"\b(search|find|show|list|student|students|please|help|me|a|an|the|for|by|name|karo|karein|dikhao|batao|bataiye)\b",
    re.I,
)


def extract_student_search_term(message: str) -> str | None:
    """Return a real search term, or None when the message is only a search command."""
    text = (message or "").strip()
    if not text:
        return None

    name = extract_student_name(text)
    if name:
        return name

    cleaned = _SEARCH_COMMAND_WORDS.sub(" ", text)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) >= 2:
        return cleaned
    return None


def normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", (message or "").strip().lower())


SELECT_STUDENT_PREFIX = "__select_student__:"


def parse_student_selection(message: str, selected_student_reg_no: int | None = None) -> int | None:
    text = (message or "").strip()
    if text.startswith(SELECT_STUDENT_PREFIX):
        try:
            return int(text[len(SELECT_STUDENT_PREFIX) :].strip())
        except ValueError:
            return None
    if selected_student_reg_no and text.lower().startswith("i'm asking about this student"):
        return int(selected_student_reg_no)
    return None


def try_student_selection(message: str, selected_student_reg_no: int | None = None) -> dict[str, Any] | None:
    reg_no = parse_student_selection(message, selected_student_reg_no)
    if not reg_no:
        return None

    from app.tools.student.tools import select_student_tool, set_selected_student

    set_selected_student(reg_no)
    raw = select_student_tool.invoke({"student_reg_no": reg_no})
    parsed = parse_tool_payload(raw if isinstance(raw, str) else str(raw))
    if not parsed:
        return None
    parsed["_meta"] = {"route": "select_student", "ai_used": False, "student_reg_no": reg_no}
    return parsed
