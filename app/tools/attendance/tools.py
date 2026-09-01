from __future__ import annotations

import json

from langchain_core.tools import tool

from app.services.attendance_service import get_student_attendance
from app.tools.common import run_tool
from app.tools.student.tools import get_selected_student


@tool
def get_student_attendance_tool(student_reg_no: int = 0) -> str:
    """Student attendance summary and recent days."""
    reg_no = student_reg_no or get_selected_student() or 0
    if not reg_no:
        from app.presentation.payloads import text_payload
        from app.utils.language import msg

        return json.dumps(text_payload(msg("select_student")), ensure_ascii=False)
    return run_tool(get_student_attendance, student_reg_no=int(reg_no))


TOOLS = [get_student_attendance_tool]
