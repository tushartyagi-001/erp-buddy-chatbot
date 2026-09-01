from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from app.auth.context import ChatContext
from app.routing.helpers import extract_student_name, normalize_message, parse_student_selection, parse_tool_payload
from app.utils.date_range import parse_report_dates
from app.services import export_service as ex
from app.services import fee_service as fs
from app.services.attendance_service import get_student_attendance
from app.services.dashboard_service import get_dashboard_summary
from app.services.enquiry_service import search_enquiries
from app.services.exam_service import list_student_exam_results
from app.services.student_service import get_student_profile, search_students
from app.tools.common import run_tool
from app.tools.student.tools import get_selected_student, set_selected_student


@dataclass(frozen=True)
class IntentRule:
    intent_id: str
    patterns: tuple[str, ...]
    handler: Callable[..., dict[str, Any] | None]


def _meta(intent_id: str) -> dict[str, Any]:
    return {"route": "direct", "intent": intent_id, "ai_used": False}


def _dates_from_message(message: str) -> tuple[date | None, date | None]:
    dr = parse_report_dates(message)
    return dr.from_date, dr.to_date


def _from_service(func, **kwargs) -> dict[str, Any] | None:
    raw = run_tool(func, **kwargs)
    parsed = parse_tool_payload(raw)
    if not parsed:
        return None
    parsed["_meta"] = _meta(func.__name__)
    return parsed


def _student_flow(
    ctx: ChatContext,
    message: str,
    selected_reg_no: int | None,
    intent_id: str,
    service_func,
    **kwargs,
) -> dict[str, Any] | None:
    reg = selected_reg_no or get_selected_student()
    if reg:
        result = _from_service(service_func, student_reg_no=int(reg), **kwargs)
        if result:
            result["_meta"] = _meta(intent_id)
        return result

    name = extract_student_name(message)
    if not name:
        return None

    search_raw = run_tool(search_students, term=name, limit=10)
    search = parse_tool_payload(search_raw)
    if not search:
        return None

    options = search.get("options") or []
    if len(options) == 1:
        reg_no = int(options[0]["student_reg_no"])
        set_selected_student(reg_no)
        result = _from_service(service_func, student_reg_no=reg_no, **kwargs)
        if result:
            result["_meta"] = _meta(intent_id)
        return result

    search["_meta"] = _meta("student_disambiguation")
    return search


def _handle_export_pending(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(ex.export_pending_fee_students_excel)


def _handle_export_course(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        ex.export_course_wise_pending_fee_excel,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_export_batch(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        ex.export_batch_wise_pending_fee_excel,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_export_defaulter(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(ex.export_fee_defaulters_excel)


def _handle_export_daily(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        ex.export_daily_collection_excel,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_pending_fee_list(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(fs.get_pending_fee_students)


def _handle_defaulter_list(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(fs.get_fee_defaulter_list)


def _handle_daily_collection(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    result = _from_service(
        fs.get_fee_daily_collection,
        from_date=from_date,
        to_date=to_date,
    )
    if result:
        result["_meta"] = _meta("daily_collection")
    return result


def _handle_due_alert(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(fs.get_fee_due_alert)


def _handle_branch_snapshot(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        fs.get_fee_branch_snapshot,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_dashboard(_ctx, _message, _params, _selected) -> dict[str, Any] | None:
    return _from_service(get_dashboard_summary)


def _handle_course_student_count(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        fs.get_course_wise_student_count,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_course_summary(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        fs.get_fee_course_summary,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_batch_summary(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    from_date, to_date = _dates_from_message(message)
    return _from_service(
        fs.get_fee_batch_summary,
        from_date=from_date,
        to_date=to_date,
    )


def _handle_fee_summary(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_fee_summary", fs.get_student_fee_summary)


def _handle_installments(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_installments", fs.get_student_fee_installments)


def _handle_overdue(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_overdue", fs.get_student_fee_overdue)


def _handle_receipts(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_receipts", fs.get_student_receipt_history)


def _handle_attendance(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_attendance", get_student_attendance)


def _handle_exam(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_exam", list_student_exam_results)


def _handle_profile(ctx, message, _params, selected) -> dict[str, Any] | None:
    return _student_flow(ctx, message, selected, "student_profile", get_student_profile)


def _handle_enquiry(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    term = extract_student_name(message) or message.strip()
    if len(term) < 2:
        return None
    return _from_service(search_enquiries, term=term, limit=10)


def _handle_student_search(_ctx, message, _params, _selected) -> dict[str, Any] | None:
    if parse_student_selection(message, _selected):
        return None
    if not re.search(r"\b(search|find|show|list|student)\b", message, re.I):
        return None
    return _from_service(search_students, term=message, limit=10)


INTENT_RULES: tuple[IntentRule, ...] = (
    IntentRule(
        "export_pending_excel",
        (
            r"\b(excel|xlsx|download|export|spreadsheet|file)\b.*\bpending\b.*\bfee",
            r"\bpending\b.*\bfee\b.*\b(excel|xlsx|download|export|spreadsheet|file)\b",
        ),
        _handle_export_pending,
    ),
    IntentRule(
        "export_course_excel",
        (
            r"\b(excel|xlsx|download|export|spreadsheet|file)\b.*\bcourse\b.*\bfee",
            r"\bcourse\b.*\bwise\b.*\b(excel|xlsx|download|export)\b",
        ),
        _handle_export_course,
    ),
    IntentRule(
        "export_batch_excel",
        (
            r"\b(excel|xlsx|download|export|spreadsheet|file)\b.*\b(batch|session)\b",
            r"\b(batch|session)\b.*\bwise\b.*\b(excel|xlsx|download|export)\b",
        ),
        _handle_export_batch,
    ),
    IntentRule(
        "export_defaulter_excel",
        (
            r"\b(excel|xlsx|download|export|spreadsheet|file)\b.*\bdefaulter",
            r"\bdefaulter\b.*\b(excel|xlsx|download|export)\b",
        ),
        _handle_export_defaulter,
    ),
    IntentRule(
        "export_daily_excel",
        (
            r"\b(excel|xlsx|download|export|spreadsheet|file)\b.*\b(daily|collection)\b",
            r"\bdaily\b.*\bcollection\b.*\b(excel|xlsx|download|export)\b",
        ),
        _handle_export_daily,
    ),
    IntentRule("pending_fee_list", (r"\bpending\b.*\bfee\b.*\b(student|list|students)\b", r"\bpending fee students\b"), _handle_pending_fee_list),
    IntentRule("defaulter_list", (r"\bdefaulter", r"\bdefault(er|ers)\b.*\bfee\b"), _handle_defaulter_list),
    IntentRule("daily_collection", (r"\bdaily\b.*\bcollection\b", r"\bcollection\b.*\blast\b.*\bday"), _handle_daily_collection),
    IntentRule("due_alert", (r"\bfee\b.*\bdue\b.*\balert\b", r"\boverdue\b.*\balert\b", r"\bdue today\b"), _handle_due_alert),
    IntentRule("branch_snapshot", (r"\bbranch\b.*\bfee\b.*\bsnapshot\b", r"\bfee snapshot\b"), _handle_branch_snapshot),
    IntentRule("dashboard", (r"\bdashboard\b", r"\bbranch summary\b", r"\bkpi\b"), _handle_dashboard),
    IntentRule(
        "course_student_count",
        (
            r"\bkis course\b.*\bkitne\b.*\bstudent",
            r"\bkitne\b.*\bstudent\b.*\bcourse",
            r"\bcourse\b.*\b(student|students)\b.*\b(count|kitne|number|how many|hai)\b",
            r"\b(student|students)\b.*\b(course|courses)\b.*\b(count|kitne|wise|number|how many)\b",
            r"\bcourse wise\b.*\bstudent\b.*\bcount\b",
            r"\bhow many\b.*\bstudent\b.*\b(course|courses)\b",
        ),
        _handle_course_student_count,
    ),
    IntentRule("course_summary", (r"\bcourse\b.*\bwise\b.*\bfee\b", r"\bcourse fee summary\b"), _handle_course_summary),
    IntentRule("batch_summary", (r"\bbatch\b.*\bwise\b.*\bfee\b", r"\bsession\b.*\bwise\b.*\bfee\b"), _handle_batch_summary),
    IntentRule("student_fee_summary", (r"\bfee\b.*\b(status|summary|detail)\b", r"\b(status|summary)\b.*\bfee\b"), _handle_fee_summary),
    IntentRule("student_installments", (r"\binstallment", r"\bfee plan\b"), _handle_installments),
    IntentRule("student_overdue", (r"\boverdue\b.*\bfee\b", r"\bfee\b.*\boverdue\b"), _handle_overdue),
    IntentRule("student_receipts", (r"\breceipt\b.*\bhistory\b", r"\bpayment history\b"), _handle_receipts),
    IntentRule("student_attendance", (r"\battendance\b",), _handle_attendance),
    IntentRule("student_exam", (r"\bexam\b.*\bresult", r"\bresult\b.*\bexam\b"), _handle_exam),
    IntentRule("student_profile", (r"\bstudent profile\b", r"\bprofile\b.*\bstudent\b"), _handle_profile),
    IntentRule("enquiry_search", (r"\benquir", r"\binquiry\b", r"\blead\b"), _handle_enquiry),
    IntentRule("student_search", (r"\bsearch\b.*\bstudent", r"\bfind\b.*\bstudent", r"\bstudent\b.*\bsearch\b"), _handle_student_search),
)


def match_intent(message: str) -> str | None:
    text = normalize_message(message)
    for rule in INTENT_RULES:
        for pattern in rule.patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return rule.intent_id
    return None


def try_direct_route(
    ctx: ChatContext,
    message: str,
    selected_student_reg_no: int | None,
) -> dict[str, Any] | None:
    text = normalize_message(message)
    for rule in INTENT_RULES:
        matched = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in rule.patterns)
        if not matched:
            continue
        result = rule.handler(ctx, message, {}, selected_student_reg_no)
        if result is not None:
            return result
    return None
