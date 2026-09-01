from __future__ import annotations

from langchain_core.tools import tool

from app.services.enquiry_service import search_enquiries
from app.tools.common import run_tool


@tool
def search_enquiries_tool(name_or_mobile: str) -> str:
    """Search enquiries by name or mobile."""
    return run_tool(search_enquiries, term=name_or_mobile, limit=10)


TOOLS = [search_enquiries_tool]
