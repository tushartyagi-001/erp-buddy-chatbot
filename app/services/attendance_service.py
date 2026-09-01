from __future__ import annotations

from app.auth.context import ChatContext
from app.db.connection import exec_sp
from app.permissions.checker import can_view_attendance
from app.utils.language import msg


def _status_key(status: str | None) -> str:
    return (status or "").strip().lower()


def _build_summary(course: str, batch: str, section: str, rows: list[dict]) -> dict:
    summary = {
        "course": course or "-",
        "batch": batch or "",
        "section": section or "",
        "present": 0,
        "absent": 0,
        "late": 0,
        "leave": 0,
        "half_day": 0,
        "week_off": 0,
        "holiday": 0,
        "total_marked": 0,
        "working_days": 0,
        "attended": 0,
        "percentage": 0.0,
    }
    for row in rows:
        count = max(1, int(row.get("TotalStudents") or 1))
        status = _status_key(row.get("StatusName"))
        summary["total_marked"] += count
        if status == "present":
            summary["present"] += count
        elif status == "absent":
            summary["absent"] += count
        elif status == "late":
            summary["late"] += count
        elif status == "leave":
            summary["leave"] += count
        elif status == "half day":
            summary["half_day"] += count
        elif status == "week off":
            summary["week_off"] += count
        elif status == "holiday":
            summary["holiday"] += count

    summary["working_days"] = max(
        0, summary["total_marked"] - summary["week_off"] - summary["holiday"]
    )
    summary["attended"] = (
        summary["present"] + summary["late"] + summary["half_day"]
    )
    if summary["working_days"]:
        summary["percentage"] = round(
            (summary["attended"] * 100) / summary["working_days"], 2
        )
    return summary


def get_student_attendance(ctx: ChatContext, student_reg_no: int) -> dict:
    if not can_view_attendance(ctx):
        return {
            "allowed": False,
            "message": msg("permission_attendance"),
        }

    rows = exec_sp(
        "USP_GetStudentAttendanceStatsForPopup",
        (student_reg_no, ctx.branch_id, ctx.org_id),
    )
    if not rows:
        return {"allowed": True, "found": False, "student_reg_no": student_reg_no}

    reg_text = str(student_reg_no)
    rows = [
        r
        for r in rows
        if str(r.get("StudentRegNo") or "").endswith(reg_text)
        or str(r.get("StudentRegNo") or "") == reg_text
    ]
    if not rows:
        return {"allowed": True, "found": False, "student_reg_no": student_reg_no}

    grouped: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        key = (
            str(row.get("CourseName") or "-"),
            str(row.get("CourseBatchName") or ""),
            str(row.get("SectionBatchName") or ""),
        )
        grouped.setdefault(key, []).append(row)

    course_summaries = [
        _build_summary(course, batch, section, group_rows)
        for (course, batch, section), group_rows in grouped.items()
    ]
    overall = _build_summary("Overall", "", "", rows)
    recent = sorted(rows, key=lambda r: r.get("AttendanceDate") or "", reverse=True)[:10]
    recent_rows = [
        {
            "date": r.get("AttendanceDate"),
            "course": r.get("CourseName"),
            "subject": r.get("SubjectName"),
            "status": r.get("StatusName"),
        }
        for r in recent
    ]

    return {
        "allowed": True,
        "found": True,
        "student_reg_no": student_reg_no,
        "student_name": rows[0].get("StudentName"),
        "overall": overall,
        "by_course": course_summaries,
        "recent_days": recent_rows,
    }
