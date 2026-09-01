from __future__ import annotations

from app.auth.context import ChatContext
from app.db.connection import exec_sp
from app.permissions.checker import require_menu_permission
from app.permissions.menu_urls import MENU_STUDENT_LIST
from app.routing.helpers import extract_student_search_term
from app.utils.language import get_reply_language, msg


def _mask_mobile(mobile: str | None) -> str | None:
    if not mobile:
        return None
    digits = "".join(ch for ch in str(mobile) if ch.isdigit())
    if len(digits) < 4:
        return "****"
    return f"****{digits[-4:]}"


def shape_student_row(row: dict) -> dict:
    return {
        "student_reg_no": row.get("StuRegNo"),
        "name": row.get("StudentName"),
        "father_name": row.get("FatherName"),
        "mobile_masked": _mask_mobile(row.get("Mobile")),
        "course": row.get("ClassName"),
        "roll_no": row.get("RollNo"),
    }


def search_students(ctx: ChatContext, term: str, limit: int = 10) -> dict:
    require_menu_permission(ctx, MENU_STUDENT_LIST, "student information")

    term = extract_student_search_term(term or "")
    if not term or len(term) < 2:
        return {
            "total": 0,
            "students": [],
            "needs_more_info": True,
            "hint": msg("search_student_prompt"),
        }

    rows = exec_sp(
        "USP_SearchAdmissionStudents",
        (term, ctx.branch_id, ctx.org_id),
    )[: min(max(limit, 1), 15)]

    students = [shape_student_row(r) for r in rows]
    multi_hint_en = (
        "Multiple students found — ask the user to pick one using name, course, roll no, or father name."
    )
    multi_hint_hi = (
        "Agar multiple students hain to user se pucho kaunsa student — "
        "name, course, roll no, father name se identify karo."
    )
    return {
        "total": len(students),
        "students": students,
        "needs_selection": len(students) > 1,
        "selected_hint": multi_hint_hi if get_reply_language() == "hi" else multi_hint_en
        if len(students) > 1
        else None,
    }


def get_student_profile(ctx: ChatContext, student_reg_no: int) -> dict:
    require_menu_permission(ctx, MENU_STUDENT_LIST, "student profile")

    rows = exec_sp("USP_STUDENTDETAILS", (1, student_reg_no, ctx.branch_id))
    if not rows:
        return {"found": False}

    row = rows[0]
    return {
        "found": True,
        "student_reg_no": student_reg_no,
        "name": " ".join(
            p for p in [row.get("FName"), row.get("MName"), row.get("LName")] if p
        ).strip(),
        "course": row.get("ClassName") or row.get("CourseName"),
        "section": row.get("SectionName"),
        "roll_no": row.get("Roll_No") or row.get("RollNo"),
        "father_name": row.get("Gname"),
        "status": row.get("StatusName") or row.get("Status"),
        "admission_no": row.get("AdmissionNo") or row.get("ErpId"),
    }
