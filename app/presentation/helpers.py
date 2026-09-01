from __future__ import annotations

import html
from datetime import date, datetime
from typing import Any, Callable


def esc(value: Any) -> str:
    if value is None:
        return "-"
    text = html.unescape(str(value))
    return html.escape(text)


def money(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount == int(amount):
        return f"₹{int(amount):,}"
    return f"₹{amount:,.2f}"


def fmt_date(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d-%b-%Y")
    text = str(value)
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%d-%b-%Y")
        except ValueError:
            continue
    return esc(text)


def pct(value: Any) -> str:
    try:
        return f"{float(value or 0):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def card(title: str, body: str, subtitle: str = "") -> str:
    sub = f'<div class="erp-card-sub">{esc(subtitle)}</div>' if subtitle else ""
    return (
        f'<div class="erp-card">'
        f'<div class="erp-card-title">{esc(title)}</div>{sub}'
        f"{body}</div>"
    )


def note(text: str) -> str:
    return f'<div class="erp-note">{esc(text)}</div>'


def empty(text: str) -> str:
    return f'<div class="erp-empty">{esc(text)}</div>'


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="erp-badge erp-badge-{tone}">{esc(text)}</span>'


def kpis(items: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div class="erp-kpi"><span class="erp-kpi-label">{esc(label)}</span>'
        f'<span class="erp-kpi-value">{value}</span></div>'
        for label, value in items
    )
    return f'<div class="erp-kpi-grid">{cells}</div>'


def table(headers: list[str], rows: list[list[Any]], row_class: Callable | None = None) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cls = row_class(row) if row_class else ""
        cls_attr = f' class="{cls}"' if cls else ""
        cells = "".join(f"<td>{cell if isinstance(cell, str) else esc(cell)}</td>" for cell in row)
        body_rows.append(f"<tr{cls_attr}>{cells}</tr>")
    body = "".join(body_rows) or f'<tr><td colspan="{len(headers)}">No records</td></tr>'
    return (
        '<div class="erp-table-wrap"><table class="erp-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def list_report(
    title: str,
    rows: list[dict],
    columns: list[tuple[str, Callable[[dict], Any]]],
    limit_note: str | None = None,
) -> str:
    if not rows:
        return card(title, empty("No records found."))
    table_rows = []
    for row in rows:
        table_rows.append([col[1](row) for col in columns])
    body = table([c[0] for c in columns], table_rows)
    if limit_note:
        body += note(limit_note)
    return card(title, body)


def overdue_cell(amount: Any, is_overdue: bool = False) -> str:
    if is_overdue:
        return f'<span class="erp-overdue">{money(amount)}</span>'
    return money(amount)


def status_badge(status: Any) -> str:
    text = str(status or "-")
    key = text.lower()
    tone = "neutral"
    if any(w in key for w in ("paid", "complete", "present", "pass", "active")):
        tone = "success"
    elif any(w in key for w in ("overdue", "absent", "fail", "pending", "due")):
        tone = "danger"
    elif any(w in key for w in ("partial", "late", "half")):
        tone = "warning"
    return badge(text, tone)
