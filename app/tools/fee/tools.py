from __future__ import annotations

import json

from langchain_core.tools import tool

from app.services import fee_service as fs
from app.tools.common import run_tool
from app.tools.student.tools import get_selected_student


def _optional_dates(from_date: str = "", to_date: str = ""):
    from datetime import date

    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    return fd, td


def _need_student(reg_no: int) -> int | None:
    reg = reg_no or get_selected_student() or 0
    return int(reg) if reg else None


def _student_msg() -> str:
    from app.presentation.payloads import text_payload
    from app.utils.language import msg

    return json.dumps(
        text_payload(msg("select_student")),
        ensure_ascii=False,
    )


# --- Student fee tools ---


@tool
def get_student_fee_summary_tool(student_reg_no: int = 0) -> str:
    """Student fee summary — total, paid, balance (course-wise)."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_fee_summary, student_reg_no=reg)


@tool
def get_student_fee_installments_tool(student_reg_no: int = 0) -> str:
    """Student installment schedule and balances."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_fee_installments, student_reg_no=reg)


@tool
def get_student_fee_overdue_tool(student_reg_no: int = 0) -> str:
    """Student overdue fee installments."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_fee_overdue, student_reg_no=reg)


@tool
def get_student_fee_receipt_history_tool(student_reg_no: int = 0) -> str:
    """Student fee receipt history."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_receipt_history, student_reg_no=reg)


@tool
def get_student_fee_ledger_tool(student_reg_no: int = 0) -> str:
    """Student fee ledger totals."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_fee_ledger, student_reg_no=reg)


@tool
def get_student_fee_discount_tool(student_reg_no: int = 0) -> str:
    """Student discounts and scholarships."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_fee_discount, student_reg_no=reg)


@tool
def get_student_transport_fee_tool(student_reg_no: int = 0) -> str:
    """Student transport fee status."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_transport_fee, student_reg_no=reg)


@tool
def get_student_hostel_fee_tool(student_reg_no: int = 0) -> str:
    """Student hostel fee status."""
    reg = _need_student(student_reg_no)
    if not reg:
        return _student_msg()
    return run_tool(fs.get_student_hostel_fee, student_reg_no=reg)


# --- Branch / report tools ---


@tool
def get_fee_due_alert_tool() -> str:
    """Branch fee due alerts."""
    return run_tool(fs.get_fee_due_alert)


@tool
def get_fee_branch_snapshot_tool(
    course_id: int = 0, from_date: str = "", to_date: str = ""
) -> str:
    """Branch fee snapshot — all-time totals unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_branch_snapshot, course_id=course_id, from_date=fd, to_date=td)


@tool
def get_fee_daily_collection_tool(from_date: str = "", to_date: str = "") -> str:
    """Daily fee collection — all dates unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_daily_collection, from_date=fd, to_date=td)


@tool
def get_fee_pending_due_list_tool(due_status: str = "Overdue") -> str:
    """Pending or overdue installments list."""
    return run_tool(fs.get_fee_pending_due_list, due_status=due_status)


@tool
def get_fee_defaulter_list_tool(course_id: int = 0) -> str:
    """Fee defaulter students list."""
    return run_tool(fs.get_fee_defaulter_list, course_id=course_id)


@tool
def get_pending_fee_students_tool(
    course_id: int = 0, batch_id: int = 0, search_text: str = ""
) -> str:
    """Pending fee students list."""
    return run_tool(
        fs.get_pending_fee_students,
        course_id=course_id,
        batch_id=batch_id,
        search_text=search_text,
    )


@tool
def get_fee_course_summary_tool(from_date: str = "", to_date: str = "") -> str:
    """Course-wise fee summary — all-time unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_course_summary, from_date=fd, to_date=td)


@tool
def get_course_wise_student_count_tool(from_date: str = "", to_date: str = "") -> str:
    """Course-wise student count — how many students per course."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_course_wise_student_count, from_date=fd, to_date=td)


@tool
def get_fee_batch_summary_tool(
    course_id: int = 0, from_date: str = "", to_date: str = ""
) -> str:
    """Batch-wise fee summary — all-time unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_batch_summary, course_id=course_id, from_date=fd, to_date=td)


@tool
def get_fee_head_summary_tool(from_date: str = "", to_date: str = "") -> str:
    """Fee head demand vs collection — all-time unless dates given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_head_summary, from_date=fd, to_date=td)


@tool
def get_fee_payment_mode_summary_tool(from_date: str = "", to_date: str = "") -> str:
    """Payment mode collection summary — all-time unless dates given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_payment_mode_summary, from_date=fd, to_date=td)


@tool
def get_fee_installment_calendar_tool(from_date: str = "", to_date: str = "") -> str:
    """Installment calendar — all upcoming unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_installment_calendar, from_date=fd, to_date=td)


@tool
def get_fee_receipt_register_tool(from_date: str = "", to_date: str = "") -> str:
    """Receipt register — all-time unless from_date/to_date are given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_receipt_register, from_date=fd, to_date=td)


@tool
def get_fee_aging_report_tool(course_id: int = 0) -> str:
    """Fee aging buckets report."""
    return run_tool(fs.get_fee_aging_report, course_id=course_id)


@tool
def get_fee_rollback_receipts_tool(from_date: str = "", to_date: str = "") -> str:
    """Rollback receipt audit list — all-time unless dates given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_rollback_receipts, from_date=fd, to_date=td)


@tool
def get_fee_tax_gst_summary_tool(from_date: str = "", to_date: str = "") -> str:
    """GST/tax collection summary — all-time unless dates given."""
    fd, td = _optional_dates(from_date, to_date)
    return run_tool(fs.get_fee_tax_gst_summary, from_date=fd, to_date=td)


# --- Reference ---


@tool
def search_fee_students_tool(name_or_term: str) -> str:
    """Search students with fee balance."""
    return run_tool(fs.search_fee_students, term=name_or_term, limit=10)


@tool
def get_fee_structures_by_course_tool(course_id: int) -> str:
    """Fee structures for a course."""
    return run_tool(fs.get_fee_structures_by_course, course_id=course_id)


@tool
def get_scholarships_list_tool(search_text: str = "") -> str:
    """Scholarship schemes list."""
    return run_tool(fs.get_scholarships_list, search_text=search_text)


TOOLS = [
    get_student_fee_summary_tool,
    get_student_fee_installments_tool,
    get_student_fee_overdue_tool,
    get_student_fee_receipt_history_tool,
    get_student_fee_ledger_tool,
    get_student_fee_discount_tool,
    get_student_transport_fee_tool,
    get_student_hostel_fee_tool,
    get_fee_due_alert_tool,
    get_fee_branch_snapshot_tool,
    get_fee_daily_collection_tool,
    get_fee_pending_due_list_tool,
    get_fee_defaulter_list_tool,
    get_pending_fee_students_tool,
    get_fee_course_summary_tool,
    get_course_wise_student_count_tool,
    get_fee_batch_summary_tool,
    get_fee_head_summary_tool,
    get_fee_payment_mode_summary_tool,
    get_fee_installment_calendar_tool,
    get_fee_receipt_register_tool,
    get_fee_aging_report_tool,
    get_fee_rollback_receipts_tool,
    get_fee_tax_gst_summary_tool,
    search_fee_students_tool,
    get_fee_structures_by_course_tool,
    get_scholarships_list_tool,
]
