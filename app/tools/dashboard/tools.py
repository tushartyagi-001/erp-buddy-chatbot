from __future__ import annotations

import json

from langchain_core.tools import tool

from app.services.dashboard_service import get_dashboard_summary
from app.tools.common import run_tool


@tool
def get_dashboard_summary_tool() -> str:
    """Branch dashboard KPI summary."""
    return run_tool(get_dashboard_summary)


TOOLS = [get_dashboard_summary_tool]
