from __future__ import annotations

import json
from contextvars import ContextVar

from langchain_core.tools import tool

from app.tools.common import run_tool
from app.services.student_service import get_student_profile, search_students

_selected_student: ContextVar[int | None] = ContextVar("selected_student", default=None)


def set_selected_student(student_reg_no: int | None) -> None:
    _selected_student.set(student_reg_no)


def get_selected_student() -> int | None:
    return _selected_student.get()


@tool
def search_students_tool(name_or_term: str) -> str:
    """Search students by name, mobile, roll, or reg no."""
    return run_tool(search_students, term=name_or_term, limit=10)


@tool
def get_student_profile_tool(student_reg_no: int) -> str:
    """Get safe student profile."""
    return run_tool(get_student_profile, student_reg_no=student_reg_no)


@tool
def select_student_tool(student_reg_no: int) -> str:
    """Set active student for this chat session."""
    set_selected_student(int(student_reg_no))
    profile_json = run_tool(get_student_profile, student_reg_no=int(student_reg_no))

    try:
        payload = json.loads(profile_json)
    except json.JSONDecodeError:
        set_selected_student(None)
        return profile_json

    if payload.get("allowed") is False:
        set_selected_student(None)
        return profile_json

    content = payload.get("content") or ""
    if "not found" in content.lower():
        set_selected_student(None)
        return profile_json

    intro = '<div class="erp-note">Student selected. You can ask about fees, attendance, or profile.</div>'
    if payload.get("reply_type") == "html":
        return json.dumps(
            {
                "__erp_buddy_fmt__": True,
                "reply_type": "html",
                "content": intro + content,
            },
            ensure_ascii=False,
        )
    return profile_json


TOOLS = [
    search_students_tool,
    get_student_profile_tool,
    select_student_tool,
]
