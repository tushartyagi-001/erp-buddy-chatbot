from __future__ import annotations

from langchain_core.tools import tool

from app.services import export_service as ex
from app.tools.common import run_tool


@tool
def export_pending_fee_students_excel_tool(
    course_id: int = 0, batch_id: int = 0, search_text: str = ""
) -> str:
    """Export pending fee students to Excel with charts."""
    return run_tool(
        ex.export_pending_fee_students_excel,
        course_id=course_id,
        batch_id=batch_id,
        search_text=search_text,
    )


@tool
def export_course_wise_pending_fee_excel_tool(
    from_date: str = "", to_date: str = ""
) -> str:
    """Export course-wise pending fee Excel with charts."""
    from datetime import date

    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    return run_tool(ex.export_course_wise_pending_fee_excel, from_date=fd, to_date=td)


@tool
def export_batch_wise_pending_fee_excel_tool(
    course_id: int = 0, from_date: str = "", to_date: str = ""
) -> str:
    """Export batch/session-wise pending fee Excel with charts."""
    from datetime import date

    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    return run_tool(
        ex.export_batch_wise_pending_fee_excel,
        course_id=course_id,
        from_date=fd,
        to_date=td,
    )


@tool
def export_fee_defaulters_excel_tool(course_id: int = 0) -> str:
    """Export fee defaulter list to Excel with charts."""
    return run_tool(ex.export_fee_defaulters_excel, course_id=course_id)


@tool
def export_daily_collection_excel_tool(from_date: str = "", to_date: str = "") -> str:
    """Export daily fee collection to Excel with charts."""
    from datetime import date

    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    return run_tool(ex.export_daily_collection_excel, from_date=fd, to_date=td)


TOOLS = [
    export_pending_fee_students_excel_tool,
    export_course_wise_pending_fee_excel_tool,
    export_batch_wise_pending_fee_excel_tool,
    export_fee_defaulters_excel_tool,
    export_daily_collection_excel_tool,
]
