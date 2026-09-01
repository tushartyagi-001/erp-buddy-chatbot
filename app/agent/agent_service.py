from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tool_executor import run_single_pass_agent
from app.auth.context import ChatContext, set_chat_context
from app.config import settings
from app.routing.intent_router import match_intent, try_direct_route
from app.routing.helpers import try_student_selection
from app.routing.tool_groups import select_tool_names
from app.services.response_cache import get_cached, make_cache_key, set_cached
from app.tools.registry import TOOLS, get_tools_by_names
from app.tools.student.tools import set_selected_student
from app.utils.language import detect_language, language_instruction, set_reply_language


def _trim_history(history: list[dict] | None) -> list[dict]:
    if not history:
        return []
    limit = max(settings.CHAT_HISTORY_LIMIT, 0)
    if limit <= 0:
        return []
    return history[-limit:]


def _build_messages(
    message: str,
    history: list[dict],
    lang: str,
    selected_student_reg_no: int | None,
) -> list:
    messages: list = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.append(SystemMessage(content=language_instruction(lang)))
    if selected_student_reg_no:
        messages.append(
            SystemMessage(content=f"Currently selected student_reg_no: {selected_student_reg_no}")
        )
    for item in history:
        if item.get("role") == "user":
            messages.append(HumanMessage(content=item["content"]))
        elif item.get("role") == "assistant":
            messages.append(AIMessage(content=item["content"]))
    messages.append(HumanMessage(content=message))
    return messages


def _get_llm():
    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )


def _public_response(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "reply": result.get("reply") or "",
        "reply_type": result.get("reply_type") or "text",
        "options": result.get("options"),
        "attachments": result.get("attachments"),
    }


def run_chat(
    ctx: ChatContext,
    message: str,
    history: list[dict] | None = None,
    selected_student_reg_no: int | None = None,
) -> dict[str, Any]:
    set_chat_context(ctx)
    set_selected_student(selected_student_reg_no)

    lang = detect_language(message)
    set_reply_language(lang)
    trimmed_history = _trim_history(history)

    selected = try_student_selection(message, selected_student_reg_no)
    if selected:
        return _public_response(selected)

    route_name = "agent"
    if settings.INTENT_ROUTER_ENABLED:
        matched = match_intent(message)
        if matched:
            route_name = f"direct:{matched}"
            cache_key = make_cache_key(
                branch_id=ctx.branch_id,
                user_id=ctx.user_id,
                route=route_name,
                message=message,
                selected_student_reg_no=selected_student_reg_no,
            )
            cached = get_cached(cache_key)
            if cached:
                return cached

            direct = try_direct_route(ctx, message, selected_student_reg_no)
            if direct:
                response = _public_response(direct)
                set_cached(cache_key, response)
                return response

    if settings.TOOL_GROUPING_ENABLED:
        tool_names = select_tool_names(message)
        tools = get_tools_by_names(tool_names)
    else:
        tools = list(TOOLS)

    cache_key = make_cache_key(
        branch_id=ctx.branch_id,
        user_id=ctx.user_id,
        route=f"agent:{','.join(sorted(t.name for t in tools))}",
        message=message,
        selected_student_reg_no=selected_student_reg_no,
    )
    cached = get_cached(cache_key)
    if cached:
        return cached

    messages = _build_messages(message, trimmed_history, lang, selected_student_reg_no)
    result = run_single_pass_agent(_get_llm(), tools, messages)
    response = _public_response(result)
    set_cached(cache_key, response)
    return response
