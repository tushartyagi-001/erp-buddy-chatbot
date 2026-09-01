from __future__ import annotations

import json

from langchain_core.tools import tool

from app.services.exam_service import get_exam_result_detail, list_student_exam_results
from app.tools.common import run_tool
from app.tools.student.tools import get_selected_student


@tool
def get_student_exam_results_tool(student_reg_no: int = 0) -> str:
    """List student exam results."""
    reg_no = student_reg_no or get_selected_student() or 0
    if not reg_no:
        from app.presentation.payloads import text_payload
        from app.utils.language import msg

        return json.dumps(text_payload(msg("select_student")), ensure_ascii=False)
    return run_tool(list_student_exam_results, student_reg_no=int(reg_no))


@tool
def get_exam_result_detail_tool(exam_plan_id: int, student_reg_no: int = 0) -> str:
    """Exam subject-wise result detail."""
    reg_no = student_reg_no or get_selected_student() or 0
    if not reg_no:
        from app.presentation.payloads import text_payload
        from app.utils.language import msg

        return json.dumps(text_payload(msg("select_student")), ensure_ascii=False)
    return run_tool(
        get_exam_result_detail,
        exam_plan_id=int(exam_plan_id),
        student_reg_no=int(reg_no),
    )


TOOLS = [get_student_exam_results_tool, get_exam_result_detail_tool]
