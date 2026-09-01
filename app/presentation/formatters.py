from __future__ import annotations

from typing import Any, Callable

from app.presentation.payloads import html_payload, text_payload
from app.presentation.helpers import (
    badge,
    card,
    empty,
    esc,
    fmt_date,
    kpis,
    list_report,
    money,
    note,
    overdue_cell,
    pct,
    status_badge,
    table,
)

Column = tuple[str, Callable[[dict], Any]]


def _dated_title(base: str, data: dict) -> str:
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    if not from_date and not to_date:
        return base
    start = fmt_date(from_date) if from_date else "Start"
    end = fmt_date(to_date) if to_date else "End"
    return f"{base} ({start} – {end})"


def _student_options(students: list[dict]) -> list[dict]:
    options = []
    for s in students:
        reg = s.get("student_reg_no")
        if not reg:
            continue
        options.append(
            {
                "student_reg_no": reg,
                "label": (
                    f"{s.get('name', '-')} | {s.get('course') or '-'} | "
                    f"Roll {s.get('roll_no') or '-'} | Father: {s.get('father_name') or '-'}"
                ),
            }
        )
    return options


def format_search_students(data: dict) -> dict:
    if data.get("needs_more_info"):
        hint = data.get("hint") or "Please enter at least 2 characters to search."
        return html_payload(card("Student Search", note(hint)))

    students = data.get("students") or []
    if not students:
        return html_payload(card("Student Search", empty("No students found for this branch.")))

    options = _student_options(students)
    rows = [
        [esc(s.get("name")), esc(s.get("course")), esc(s.get("roll_no")), esc(s.get("father_name"))]
        for s in students
    ]
    body = table(["Name", "Course", "Roll No", "Father"], rows)
    if len(students) > 1:
        body += note("Multiple students found — select one below to continue.")
    return html_payload(card(f"Students Found ({len(students)})", body), options=options or None)


def format_get_student_profile(data: dict) -> dict:
    if not data.get("found"):
        return html_payload(card("Student Profile", empty("Student not found in this branch.")))

    body = kpis(
        [
            ("Name", esc(data.get("name"))),
            ("Course", esc(data.get("course"))),
            ("Section", esc(data.get("section"))),
            ("Roll No", esc(data.get("roll_no"))),
            ("Father", esc(data.get("father_name"))),
            ("Status", status_badge(data.get("status"))),
            ("Admission No", esc(data.get("admission_no"))),
        ]
    )
    return html_payload(card("Student Profile", body))


def format_get_student_fee_summary(data: dict) -> dict:
    fees = data.get("fees") or []
    if not data.get("found") or not fees:
        return html_payload(card("Fee Summary", empty("No fee assignment found for this student.")))

    rows = []
    total = paid = balance = 0.0
    for f in fees:
        gt = float(f.get("grand_total") or 0)
        pd = float(f.get("paid_amount") or 0)
        bal = float(f.get("balance_amount") or 0)
        total += gt
        paid += pd
        balance += bal
        rows.append(
            [
                esc(f.get("course")),
                esc(f.get("batch") or f.get("session")),
                money(gt),
                money(pd),
                overdue_cell(bal, bal > 0),
                status_badge(f.get("status")),
            ]
        )

    summary = kpis(
        [
            ("Total Fee", money(total)),
            ("Paid", money(paid)),
            ("Balance", money(balance)),
        ]
    )
    body = summary + table(
        ["Course", "Batch/Session", "Total", "Paid", "Balance", "Status"],
        rows,
    )
    return html_payload(card("Fee Summary", body))


def format_get_student_fee_installments(data: dict) -> dict:
    items = data.get("installments") or []
    if not data.get("found") or not items:
        msg = data.get("message") or "No installment records found."
        return html_payload(card("Fee Installments", empty(msg)))

    rows = []
    for i in items:
        rows.append(
            [
                esc(i.get("fee_head")),
                esc(i.get("installment_no")),
                fmt_date(i.get("due_date")),
                money(i.get("payable")),
                money(i.get("paid")),
                overdue_cell(i.get("balance"), i.get("is_overdue")),
                status_badge(i.get("status")),
            ]
        )
    body = table(
        ["Fee Head", "Inst.", "Due Date", "Payable", "Paid", "Balance", "Status"],
        rows,
    )
    return html_payload(card("Fee Installments", body, subtitle=f"Student #{data.get('student_reg_no')}"))


def format_get_student_fee_overdue(data: dict) -> dict:
    items = data.get("overdue") or []
    if not data.get("found") or not items:
        return html_payload(card("Overdue Fees", empty("No overdue installments — all clear.")))

    total = sum(float(i.get("amount") or 0) for i in items)
    body = kpis([("Total Overdue", money(total)), ("Installments", str(len(items)))])
    rows = [
        [
            esc(i.get("fee_head")),
            fmt_date(i.get("due_date")),
            money(i.get("amount")),
            f'{int(i.get("days_overdue") or 0)} days',
        ]
        for i in items
    ]
    body += table(["Fee Head", "Due Date", "Amount", "Overdue By"], rows)
    return html_payload(card("Overdue Fees", body))


def format_get_student_receipt_history(data: dict) -> dict:
    items = data.get("receipts") or []
    if not data.get("found") or not items:
        return html_payload(card("Receipt History", empty("No receipts found for this student.")))

    rows = [
        [
            fmt_date(i.get("date")),
            esc(i.get("mode")),
            money(i.get("amount")),
            money(i.get("discount")),
            esc(i.get("reference_masked")),
            status_badge(i.get("status")),
        ]
        for i in items
    ]
    body = table(["Date", "Mode", "Amount", "Discount", "Reference", "Status"], rows)
    body += note("Bank/reference numbers are masked for security.")
    return html_payload(card("Receipt History", body))


def format_get_student_fee_ledger(data: dict) -> dict:
    return html_payload(
        list_report(
            "Fee Ledger",
            data.get("ledger") or [],
            [
                ("Course", lambda r: esc(r.get("course"))),
                ("Structure", lambda r: esc(r.get("structure"))),
                ("Total", lambda r: money(r.get("grand_total"))),
                ("Paid", lambda r: money(r.get("paid"))),
                ("Discount", lambda r: money(r.get("discount"))),
                ("Balance", lambda r: money(r.get("balance"))),
                ("Status", lambda r: status_badge(r.get("status"))),
            ],
        )
    )


def format_get_student_fee_discount(data: dict) -> dict:
    return html_payload(
        list_report(
            "Discount / Scholarship",
            data.get("discounts") or [],
            [
                ("Course", lambda r: esc(r.get("course"))),
                ("Fee Head", lambda r: esc(r.get("fee_head"))),
                ("Discount", lambda r: money(r.get("discount_amount"))),
                ("Receipt Date", lambda r: fmt_date(r.get("receipt_date"))),
            ],
        )
    )


def format_get_student_transport_fee(data: dict) -> dict:
    return html_payload(
        list_report(
            "Transport Fee",
            data.get("transport") or [],
            [
                ("Route", lambda r: esc(r.get("route"))),
                ("Stop", lambda r: esc(r.get("stop"))),
                ("Payable", lambda r: money(r.get("payable"))),
                ("Status", lambda r: status_badge(r.get("status"))),
            ],
        )
    )


def format_get_student_hostel_fee(data: dict) -> dict:
    return html_payload(
        list_report(
            "Hostel Fee",
            data.get("hostel") or [],
            [
                ("Hostel", lambda r: esc(r.get("hostel"))),
                ("Room", lambda r: esc(r.get("room"))),
                ("Balance", lambda r: money(r.get("balance"))),
            ],
        )
    )


def format_get_fee_due_alert(data: dict) -> dict:
    alert = data.get("alert") or {}
    if not data.get("found"):
        return html_payload(card("Fee Due Alert", empty("No pending or overdue fee alerts today.")))

    body = kpis(
        [
            ("Overdue Amount", money(alert.get("overdue_amount"))),
            ("Overdue Students", str(alert.get("overdue_students", 0))),
            ("Due Today", money(alert.get("due_today_amount"))),
            ("Next 7 Days", money(alert.get("upcoming_7_days_amount"))),
            ("Total Pending", money(alert.get("total_pending_amount"))),
            ("Max Days Overdue", str(alert.get("max_days_overdue", 0))),
        ]
    )
    return html_payload(card("Branch Fee Alert", body))


def format_get_fee_branch_snapshot(data: dict) -> dict:
    snap = data.get("snapshot") or {}
    if not data.get("found"):
        return html_payload(card("Branch Fee Snapshot", empty("No snapshot data available.")))

    money_keys = {
        "today_collection",
        "total_collected",
        "total_assigned",
        "total_balance",
        "total_pending_balance",
        "overdue_amount",
    }
    count_keys = {"active_students", "overdue_students", "paid_receipts"}
    labels = {
        "today_collection": "Today's Collection",
        "total_collected": "Total Collected",
        "total_assigned": "Total Assigned",
        "total_balance": "Total Balance",
        "total_pending_balance": "Pending Balance",
        "overdue_amount": "Overdue Amount",
        "active_students": "Active Students",
        "overdue_students": "Overdue Students",
        "paid_receipts": "Paid Receipts",
    }
    items = []
    for key, label in labels.items():
        if key not in snap:
            continue
        val = snap[key]
        if key in money_keys:
            display = money(val)
        elif key in count_keys:
            display = str(val)
        else:
            display = esc(val)
        items.append((label, display))

    return html_payload(card(_dated_title("Branch Fee Snapshot", data), kpis(items)))


def format_get_fee_daily_collection(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Daily Collection", data),
            data.get("collections") or [],
            [
                ("Date", lambda r: fmt_date(r.get("date"))),
                ("Mode", lambda r: esc(r.get("mode"))),
                ("Receipts", lambda r: str(r.get("receipts", 0))),
                ("Amount", lambda r: money(r.get("amount"))),
            ],
        )
    )


def format_get_fee_pending_due_list(data: dict) -> dict:
    status = data.get("due_status") or "Overdue"
    return html_payload(
        list_report(
            f"Pending Due — {status}",
            data.get("items") or [],
            [
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("Fee Head", lambda r: esc(r.get("fee_head"))),
                ("Due Date", lambda r: fmt_date(r.get("due_date"))),
                ("Balance", lambda r: money(r.get("balance"))),
            ],
        )
    )


def format_get_fee_defaulter_list(data: dict) -> dict:
    return html_payload(
        list_report(
            "Fee Defaulters",
            data.get("defaulters") or [],
            [
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("Batch", lambda r: esc(r.get("batch"))),
                ("Overdue", lambda r: money(r.get("overdue_amount"))),
                ("Days", lambda r: str(r.get("max_days_overdue", 0))),
            ],
            limit_note="Showing top 15 defaulters.",
        )
    )


def format_get_pending_fee_students(data: dict) -> dict:
    if data.get("message") and not data.get("students"):
        return html_payload(card("Pending Fee Students", empty(data["message"])))
    return html_payload(
        list_report(
            "Pending Fee Students",
            data.get("students") or [],
            [
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("Batch", lambda r: esc(r.get("batch"))),
                ("Balance", lambda r: money(r.get("balance"))),
                ("Pending %", lambda r: pct(r.get("pending_percent"))),
            ],
        )
    )


def format_get_fee_course_summary(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Course-wise Fee Summary", data),
            data.get("courses") or [],
            [
                ("Course", lambda r: esc(r.get("course"))),
                ("Assigned", lambda r: money(r.get("assigned"))),
                ("Collected", lambda r: money(r.get("collected"))),
                ("Balance", lambda r: money(r.get("balance"))),
            ],
        )
    )


def format_get_course_wise_student_count(data: dict) -> dict:
    courses = data.get("courses") or []
    if not courses:
        return html_payload(
            card(_dated_title("Course-wise Student Count", data), empty("No student data found."))
        )

    rows = [[esc(c.get("course")), str(c.get("students", 0))] for c in courses]
    total = int(data.get("total_students") or sum(c.get("students", 0) for c in courses))
    body = table(["Course", "Student Count"], rows)
    body += note(f"Total students across courses: {total}")
    return html_payload(card(_dated_title("Course-wise Student Count", data), body))


def format_get_fee_batch_summary(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Batch-wise Fee Summary", data),
            data.get("batches") or [],
            [
                ("Course", lambda r: esc(r.get("course"))),
                ("Batch", lambda r: esc(r.get("batch"))),
                ("Assigned", lambda r: money(r.get("assigned"))),
                ("Collected", lambda r: money(r.get("collected"))),
                ("Balance", lambda r: money(r.get("balance"))),
            ],
        )
    )


def format_get_fee_head_summary(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Fee Head Summary", data),
            data.get("fee_heads") or [],
            [
                ("Fee Head", lambda r: esc(r.get("fee_head"))),
                ("Demand", lambda r: money(r.get("demand"))),
                ("Collected", lambda r: money(r.get("collected"))),
                ("Balance", lambda r: money(r.get("balance"))),
            ],
        )
    )


def format_get_fee_payment_mode_summary(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Payment Mode Summary", data),
            data.get("modes") or [],
            [
                ("Mode", lambda r: esc(r.get("mode"))),
                ("Receipts", lambda r: str(r.get("receipts", 0))),
                ("Amount", lambda r: money(r.get("amount"))),
            ],
        )
    )


def format_get_fee_installment_calendar(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Installment Calendar", data),
            data.get("calendar") or [],
            [
                ("Due Date", lambda r: fmt_date(r.get("due_date"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("Students Due", lambda r: str(r.get("students_due", 0))),
                ("Amount", lambda r: money(r.get("amount_due"))),
            ],
        )
    )


def format_get_fee_receipt_register(data: dict) -> dict:
    return html_payload(
        list_report(
            _dated_title("Receipt Register", data),
            data.get("receipts") or [],
            [
                ("Date", lambda r: fmt_date(r.get("date"))),
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Mode", lambda r: esc(r.get("mode"))),
                ("Amount", lambda r: money(r.get("amount"))),
                ("Status", lambda r: status_badge(r.get("status"))),
            ],
        )
    )


def format_get_fee_aging_report(data: dict) -> dict:
    return html_payload(
        list_report(
            "Fee Aging Report",
            data.get("aging") or [],
            [
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("0-30 days", lambda r: money(r.get("bucket_0_30"))),
                ("31-60 days", lambda r: money(r.get("bucket_31_60"))),
                ("61-90 days", lambda r: money(r.get("bucket_61_90"))),
                ("90+ days", lambda r: money(r.get("bucket_90_plus"))),
            ],
        )
    )


def format_get_fee_rollback_receipts(data: dict) -> dict:
    return html_payload(
        list_report(
            "Rollback Receipts",
            data.get("rollbacks") or [],
            [
                ("Date", lambda r: fmt_date(r.get("date"))),
                ("Student", lambda r: esc(r.get("student_name"))),
                ("Amount", lambda r: money(r.get("amount"))),
                ("Reason", lambda r: esc(r.get("reason"))),
            ],
        )
    )


def format_get_fee_tax_gst_summary(data: dict) -> dict:
    summary = data.get("summary") or {}
    if not data.get("found") or not summary:
        return html_payload(card("GST Summary", empty("No GST summary available.")))
    body = kpis(
        [
            ("Taxable Amount", money(summary.get("taxable_amount"))),
            ("Non-Taxable", money(summary.get("non_taxable_amount"))),
            ("GST Collected", money(summary.get("gst_amount"))),
            ("Total Collected", money(summary.get("total_collected"))),
        ]
    )
    return html_payload(card("GST / Tax Summary", body))


def format_search_fee_students(data: dict) -> dict:
    students = data.get("students") or []
    if not students:
        return html_payload(card("Fee Student Search", empty("No students found.")))
    options = []
    for s in students:
        reg = s.get("student_reg_no")
        if reg:
            options.append(
                {
                    "student_reg_no": reg,
                    "label": (
                        f"{s.get('name', '-')} | {s.get('course') or '-'} | "
                        f"Balance {money(s.get('balance'))}"
                    ),
                }
            )
    html = list_report(
        "Fee Student Search",
        students,
        [
            ("Student", lambda r: esc(r.get("name"))),
            ("Course", lambda r: esc(r.get("course"))),
            ("Batch", lambda r: esc(r.get("batch"))),
            ("Balance", lambda r: money(r.get("balance"))),
            ("Status", lambda r: status_badge(r.get("status"))),
        ],
    )
    return html_payload(html, options=options or None)


def format_get_fee_structures_by_course(data: dict) -> dict:
    return html_payload(
        list_report(
            "Fee Structures",
            data.get("structures") or [],
            [
                ("Structure", lambda r: esc(r.get("name"))),
                ("Total", lambda r: money(r.get("grand_total"))),
            ],
        )
    )


def format_get_scholarships_list(data: dict) -> dict:
    return html_payload(
        list_report(
            "Scholarships / Schemes",
            data.get("scholarships") or [],
            [
                ("Name", lambda r: esc(r.get("name"))),
                ("Type", lambda r: esc(r.get("type"))),
                ("Value", lambda r: esc(r.get("value"))),
            ],
        )
    )


def format_get_student_attendance(data: dict) -> dict:
    if not data.get("found"):
        return html_payload(card("Attendance", empty("No attendance records found for this student.")))

    overall = data.get("overall") or {}
    body = kpis(
        [
            ("Attendance %", pct(overall.get("percentage"))),
            ("Present", str(overall.get("present", 0))),
            ("Absent", str(overall.get("absent", 0))),
            ("Late", str(overall.get("late", 0))),
            ("Leave", str(overall.get("leave", 0))),
        ]
    )

    by_course = data.get("by_course") or []
    if by_course:
        rows = [
            [
                esc(c.get("course")),
                pct(c.get("percentage")),
                str(c.get("present", 0)),
                str(c.get("absent", 0)),
            ]
            for c in by_course
        ]
        body += table(["Course", "Attendance %", "Present", "Absent"], rows)

    recent = data.get("recent_days") or []
    if recent:
        rows = [
            [
                fmt_date(r.get("date")),
                esc(r.get("subject") or r.get("course")),
                status_badge(r.get("status")),
            ]
            for r in recent
        ]
        body += note("Recent days") + table(["Date", "Subject/Course", "Status"], rows)

    title = f"Attendance — {data.get('student_name') or data.get('student_reg_no')}"
    return html_payload(card(title, body))


def format_get_dashboard_summary(data: dict) -> dict:
    if not data.get("found") and data.get("message"):
        return html_payload(card("Dashboard", empty(data["message"])))

    parts = []
    student_kpis = data.get("student_kpis") or []
    if student_kpis:
        items = [(esc(k.get("label")), str(int(k.get("metric1", 0)))) for k in student_kpis[:6]]
        parts.append(note("Students") + kpis(items))

    fee_kpis = data.get("fee_kpis") or []
    if fee_kpis and not data.get("fee_section_hidden"):
        items = [(esc(k.get("label")), money(k.get("metric1"))) for k in fee_kpis[:6]]
        parts.append(note("Fee") + kpis(items))

    courses = data.get("top_courses_by_students") or []
    if courses:
        rows = [[esc(c.get("label")), str(int(c.get("metric1", 0)))] for c in courses]
        parts.append(note("Top Courses") + table(["Course", "Students"], rows))

    if not parts:
        return html_payload(card("Dashboard Summary", empty("No dashboard data available.")))
    return html_payload(card("Branch Dashboard Summary", "".join(parts)))


def format_search_enquiries(data: dict) -> dict:
    if data.get("needs_more_info"):
        return text_payload(data.get("hint") or "Enter at least 2 characters.")
    enquiries = data.get("enquiries") or []
    if not enquiries:
        return html_payload(card("Enquiry Search", empty("No enquiries found.")))
    return html_payload(
        list_report(
            f"Enquiries ({len(enquiries)})",
            enquiries,
            [
                ("Name", lambda r: esc(r.get("name"))),
                ("Date", lambda r: fmt_date(r.get("enquiry_date"))),
                ("Follow-up", lambda r: fmt_date(r.get("followup_date"))),
                ("Status", lambda r: status_badge(r.get("status"))),
                ("Interest", lambda r: esc(r.get("course_interest"))),
            ],
        )
    )


def format_list_student_exam_results(data: dict) -> dict:
    exams = data.get("exams") or []
    if not data.get("found") or not exams:
        return html_payload(card("Exam Results", empty("No exam results found for this student.")))
    return html_payload(
        list_report(
            "Exam Results",
            exams,
            [
                ("Exam", lambda r: esc(r.get("exam_name"))),
                ("Type", lambda r: esc(r.get("exam_type"))),
                ("Course", lambda r: esc(r.get("course"))),
                ("Marks", lambda r: f'{r.get("marks_obtained", 0)}/{r.get("max_marks", 0)}'),
                ("%", lambda r: pct(r.get("percentage"))),
                ("Grade", lambda r: esc(r.get("grade"))),
                ("Result", lambda r: status_badge(r.get("result_status"))),
            ],
        )
    )


def format_get_exam_result_detail(data: dict) -> dict:
    if not data.get("found"):
        return html_payload(card("Exam Detail", empty("Exam result not found.")))
    summary = data.get("summary") or {}
    body = kpis(
        [
            ("Exam", esc(summary.get("exam_name"))),
            ("Percentage", pct(summary.get("percentage"))),
            ("Grade", esc(summary.get("grade"))),
            ("Result", status_badge(summary.get("result_status"))),
        ]
    )
    subjects = data.get("subjects") or []
    if subjects:
        rows = [
            [
                esc(s.get("subject")),
                f'{s.get("marks_obtained", 0)}/{s.get("max_marks", 0)}',
                status_badge(s.get("status")),
            ]
            for s in subjects
        ]
        body += table(["Subject", "Marks", "Status"], rows)
    return html_payload(card("Exam Result Detail", body))


def _format_excel_export(data: dict, title: str) -> dict:
    if not data.get("file_id"):
        msg = data.get("message") or "No data available for Excel export."
        return html_payload(card(title, empty(msg)))

    body = kpis(
        [
            ("Rows exported", str(data.get("row_count", 0))),
            ("File name", esc(data.get("filename"))),
        ]
    )
    body += note(data.get("summary") or "Excel file is ready to download.")
    body += note("Sheets include formatted tables and pie/bar charts where applicable.")
    attachments = [
        {
            "file_id": data["file_id"],
            "filename": data["filename"],
            "label": "Download Excel",
        }
    ]
    return html_payload(card(title, body), attachments=attachments)


def format_export_pending_fee_students_excel(data: dict) -> dict:
    return _format_excel_export(data, "Pending Fee Students — Excel Export")


def format_export_course_wise_pending_fee_excel(data: dict) -> dict:
    return _format_excel_export(data, "Course-wise Pending Fee — Excel Export")


def format_export_batch_wise_pending_fee_excel(data: dict) -> dict:
    return _format_excel_export(data, "Batch/Session-wise Pending Fee — Excel Export")


def format_export_daily_collection_excel(data: dict) -> dict:
    return _format_excel_export(data, "Daily Collection — Excel Export")


def format_export_fee_defaulters_excel(data: dict) -> dict:
    return _format_excel_export(data, "Fee Defaulters — Excel Export")


def format_generic(data: dict) -> dict:
    if data.get("message") and not any(
        k in data for k in ("students", "fees", "items", "rows", "found", "total")
    ):
        return text_payload(str(data["message"]))
    if data.get("success") is False:
        return text_payload(data.get("message") or "Request failed.")
    if data.get("success") and data.get("message"):
        return text_payload(str(data["message"]))

    rows = []
    for key, value in data.items():
        if key in ("allowed",):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append([esc(key.replace("_", " ").title()), esc(value)])
    if rows:
        return html_payload(card("Details", table(["Field", "Value"], rows)))
    return html_payload(card("Details", empty("No displayable data.")))


FORMATTERS: dict[str, Callable[[dict], dict]] = {
    "search_students": format_search_students,
    "get_student_profile": format_get_student_profile,
    "get_student_fee_summary": format_get_student_fee_summary,
    "get_student_fee_installments": format_get_student_fee_installments,
    "get_student_fee_overdue": format_get_student_fee_overdue,
    "get_student_receipt_history": format_get_student_receipt_history,
    "get_student_fee_ledger": format_get_student_fee_ledger,
    "get_student_fee_discount": format_get_student_fee_discount,
    "get_student_transport_fee": format_get_student_transport_fee,
    "get_student_hostel_fee": format_get_student_hostel_fee,
    "get_fee_due_alert": format_get_fee_due_alert,
    "get_fee_branch_snapshot": format_get_fee_branch_snapshot,
    "get_fee_daily_collection": format_get_fee_daily_collection,
    "get_fee_pending_due_list": format_get_fee_pending_due_list,
    "get_fee_defaulter_list": format_get_fee_defaulter_list,
    "get_pending_fee_students": format_get_pending_fee_students,
    "get_fee_course_summary": format_get_fee_course_summary,
    "get_course_wise_student_count": format_get_course_wise_student_count,
    "get_fee_batch_summary": format_get_fee_batch_summary,
    "get_fee_head_summary": format_get_fee_head_summary,
    "get_fee_payment_mode_summary": format_get_fee_payment_mode_summary,
    "get_fee_installment_calendar": format_get_fee_installment_calendar,
    "get_fee_receipt_register": format_get_fee_receipt_register,
    "get_fee_aging_report": format_get_fee_aging_report,
    "get_fee_rollback_receipts": format_get_fee_rollback_receipts,
    "get_fee_tax_gst_summary": format_get_fee_tax_gst_summary,
    "search_fee_students": format_search_fee_students,
    "get_fee_structures_by_course": format_get_fee_structures_by_course,
    "get_scholarships_list": format_get_scholarships_list,
    "get_student_attendance": format_get_student_attendance,
    "get_dashboard_summary": format_get_dashboard_summary,
    "search_enquiries": format_search_enquiries,
    "list_student_exam_results": format_list_student_exam_results,
    "get_exam_result_detail": format_get_exam_result_detail,
    "export_pending_fee_students_excel": format_export_pending_fee_students_excel,
    "export_course_wise_pending_fee_excel": format_export_course_wise_pending_fee_excel,
    "export_batch_wise_pending_fee_excel": format_export_batch_wise_pending_fee_excel,
    "export_fee_defaulters_excel": format_export_fee_defaulters_excel,
    "export_daily_collection_excel": format_export_daily_collection_excel,
}
