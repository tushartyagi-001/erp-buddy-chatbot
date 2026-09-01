from __future__ import annotations

from datetime import date, datetime

from app.auth.context import ChatContext
from app.services import fee_service as fs
from app.services.excel_builder import (
    build_batch_summary_workbook,
    build_course_summary_workbook,
    build_daily_collection_workbook,
    build_defaulter_workbook,
    build_pending_fee_workbook,
    save_workbook,
)
from app.services.export_store import EXPORT_DIR, register_export


def _export_result(
    ctx: ChatContext,
    wb,
    filename: str,
    export_type: str,
    row_count: int,
    summary: str,
) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace(" ", "_")
    if not safe_name.lower().endswith(".xlsx"):
        safe_name += ".xlsx"
    final_name = f"{stamp}_{safe_name}"
    path = save_workbook(wb, EXPORT_DIR, final_name)
    file_id = register_export(ctx.branch_id, ctx.user_id, path, safe_name)
    return {
        "allowed": True,
        "export_type": export_type,
        "row_count": row_count,
        "file_id": file_id,
        "filename": safe_name,
        "summary": summary,
    }


def export_pending_fee_students_excel(
    ctx: ChatContext,
    course_id: int = 0,
    batch_id: int = 0,
    search_text: str = "",
) -> dict:
    data = fs.fetch_pending_fee_students_export(
        ctx, course_id=course_id, batch_id=batch_id, search_text=search_text
    )
    if not data.get("found"):
        return {
            "allowed": True,
            "export_type": "pending_fee",
            "found": False,
            "message": "No pending fee students found for export.",
        }
    students = data["students"]
    wb = build_pending_fee_workbook(
        students,
        title="Pending Fee Students Report",
    )
    total_balance = sum(float(s.get("balance") or 0) for s in students)
    summary = (
        f"{len(students)} students exported. Total pending balance: ₹{total_balance:,.0f}. "
        "Excel includes student list, course summary, batch/session summary, and pie charts."
    )
    return _export_result(
        ctx,
        wb,
        "pending_fee_students.xlsx",
        "pending_fee",
        len(students),
        summary,
    )


def export_course_wise_pending_fee_excel(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    data = fs.fetch_fee_course_summary_export(ctx, from_date=from_date, to_date=to_date)
    if not data.get("found"):
        return {
            "allowed": True,
            "export_type": "course_summary",
            "found": False,
            "message": "No course-wise fee data found for export.",
        }
    courses = data["courses"]
    wb = build_course_summary_workbook(courses, title="Course-wise Pending Fee Report")
    total_balance = sum(float(c.get("balance") or 0) for c in courses)
    summary = (
        f"{len(courses)} courses exported. Total pending: ₹{total_balance:,.0f}. "
        "Excel includes pie chart and collected vs pending bar chart."
    )
    return _export_result(
        ctx,
        wb,
        "course_wise_pending_fee.xlsx",
        "course_summary",
        len(courses),
        summary,
    )


def export_batch_wise_pending_fee_excel(
    ctx: ChatContext,
    course_id: int = 0,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    data = fs.fetch_fee_batch_summary_export(
        ctx,
        course_id=course_id,
        from_date=from_date,
        to_date=to_date,
    )
    if not data.get("found"):
        return {
            "allowed": True,
            "export_type": "batch_summary",
            "found": False,
            "message": "No batch/session-wise fee data found for export.",
        }
    batches = data["batches"]
    wb = build_batch_summary_workbook(batches, title="Batch / Session-wise Pending Fee Report")
    total_balance = sum(float(b.get("balance") or 0) for b in batches)
    summary = (
        f"{len(batches)} batches exported. Total pending: ₹{total_balance:,.0f}. "
        "Excel includes batch/session pie chart."
    )
    return _export_result(
        ctx,
        wb,
        "batch_session_pending_fee.xlsx",
        "batch_summary",
        len(batches),
        summary,
    )


def export_fee_defaulters_excel(ctx: ChatContext, course_id: int = 0) -> dict:
    data = fs.fetch_fee_defaulter_export(ctx, course_id=course_id)
    if not data.get("found"):
        return {
            "allowed": True,
            "export_type": "defaulters",
            "found": False,
            "message": "No fee defaulters found for export.",
        }
    defaulters = data["defaulters"]
    wb = build_defaulter_workbook(defaulters, title="Fee Defaulters Report")
    total = sum(float(d.get("overdue_amount") or 0) for d in defaulters)
    summary = (
        f"{len(defaulters)} defaulters exported. Total overdue: ₹{total:,.0f}. "
        "Excel includes course pie chart."
    )
    return _export_result(ctx, wb, "fee_defaulters.xlsx", "defaulters", len(defaulters), summary)


def export_daily_collection_excel(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    data = fs.fetch_fee_daily_collection_export(ctx, from_date=from_date, to_date=to_date)
    if not data.get("found"):
        return {
            "allowed": True,
            "export_type": "daily_collection",
            "found": False,
            "message": "No daily collection data found for export.",
        }
    collections = data["collections"]
    fd = data.get("from_date")
    td = data.get("to_date")
    if fd or td:
        title = f"Daily Collection ({fd or '…'} to {td or '…'})"
    else:
        title = "Daily Collection (All Time)"
    wb = build_daily_collection_workbook(collections, title=title)
    total = sum(float(c.get("amount") or 0) for c in collections)
    summary = (
        f"{len(collections)} rows exported. Total collected: ₹{total:,.0f}. "
        "Excel includes bar chart by date."
    )
    return _export_result(
        ctx, wb, "daily_fee_collection.xlsx", "daily_collection", len(collections), summary
    )
