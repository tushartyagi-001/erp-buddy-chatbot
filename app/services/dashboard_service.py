from __future__ import annotations

from datetime import date

from app.auth.context import ChatContext
from app.db.connection import exec_sp
from app.permissions.checker import can_view_fee, require_menu_permission
from app.permissions.menu_urls import MENU_DASHBOARD
from app.utils.language import msg


def _shape_row(row: dict) -> dict:
    return {
        "type": row.get("RowType"),
        "label": row.get("Label"),
        "sub_label": row.get("SubLabel"),
        "metric1": float(row.get("Metric1") or 0),
        "metric2": float(row.get("Metric2") or 0),
        "metric3": float(row.get("Metric3") or 0),
        "extra1": row.get("Extra1"),
        "extra2": row.get("Extra2"),
    }


def get_dashboard_summary(ctx: ChatContext) -> dict:
    require_menu_permission(ctx, MENU_DASHBOARD, "dashboard summary")

    try:
        rows = exec_sp("USP_NewDashboardSummary", (ctx.branch_id, ctx.org_id, ctx.fy_id))
    except Exception:
        return {
            "allowed": True,
            "found": False,
            "message": msg("dashboard_unavailable"),
            "student_kpis": [],
            "fee_kpis": [],
            "top_courses_by_students": [],
            "admission_trend": [],
            "fee_section_hidden": not can_view_fee(ctx),
        }

    shaped = [_shape_row(r) for r in rows]

    if not can_view_fee(ctx):
        shaped = [r for r in shaped if r.get("type") != "FeeKpi"]

    student_kpis = [r for r in shaped if r.get("type") == "StudentKpi"]
    fee_kpis = [r for r in shaped if r.get("type") == "FeeKpi"]
    top_courses = [r for r in shaped if r.get("type") == "CourseBatchStudents"][:8]
    admission_trend = [r for r in shaped if r.get("type") == "AdmissionTrend"]

    return {
        "allowed": True,
        "branch_id": ctx.branch_id,
        "fy_id": ctx.fy_id,
        "student_kpis": student_kpis,
        "fee_kpis": fee_kpis,
        "top_courses_by_students": top_courses,
        "admission_trend": admission_trend,
        "fee_section_hidden": not can_view_fee(ctx),
    }
