from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class ReportDateRange:
    from_date: date | None = None
    to_date: date | None = None

    @property
    def filtered(self) -> bool:
        return self.from_date is not None or self.to_date is not None

    def sp_params(self) -> tuple[None | str, None | str]:
        return (
            self.from_date.isoformat() if self.from_date else None,
            self.to_date.isoformat() if self.to_date else None,
        )


def _parse_date_token(token: str) -> date | None:
    token = (token or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def parse_report_dates(message: str, *, today: date | None = None) -> ReportDateRange:
    """Return a date range only when the user explicitly mentions dates or periods."""
    today = today or date.today()
    text = re.sub(r"\s+", " ", (message or "").strip().lower())
    if not text:
        return ReportDateRange()

    date_token = r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"

    range_match = re.search(
        rf"(?:from|between)\s+{date_token}\s+(?:to|and|-)\s+{date_token}",
        text,
    )
    if range_match:
        start = _parse_date_token(range_match.group(1))
        end = _parse_date_token(range_match.group(2))
        if start and end:
            return ReportDateRange(from_date=min(start, end), to_date=max(start, end))

    last_days = re.search(r"(?:last|past|previous)\s+(\d{1,3})\s+days?", text)
    if last_days:
        days = max(1, min(int(last_days.group(1)), 366))
        return ReportDateRange(from_date=today - timedelta(days=days - 1), to_date=today)

    if re.search(r"\bdays?\b", text):
        days_match = re.search(r"(\d{1,3})\s+days?", text)
        if days_match and re.search(r"\b(last|past|previous|for)\b", text):
            days = max(1, min(int(days_match.group(1)), 366))
            return ReportDateRange(from_date=today - timedelta(days=days - 1), to_date=today)

    if re.search(r"\btoday\b|\baaj\b", text):
        return ReportDateRange(from_date=today, to_date=today)

    if re.search(r"\byesterday\b|\bkal\b", text):
        yesterday = today - timedelta(days=1)
        return ReportDateRange(from_date=yesterday, to_date=yesterday)

    if re.search(r"\bthis month\b|\bcurrent month\b|\bis mahine\b", text):
        return ReportDateRange(from_date=today.replace(day=1), to_date=today)

    if re.search(r"\blast month\b|\bpichle mahine\b", text):
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        return ReportDateRange(
            from_date=last_month_end.replace(day=1),
            to_date=last_month_end,
        )

    single = re.search(rf"\b{date_token}\b", text)
    if single and re.search(r"\bon\b|\bdate\b|\bfor\b", text):
        parsed = _parse_date_token(single.group(1))
        if parsed:
            return ReportDateRange(from_date=parsed, to_date=parsed)

    return ReportDateRange()
