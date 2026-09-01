from __future__ import annotations

from app.auth.context import ChatContext
from app.db.connection import exec_sp_scalar
from app.utils.language import msg
from app.permissions.menu_urls import (
    MENU_ATTENDANCE,
    MENU_DASHBOARD,
    MENU_ENQUIRY_LIST,
    MENU_EXAM_RESULTS,
    MENU_FEE_COLLECTION,
    MENU_FEE_DASHBOARD,
    MENU_FEE_REPORTS,
    MENU_PENDING_FEE,
    MENU_STUDENT_LIST,
)


class PermissionDenied(Exception):
    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


def check_menu_permission(ctx: ChatContext, menu_url: str) -> bool:
    if ctx.is_super_admin or ctx.is_head_branch:
        return True
    # ERP CommonClass.CheckActionRights always passes brid "0" (not session branch).
    result = exec_sp_scalar(
        "Usp_ManageActionRights",
        ("0", str(ctx.user_id), menu_url, "0"),
    )
    try:
        return int(result or 0) == 1
    except (TypeError, ValueError):
        return False


def require_menu_permission(ctx: ChatContext, menu_url: str, label: str) -> None:
    if not check_menu_permission(ctx, menu_url):
        raise PermissionDenied(msg("permission_menu", label=label))


def can_view_students(ctx: ChatContext) -> bool:
    return ctx.is_super_admin or check_menu_permission(ctx, MENU_STUDENT_LIST)


def can_view_fee(ctx: ChatContext) -> bool:
    if ctx.is_super_admin or ctx.is_head_branch:
        return True
    if check_menu_permission(ctx, MENU_FEE_COLLECTION):
        return True
    if check_menu_permission(ctx, MENU_FEE_REPORTS):
        return True
    if check_menu_permission(ctx, MENU_FEE_DASHBOARD):
        return True
    if check_menu_permission(ctx, MENU_STUDENT_LIST):
        return True
    result = exec_sp_scalar(
        "USP_CheckFeeUserActionPermission",
        (ctx.user_id, "student-fee-collection", "view-summary", ctx.branch_id, ctx.org_id),
    )
    return bool(result)


def can_view_fee_reports(ctx: ChatContext) -> bool:
    if ctx.is_super_admin or ctx.is_head_branch:
        return True
    return check_menu_permission(ctx, MENU_FEE_REPORTS) or check_menu_permission(
        ctx, MENU_FEE_COLLECTION
    )


def require_fee_view(ctx: ChatContext) -> None:
    if not can_view_fee(ctx):
        raise PermissionDenied(msg("permission_fee"))


def require_fee_reports(ctx: ChatContext) -> None:
    if not can_view_fee_reports(ctx):
        raise PermissionDenied(msg("permission_fee_reports"))


def can_view_dashboard(ctx: ChatContext) -> bool:
    return ctx.is_super_admin or ctx.is_head_branch or check_menu_permission(ctx, MENU_DASHBOARD)


def can_view_attendance(ctx: ChatContext) -> bool:
    return ctx.is_super_admin or ctx.is_head_branch or check_menu_permission(ctx, MENU_ATTENDANCE)


def can_view_enquiry(ctx: ChatContext) -> bool:
    return ctx.is_super_admin or ctx.is_head_branch or check_menu_permission(ctx, MENU_ENQUIRY_LIST)


def can_view_exam(ctx: ChatContext) -> bool:
    return ctx.is_super_admin or ctx.is_head_branch or check_menu_permission(ctx, MENU_EXAM_RESULTS)
