from __future__ import annotations

from datetime import date

from app.auth.context import ChatContext
from app.db.connection import exec_readonly_query, exec_sp
from app.permissions.checker import (
    PermissionDenied,
    can_view_fee,
    can_view_fee_reports,
    require_fee_reports,
    require_fee_view,
)
from app.utils.language import msg


def _today() -> date:
    return date.today()


def _month_start() -> date:
    t = _today()
    return t.replace(day=1)


def _sp_dates(
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[None | str, None | str]:
    return (
        from_date.isoformat() if from_date else None,
        to_date.isoformat() if to_date else None,
    )


def _attach_dates(
    result: dict,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    from_d, to_d = _sp_dates(from_date, to_date)
    if from_d:
        result["from_date"] = from_d
    if to_d:
        result["to_date"] = to_d
    return result


def _report_org_id(_ctx: ChatContext) -> int:
    """Fee report SPs treat OrgId=0 as all orgs within the branch (ERP report convention)."""
    return 0


def _limit(rows: list, n: int = 15) -> list:
    return (rows or [])[:n]


def _f(val) -> float:
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _row_amount(row: dict, *keys: str) -> float:
    for key in keys:
        if row.get(key) is not None:
            return _f(row.get(key))
    return 0.0


def _ok(**kwargs) -> dict:
    return {"allowed": True, **kwargs}


def _deny(msg: str) -> dict:
    return {"allowed": False, "message": msg}


def shape_fee_summary_row(row: dict) -> dict:
    return {
        "student_reg_no": row.get("StudentId") or row.get("StudentRegNo"),
        "student_name": row.get("StudentName"),
        "course": row.get("CourseName"),
        "batch": row.get("BatchName"),
        "session": row.get("AcademicSession"),
        "fee_structure": row.get("FeeStructureName") or row.get("StructureName"),
        "grand_total": _f(row.get("GrandTotal")),
        "paid_amount": _f(row.get("PaidAmount")),
        "balance_amount": _f(row.get("BalanceAmount")),
        "status": row.get("FeeStatus") or row.get("Status"),
    }


# --- Student level ---


def get_student_fee_summary(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_GetStudentCourseFeeSummaryForPopup",
        (student_reg_no, ctx.branch_id, _report_org_id(ctx)),
    )
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, fees=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        fees=[shape_fee_summary_row(r) for r in rows],
    )


def get_student_fee_installments(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    try:
        rows = exec_sp(
            "USP_ChatBot_StudentFeeInstallments",
            (student_reg_no, ctx.branch_id, _report_org_id(ctx)),
        )
    except Exception:
        return _ok(
            found=False,
            student_reg_no=student_reg_no,
            message="Installment detail abhi load nahi ho payi. Admin se USP_ChatBot_FeeTools.sql run karwayein.",
            installments=[],
        )
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, installments=[])
    installments = [
        {
            "course": r.get("CourseName"),
            "fee_head": r.get("FeeHeadName"),
            "installment_no": r.get("InstallmentNo"),
            "due_date": r.get("DueDate"),
            "payable": _f(r.get("PayableAmount")),
            "paid": _f(r.get("InstallmentPaid")),
            "balance": _f(r.get("InstallmentBalance")),
            "status": r.get("InstallmentStatus"),
            "is_overdue": bool(r.get("IsOverdue")),
        }
        for r in rows
    ]
    return _ok(found=True, student_reg_no=student_reg_no, installments=installments)


def get_student_fee_overdue(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    try:
        rows = exec_sp(
            "USP_ChatBot_StudentFeeOverdue",
            (student_reg_no, ctx.branch_id, _report_org_id(ctx)),
        )
    except Exception:
        rows = []
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, overdue=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        overdue=[
            {
                "fee_head": r.get("FeeHeadName"),
                "due_date": r.get("DueDate"),
                "amount": _f(r.get("OverdueAmount")),
                "days_overdue": int(r.get("DaysOverdue") or 0),
            }
            for r in rows
        ],
    )


def get_student_receipt_history(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    try:
        rows = exec_sp(
            "USP_ChatBot_StudentReceiptHistory",
            (student_reg_no, ctx.branch_id, _report_org_id(ctx)),
        )
    except Exception:
        rows = []
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, receipts=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        receipts=[
            {
                "date": r.get("ReceiptDate"),
                "mode": r.get("PaymentMode"),
                "amount": _f(r.get("PaidAmount")),
                "discount": _f(r.get("DiscountAmount")),
                "late_fee": _f(r.get("LateFeeAmount")),
                "status": r.get("Status"),
                "reference_masked": r.get("ReferenceMasked"),
                "scholarship": r.get("ScholarshipName"),
            }
            for r in rows
        ],
    )


def get_student_fee_ledger(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_FeeReport_StudentLedger",
        (ctx.branch_id, _report_org_id(ctx), str(student_reg_no), 0, 1, 15),
    )
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, ledger=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        ledger=[
            {
                "student_name": r.get("StudentName"),
                "course": r.get("CourseName"),
                "structure": r.get("StructureName"),
                "grand_total": _f(r.get("GrandTotal")),
                "paid": _f(r.get("PaidAmount")),
                "discount": _f(r.get("DiscountAmount")),
                "balance": _f(r.get("BalanceAmount")),
                "status": r.get("Status"),
            }
            for r in rows
        ],
    )


def get_student_fee_discount(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_FeeReport_Discount",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            None,
            None,
            0,
            0,
            1,
            15,
        ),
    )
    filtered = [
        r
        for r in rows
        if str(r.get("StudentRegNo", "")) == str(student_reg_no)
        or str(r.get("StudentId", "")) == str(student_reg_no)
    ]
    if not filtered:
        return _ok(found=False, student_reg_no=student_reg_no, discounts=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        discounts=[
            {
                "student_name": r.get("StudentName"),
                "course": r.get("CourseName"),
                "fee_head": r.get("FeeHeadName"),
                "discount_amount": _f(r.get("DiscountAmount")),
                "receipt_date": r.get("ReceiptDate"),
            }
            for r in filtered[:10]
        ],
    )


def get_student_transport_fee(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_SearchTransportFeeStudents",
        (ctx.branch_id, ctx.fy_id, str(student_reg_no), "all", 0, 1, 5),
    )
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, transport=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        transport=[
            {
                "student_name": r.get("StudentName"),
                "route": r.get("RouteName"),
                "stop": r.get("StopName"),
                "payable": _f(r.get("TransportPayableAmount") or r.get("PayableAmount")),
                "status": r.get("Status"),
            }
            for r in rows
        ],
    )


def get_student_hostel_fee(ctx: ChatContext, student_reg_no: int) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_SearchHostelFeeStudents",
        (ctx.branch_id, _report_org_id(ctx), str(student_reg_no), "all", 1, 5),
    )
    if not rows:
        return _ok(found=False, student_reg_no=student_reg_no, hostel=[])
    return _ok(
        found=True,
        student_reg_no=student_reg_no,
        hostel=[
            {
                "student_name": r.get("StudentName"),
                "hostel": r.get("HostelName"),
                "room": r.get("RoomNo"),
                "balance": _f(r.get("HostelPayableAmount")),
            }
            for r in rows
        ],
    )


# --- Branch / reports ---


def get_fee_due_alert(ctx: ChatContext) -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_GetDashboardFeeDueAlert",
        (ctx.branch_id, _report_org_id(ctx), _today().isoformat()),
    )
    if not rows:
        return _ok(found=False, alert={})
    row = rows[0]
    alert = {
        "overdue_amount": _f(row.get("OverdueAmount")),
        "overdue_students": int(row.get("OverdueStudentCount") or 0),
        "due_today_amount": _f(row.get("DueTodayAmount")),
        "upcoming_7_days_amount": _f(row.get("Upcoming7Amount")),
        "total_pending_amount": _f(row.get("TotalPendingAmount")),
        "max_days_overdue": int(row.get("MaxDaysOverdue") or 0),
    }
    has_due = any(
        alert[k] > 0
        for k in ("overdue_amount", "due_today_amount", "upcoming_7_days_amount")
    )
    return _ok(found=has_due, alert=alert)


def get_fee_branch_snapshot(
    ctx: ChatContext,
    course_id: int = 0,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_view(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_Dashboard",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, course_id),
    )
    if not rows:
        return _ok(found=False, snapshot={})
    r = rows[0]
    result = _ok(
        found=True,
        snapshot={
            "total_assigned": _f(r.get("TotalAssigned")),
            "total_collected": _f(r.get("TotalCollected")),
            "total_balance": _f(r.get("TotalBalance")),
            "overdue_amount": _f(r.get("OverdueAmount")),
            "active_students": int(r.get("ActiveStudents") or 0),
            "paid_receipts": int(r.get("PaidReceipts") or 0),
        },
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_daily_collection(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_DailyCollection",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, "", 1, 15),
    )
    result = _ok(
        found=bool(rows),
        collections=[
            {
                "date": r.get("CollectionDate"),
                "mode": r.get("PaymentMode"),
                "receipts": int(r.get("ReceiptCount") or 0),
                "amount": _row_amount(r, "CollectedAmount", "TotalCollected"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_pending_due_list(
    ctx: ChatContext,
    due_status: str = "Overdue",
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_PendingDue",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            from_d,
            to_d,
            0,
            0,
            due_status,
            1,
            15,
        ),
    )
    result = _ok(
        found=bool(rows),
        due_status=due_status,
        items=[
            {
                "student_name": r.get("StudentName"),
                "student_reg_no": r.get("StudentRegNo"),
                "course": r.get("CourseName"),
                "due_date": r.get("DueDate"),
                "balance": _f(r.get("BalanceAmount")),
                "fee_head": r.get("FeeHeadName"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_defaulter_list(ctx: ChatContext, course_id: int = 0) -> dict:
    require_fee_reports(ctx)
    rows = exec_sp(
        "USP_FeeReport_Defaulter",
        (ctx.branch_id, _report_org_id(ctx), course_id, "", 1, 15),
    )
    return _ok(
        found=bool(rows),
        defaulters=[
            {
                "student_name": r.get("StudentName"),
                "student_reg_no": r.get("StudentRegNo"),
                "course": r.get("CourseName"),
                "batch": r.get("BatchName"),
                "overdue_amount": _f(r.get("TotalOverdueAmount")),
                "max_days_overdue": int(r.get("MaxDaysOverdue") or 0),
            }
            for r in rows
        ],
    )


def get_pending_fee_students(
    ctx: ChatContext,
    course_id: int = 0,
    batch_id: int = 0,
    search_text: str = "",
) -> dict:
    require_fee_reports(ctx)
    try:
        rows = exec_sp(
            "USP_ChatBot_PendingFeeStudents",
            (ctx.branch_id, _report_org_id(ctx), course_id, batch_id, search_text or "", 15),
        )
    except Exception:
        if not course_id or not batch_id:
            return _ok(
                found=False,
                message="Course/batch filter ke liye USP_ChatBot_FeeTools.sql deploy karein.",
                students=[],
            )
        rows = exec_sp(
            "USP_GetPendingFeeStudentsReport",
            (course_id, batch_id, search_text or "", 0, 0, 0, 1, 15, ctx.branch_id, _report_org_id(ctx)),
        )
    return _ok(
        found=bool(rows),
        students=[
            {
                "student_name": r.get("StudentName"),
                "student_reg_no": r.get("StudentRegNo"),
                "course": r.get("CourseName"),
                "batch": r.get("BatchName"),
                "balance": _f(r.get("BalanceAmount")),
                "pending_percent": _f(r.get("PendingPercent")),
            }
            for r in _limit(rows)
        ],
    )


def get_fee_course_summary(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_CourseSummary",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, 1, 15),
    )
    result = _ok(
        found=bool(rows),
        courses=[
            {
                "course": r.get("CourseName"),
                "assigned": _row_amount(r, "AssignedAmount", "TotalAssigned"),
                "collected": _row_amount(r, "CollectedAmount", "TotalCollected"),
                "balance": _row_amount(r, "BalanceAmount", "TotalBalance"),
                "students": int(r.get("StudentCount") or 0),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_course_wise_student_count(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_CourseSummary",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, 1, 100),
    )
    courses = [
        {
            "course": r.get("CourseName"),
            "students": int(r.get("StudentCount") or 0),
        }
        for r in rows
    ]
    total = sum(c["students"] for c in courses)
    result = _ok(
        found=bool(courses),
        courses=courses,
        total_students=total,
        row_count=len(courses),
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_batch_summary(
    ctx: ChatContext,
    course_id: int = 0,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_BatchSummary",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            from_d,
            to_d,
            course_id,
            0,
            1,
            15,
        ),
    )
    result = _ok(
        found=bool(rows),
        batches=[
            {
                "course": r.get("CourseName"),
                "batch": r.get("BatchName"),
                "assigned": _row_amount(r, "AssignedAmount", "TotalAssigned"),
                "collected": _row_amount(r, "CollectedAmount", "TotalCollected"),
                "balance": _row_amount(r, "BalanceAmount", "TotalBalance"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_head_summary(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_FeeHeadSummary",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            from_d,
            to_d,
            0,
            0,
            1,
            15,
        ),
    )
    result = _ok(
        found=bool(rows),
        fee_heads=[
            {
                "fee_head": r.get("FeeHeadName"),
                "demand": _row_amount(r, "TotalDemand", "AssignedAmount"),
                "collected": _row_amount(r, "TotalCollected", "CollectedAmount"),
                "balance": _row_amount(r, "TotalBalance", "BalanceAmount"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_payment_mode_summary(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_PaymentModeCollection",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            from_d,
            to_d,
            0,
            "",
            1,
            15,
        ),
    )
    result = _ok(
        found=bool(rows),
        modes=[
            {
                "mode": r.get("PaymentMode"),
                "receipts": int(r.get("ReceiptCount") or 0),
                "amount": _row_amount(r, "CollectedAmount", "TotalCollected"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_installment_calendar(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_InstallmentCalendar",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, 1, 20),
    )
    result = _ok(
        found=bool(rows),
        calendar=[
            {
                "due_date": r.get("DueDate") or r.get("DueDateText"),
                "course": r.get("CourseName"),
                "students_due": int(r.get("StudentCount") or 0),
                "amount_due": _row_amount(r, "DueAmount", "BalanceAmount"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_receipt_register(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_ReceiptRegister",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, "", "", 1, 15),
    )
    result = _ok(
        found=bool(rows),
        receipts=[
            {
                "date": r.get("ReceiptDate"),
                "student_name": r.get("StudentName"),
                "student_reg_no": r.get("StudentRegNo"),
                "mode": r.get("PaymentMode"),
                "amount": _row_amount(r, "TotalPaidAmount", "CollectedAmount"),
                "course": r.get("CourseName"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_aging_report(ctx: ChatContext, course_id: int = 0) -> dict:
    require_fee_reports(ctx)
    rows = exec_sp(
        "USP_FeeReport_Aging",
        (ctx.branch_id, _report_org_id(ctx), course_id, 0, "", 1, 15),
    )
    return _ok(
        found=bool(rows),
        aging=[
            {
                "student_name": r.get("StudentName"),
                "student_reg_no": r.get("StudentRegNo"),
                "course": r.get("CourseName"),
                "bucket_0_30": _f(r.get("Bucket0To30")),
                "bucket_31_60": _f(r.get("Bucket31To60")),
                "bucket_61_90": _f(r.get("Bucket61To90")),
                "bucket_90_plus": _f(r.get("Bucket90Plus")),
            }
            for r in rows
        ],
    )


def get_fee_rollback_receipts(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_RollbackReceipt",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, "", 1, 15),
    )
    result = _ok(
        found=bool(rows),
        rollbacks=[
            {
                "date": r.get("ReceiptDate"),
                "student_name": r.get("StudentName"),
                "amount": _row_amount(r, "TotalPaidAmount", "CollectedAmount"),
                "reason": r.get("RollbackReason") or r.get("Remarks"),
            }
            for r in rows
        ],
    )
    return _attach_dates(result, from_date, to_date)


def get_fee_tax_gst_summary(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    require_fee_reports(ctx)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_TaxGst",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, 1, 15),
    )
    if not rows:
        return _ok(found=False, summary={})
    r = rows[0]
    result = _ok(
        found=True,
        summary={
            "taxable_amount": _row_amount(r, "TaxableAmount"),
            "non_taxable_amount": _row_amount(r, "NonTaxableAmount"),
            "gst_amount": _row_amount(r, "GstAmount"),
            "total_collected": _row_amount(r, "TotalCollected", "CollectedAmount"),
        },
    )
    return _attach_dates(result, from_date, to_date)


# --- Reference ---


def search_fee_students(ctx: ChatContext, term: str, limit: int = 10) -> dict:
    require_fee_view(ctx)
    term = (term or "").strip()
    if len(term) < 2:
        return _ok(total=0, students=[], needs_more_info=True)
    try:
        rows = exec_sp(
            "USP_ChatBot_FeeSearchStudent",
            (term, ctx.branch_id, _report_org_id(ctx), min(max(limit, 1), 15)),
        )
    except Exception:
        rows = exec_sp(
            "USP_SearchStudentFeeCollectionAssignments",
            (ctx.branch_id, _report_org_id(ctx), 0, 0, term, 1, limit),
        )
    students = [
        {
            "student_reg_no": r.get("StudentRegNo"),
            "name": r.get("StudentName"),
            "course": r.get("CourseName"),
            "batch": r.get("BatchName"),
            "balance": _f(r.get("BalanceAmount")),
            "status": r.get("FeeStatus") or r.get("Status"),
        }
        for r in rows
    ]
    return _ok(total=len(students), students=students, needs_selection=len(students) > 1)


def get_fee_structures_by_course(ctx: ChatContext, course_id: int) -> dict:
    require_fee_view(ctx)
    if not course_id:
        return _deny(msg("course_id_required"))
    rows = exec_sp(
        "USP_GetAdmissionFeeStructuresByCourse",
        (course_id, ctx.branch_id, _report_org_id(ctx)),
    )
    return _ok(
        found=bool(rows),
        course_id=course_id,
        structures=[
            {
                "structure_id": r.get("FeeStructureId"),
                "name": r.get("StructureName") or r.get("FeeStructureName"),
                "grand_total": _f(r.get("GrandTotal") or r.get("TotalAmount")),
            }
            for r in _limit(rows, 10)
        ],
    )


def get_scholarships_list(ctx: ChatContext, search_text: str = "") -> dict:
    require_fee_view(ctx)
    rows = exec_sp(
        "USP_GetScholarshipsList",
        (ctx.branch_id, _report_org_id(ctx), search_text or ""),
    )
    return _ok(
        found=bool(rows),
        scholarships=[
            {
                "name": r.get("ScholarshipName") or r.get("Name"),
                "type": r.get("ScholarshipType") or r.get("Type"),
                "value": r.get("Value") or r.get("DiscountValue"),
            }
            for r in _limit(rows, 15)
        ],
    )


# --- Excel export (higher row limits) ---


def fetch_pending_fee_students_export(
    ctx: ChatContext,
    course_id: int = 0,
    batch_id: int = 0,
    search_text: str = "",
    limit: int = 500,
) -> dict:
    require_fee_reports(ctx)
    limit = min(max(limit, 1), 500)
    search_text = (search_text or "").strip()
    like = f"%{search_text}%" if search_text else ""
    rows = exec_readonly_query(
        """
        SELECT TOP (%s)
            TRY_CAST(A.StudentRegNo AS BIGINT) AS StudentRegNo,
            A.StudentName,
            ISNULL(CM.CourseName, '') AS CourseName,
            ISNULL(A.BatchName, CB.BatchName) AS BatchName,
            ISNULL(A.GrandTotal, 0) AS GrandTotal,
            ISNULL(A.PaidAmount, 0) AS PaidAmount,
            ISNULL(A.BalanceAmount, 0) AS BalanceAmount,
            CAST(CASE WHEN ISNULL(A.GrandTotal, 0) <= 0 THEN 0
                 ELSE (ISNULL(A.BalanceAmount, 0) * 100.0 / A.GrandTotal) END AS DECIMAL(9,2)) AS PendingPercent
        FROM dbo.Tbl_StudentFeeAssignment A
        LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
        LEFT JOIN dbo.Tbl_CourseBatch CB ON CB.BatchId = A.BatchId
        WHERE A.BranchId = %s
          AND (%s = 0 OR A.OrganizationId = %s)
          AND (%s = 0 OR A.CourseId = %s)
          AND (%s = 0 OR A.BatchId = %s)
          AND ISNULL(A.Status, '') <> 'Closed'
          AND ISNULL(A.BalanceAmount, 0) > 0
          AND (
              %s = ''
              OR A.StudentName LIKE %s
              OR CAST(A.StudentRegNo AS NVARCHAR(50)) LIKE %s
          )
        ORDER BY A.BalanceAmount DESC, A.StudentName
        """,
        (
            limit,
            ctx.branch_id,
            _report_org_id(ctx),
            _report_org_id(ctx),
            course_id,
            course_id,
            batch_id,
            batch_id,
            search_text,
            like,
            like,
        ),
    )
    students = [
        {
            "student_reg_no": r.get("StudentRegNo"),
            "student_name": r.get("StudentName"),
            "course": r.get("CourseName"),
            "batch": r.get("BatchName"),
            "grand_total": _f(r.get("GrandTotal")),
            "paid": _f(r.get("PaidAmount")),
            "balance": _f(r.get("BalanceAmount")),
            "pending_percent": _f(r.get("PendingPercent")),
        }
        for r in rows
    ]
    return _ok(found=bool(students), students=students, row_count=len(students))


def fetch_fee_course_summary_export(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
) -> dict:
    require_fee_reports(ctx)
    limit = min(max(limit, 1), 100)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_CourseSummary",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, 1, limit),
    )
    courses = [
        {
            "course": r.get("CourseName"),
            "assigned": _row_amount(r, "AssignedAmount", "TotalAssigned"),
            "collected": _row_amount(r, "CollectedAmount", "TotalCollected"),
            "balance": _row_amount(r, "BalanceAmount", "TotalBalance"),
            "students": int(r.get("StudentCount") or 0),
        }
        for r in rows
    ]
    result = _ok(found=bool(courses), courses=courses, row_count=len(courses))
    return _attach_dates(result, from_date, to_date)


def fetch_fee_batch_summary_export(
    ctx: ChatContext,
    course_id: int = 0,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
) -> dict:
    require_fee_reports(ctx)
    limit = min(max(limit, 1), 100)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_BatchSummary",
        (
            ctx.branch_id,
            _report_org_id(ctx),
            from_d,
            to_d,
            course_id,
            0,
            1,
            limit,
        ),
    )
    batches = [
        {
            "course": r.get("CourseName"),
            "batch": r.get("BatchName"),
            "assigned": _row_amount(r, "AssignedAmount", "TotalAssigned"),
            "collected": _row_amount(r, "CollectedAmount", "TotalCollected"),
            "balance": _row_amount(r, "BalanceAmount", "TotalBalance"),
        }
        for r in rows
    ]
    result = _ok(found=bool(batches), batches=batches, row_count=len(batches))
    return _attach_dates(result, from_date, to_date)


def fetch_fee_defaulter_export(ctx: ChatContext, course_id: int = 0, limit: int = 500) -> dict:
    require_fee_reports(ctx)
    limit = min(max(limit, 1), 500)
    rows = exec_sp(
        "USP_FeeReport_Defaulter",
        (ctx.branch_id, _report_org_id(ctx), course_id, "", 1, limit),
    )
    defaulters = [
        {
            "student_name": r.get("StudentName"),
            "student_reg_no": r.get("StudentRegNo"),
            "course": r.get("CourseName"),
            "batch": r.get("BatchName"),
            "overdue_amount": _f(r.get("TotalOverdueAmount")),
            "max_days_overdue": int(r.get("MaxDaysOverdue") or 0),
        }
        for r in rows
    ]
    return _ok(found=bool(defaulters), defaulters=defaulters, row_count=len(defaulters))


def fetch_fee_daily_collection_export(
    ctx: ChatContext,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 200,
) -> dict:
    require_fee_reports(ctx)
    limit = min(max(limit, 1), 200)
    from_d, to_d = _sp_dates(from_date, to_date)
    rows = exec_sp(
        "USP_FeeReport_DailyCollection",
        (ctx.branch_id, _report_org_id(ctx), from_d, to_d, 0, "", 1, limit),
    )
    collections = [
        {
            "date": r.get("CollectionDate"),
            "mode": r.get("PaymentMode"),
            "receipts": int(r.get("ReceiptCount") or 0),
            "amount": _row_amount(r, "CollectedAmount", "TotalCollected"),
        }
        for r in rows
    ]
    result = _ok(
        found=bool(collections),
        collections=collections,
        row_count=len(collections),
    )
    return _attach_dates(result, from_date, to_date)
