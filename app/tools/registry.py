from app.tools.attendance.tools import TOOLS as ATTENDANCE_TOOLS
from app.tools.dashboard.tools import TOOLS as DASHBOARD_TOOLS
from app.tools.enquiry.tools import TOOLS as ENQUIRY_TOOLS
from app.tools.exam.tools import TOOLS as EXAM_TOOLS
from app.tools.export.tools import TOOLS as EXPORT_TOOLS
from app.tools.fee.tools import TOOLS as FEE_TOOLS
from app.tools.student.tools import TOOLS as STUDENT_TOOLS

TOOLS = (
    STUDENT_TOOLS
    + FEE_TOOLS
    + EXPORT_TOOLS
    + DASHBOARD_TOOLS
    + ATTENDANCE_TOOLS
    + EXAM_TOOLS
    + ENQUIRY_TOOLS
)

TOOL_BY_NAME = {tool.name: tool for tool in TOOLS}


def get_tools_by_names(names: set[str]) -> list:
    selected = [TOOL_BY_NAME[name] for name in names if name in TOOL_BY_NAME]
    return selected or list(TOOLS)


__all__ = ["TOOLS", "TOOL_BY_NAME", "get_tools_by_names"]
