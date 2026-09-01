from __future__ import annotations

import re

BASE_TOOL_NAMES = {
    "search_students_tool",
    "select_student_tool",
    "get_student_profile_tool",
}

TOOL_GROUPS: dict[str, set[str]] = {
    "student": {
        "search_students_tool",
        "select_student_tool",
        "get_student_profile_tool",
    },
    "fee": {
        "get_student_fee_summary_tool",
        "get_student_fee_installments_tool",
        "get_student_fee_overdue_tool",
        "get_student_fee_receipt_history_tool",
        "get_student_fee_ledger_tool",
        "get_student_fee_discount_tool",
        "get_student_transport_fee_tool",
        "get_student_hostel_fee_tool",
        "get_fee_due_alert_tool",
        "get_fee_branch_snapshot_tool",
        "get_fee_daily_collection_tool",
        "get_fee_pending_due_list_tool",
        "get_fee_defaulter_list_tool",
        "get_pending_fee_students_tool",
        "get_fee_course_summary_tool",
        "get_course_wise_student_count_tool",
        "get_fee_batch_summary_tool",
        "get_fee_head_summary_tool",
        "get_fee_payment_mode_summary_tool",
        "get_fee_installment_calendar_tool",
        "get_fee_receipt_register_tool",
        "get_fee_aging_report_tool",
        "get_fee_rollback_receipts_tool",
        "get_fee_tax_gst_summary_tool",
        "search_fee_students_tool",
        "get_fee_structures_by_course_tool",
        "get_scholarships_list_tool",
    },
    "export": {
        "export_pending_fee_students_excel_tool",
        "export_course_wise_pending_fee_excel_tool",
        "export_batch_wise_pending_fee_excel_tool",
        "export_fee_defaulters_excel_tool",
        "export_daily_collection_excel_tool",
    },
    "attendance": {"get_student_attendance_tool"},
    "exam": {"get_student_exam_results_tool", "get_exam_result_detail_tool"},
    "enquiry": {"search_enquiries_tool"},
    "dashboard": {"get_dashboard_summary_tool"},
}

GROUP_KEYWORDS: dict[str, tuple[str, ...]] = {
    "export": ("excel", "xlsx", "download", "export", "file", "spreadsheet"),
    "fee": (
        "fee",
        "fees",
        "pending",
        "defaulter",
        "collection",
        "receipt",
        "installment",
        "overdue",
        "balance",
        "paid",
        "ledger",
        "gst",
        "scholarship",
        "transport",
        "hostel",
    ),
    "attendance": ("attendance", "present", "absent"),
    "exam": ("exam", "result", "marks", "grade"),
    "enquiry": ("enquiry", "inquiry", "lead", "prospect"),
    "dashboard": ("dashboard", "summary", "kpi", "overview"),
    "student": ("student", "profile", "roll", "admission", "kitne", "count"),
}

DEFAULT_GROUPS = ("student", "fee", "dashboard")


def detect_groups(message: str) -> set[str]:
    text = (message or "").lower()
    groups = {group for group, words in GROUP_KEYWORDS.items() if any(word in text for word in words)}
    if "export" in groups:
        groups.add("fee")
    return groups


def select_tool_names(message: str) -> set[str]:
    text = (message or "").lower()
    groups = detect_groups(message)
    if not groups:
        groups = set(DEFAULT_GROUPS)
    names = set(BASE_TOOL_NAMES)
    for group in groups:
        names.update(TOOL_GROUPS.get(group, set()))
    if re.search(r"\b(course|courses)\b", text) and re.search(
        r"\b(student|students|kitne|count)\b", text
    ):
        if not re.search(r"\bfee\b", text):
            names.add("get_course_wise_student_count_tool")
    return names
