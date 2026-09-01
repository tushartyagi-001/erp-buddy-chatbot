from __future__ import annotations

from app.auth.context import ChatContext
from app.db.connection import exec_readonly_query, exec_sp_result_sets
from app.permissions.checker import can_view_exam
from app.utils.language import msg


def _shape_exam_row(row: dict) -> dict:
    return {
        "exam_plan_id": row.get("ExamPlanId"),
        "exam_name": row.get("ExamPlanName"),
        "exam_type": row.get("ExamTypeName"),
        "course": row.get("CourseName"),
        "percentage": float(row.get("Percentage") or 0),
        "grade": row.get("Grade"),
        "result_status": row.get("ResultStatus") or row.get("PassFailStatus"),
        "marks_obtained": float(row.get("TotalObtained") or 0),
        "max_marks": float(row.get("TotalMaxMarks") or 0),
    }


def _shape_subject_row(row: dict) -> dict:
    return {
        "subject": row.get("SubjectName"),
        "subject_code": row.get("SubjectCode"),
        "marks_obtained": float(row.get("MarksObtained") or 0),
        "max_marks": float(row.get("MaxMarks") or 0),
        "pass_marks": float(row.get("PassMarks") or 0),
        "status": row.get("SubjectStatus"),
        "attendance": row.get("AttendanceStatus"),
    }


def list_student_exam_results(ctx: ChatContext, student_reg_no: int, limit: int = 10) -> dict:
    if not can_view_exam(ctx):
        return {
            "allowed": False,
            "message": msg("permission_exam"),
        }

    rows = exec_readonly_query(
        """
        SELECT TOP (%s)
            R.ExamPlanId, H.ExamPlanName, ET.ExamTypeName, CM.CourseName,
            R.Percentage, R.Grade, R.ResultStatus, R.PassFailStatus,
            R.TotalObtained, R.TotalMaxMarks
        FROM dbo.Tbl_ExamResultHeader R
        INNER JOIN dbo.Tbl_ExamPlanHeader H ON H.ExamPlanId = R.ExamPlanId
        INNER JOIN dbo.Tbl_ExamTypeMaster ET ON ET.ExamTypeId = H.ExamTypeId
        INNER JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = H.CourseId
        WHERE (R.StudentId = %s OR TRY_CAST(R.StudentRegNo AS BIGINT) = %s)
          AND H.BranchId = %s
          AND (%s = 0 OR H.OrganizationId = %s)
        ORDER BY H.CreatedDate DESC
        """,
        (min(max(limit, 1), 15), student_reg_no, student_reg_no, ctx.branch_id, ctx.org_id, ctx.org_id),
    )
    exams = [_shape_exam_row(r) for r in rows]
    return {
        "allowed": True,
        "found": bool(exams),
        "student_reg_no": student_reg_no,
        "exams": exams,
        "needs_selection": len(exams) > 1,
    }


def get_exam_result_detail(
    ctx: ChatContext, exam_plan_id: int, student_reg_no: int
) -> dict:
    if not can_view_exam(ctx):
        return {
            "allowed": False,
            "message": msg("permission_exam"),
        }

    sets = exec_sp_result_sets(
        "USP_GetNewExamResult",
        (exam_plan_id, student_reg_no),
    )
    headers = sets[0] if sets else []
    subjects = sets[1] if len(sets) > 1 else []
    if not headers:
        return {
            "allowed": True,
            "found": False,
            "exam_plan_id": exam_plan_id,
            "student_reg_no": student_reg_no,
        }

    header = headers[0]
    return {
        "allowed": True,
        "found": True,
        "exam_plan_id": exam_plan_id,
        "student_reg_no": student_reg_no,
        "summary": _shape_exam_row(header),
        "subjects": [_shape_subject_row(s) for s in subjects],
    }
