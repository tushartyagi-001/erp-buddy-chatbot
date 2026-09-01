from __future__ import annotations

from app.auth.context import ChatContext
from app.db.connection import exec_sp
from app.permissions.checker import can_view_enquiry
from app.utils.language import msg


def _shape_enquiry(row: dict) -> dict:
    return {
        "enquiry_id": row.get("enquiryid"),
        "name": row.get("NAME") or row.get("Name"),
        "form_no": row.get("formno"),
        "enquiry_date": row.get("ENQUIRYDATE"),
        "followup_date": row.get("followupdate"),
        "status": row.get("statusname"),
        "course_interest": row.get("enqtype") or row.get("TargetExam"),
        "city": row.get("city"),
        "added_by": row.get("ADDEDBYNAME") or row.get("addedby"),
    }


def search_enquiries(ctx: ChatContext, term: str, limit: int = 10) -> dict:
    if not can_view_enquiry(ctx):
        return {
            "allowed": False,
            "message": msg("permission_enquiry"),
        }

    term = (term or "").strip()
    if len(term) < 2:
        return {
            "allowed": True,
            "total": 0,
            "enquiries": [],
            "needs_more_info": True,
            "hint": msg("search_min_chars"),
        }

    search_by = "Mobile" if term.isdigit() else "Name"
    mobile = term if search_by == "Mobile" else ""
    name = term if search_by == "Name" else ""

    rows = exec_sp(
        "usp_Datalist",
        (
            "",
            ctx.branch_id,
            ctx.fy_id,
            name,
            mobile,
            "",
            0,
            "",
            "",
            min(max(limit, 1), 15),
            1,
            ctx.user_id,
            "",
            "",
            term,
            search_by,
            "",
            ctx.user_id,
            "",
            0,
            0,
            0,
            0,
            "",
            ctx.branch_collection or str(ctx.branch_id),
            0,
            1 if ctx.is_head_branch else 0,
            "",
            None,
            0,
        ),
    )

    enquiries = [_shape_enquiry(r) for r in rows]
    return {
        "allowed": True,
        "total": len(enquiries),
        "enquiries": enquiries,
        "needs_selection": len(enquiries) > 1,
        "privacy_note": "Mobile aur email AI response me expose nahi hote.",
    }
