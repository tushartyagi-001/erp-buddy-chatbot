from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.presentation.envelope import extract_formatted_from_messages
from app.routing.helpers import parse_tool_payload
from app.tools.registry import TOOL_BY_NAME


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content) if content else ""


def run_single_pass_agent(
    llm,
    tools: list,
    messages: list,
) -> dict[str, Any]:
    """One LLM call for tool selection, execute tools, return formatted output — no second LLM pass."""
    if not tools:
        return {
            "reply": "No tools available for this request.",
            "reply_type": "text",
            "options": None,
            "attachments": None,
            "_meta": {"route": "agent", "ai_used": True, "passes": 1},
        }

    llm_with_tools = llm.bind_tools(tools)
    ai_msg = llm_with_tools.invoke(messages)

    if not getattr(ai_msg, "tool_calls", None):
        return {
            "reply": _extract_text(getattr(ai_msg, "content", "")) or "How can I help you?",
            "reply_type": "text",
            "options": None,
            "attachments": None,
            "_meta": {"route": "agent", "ai_used": True, "passes": 1},
        }

    tool_messages: list[ToolMessage] = []
    combined: dict[str, Any] | None = None

    for call in ai_msg.tool_calls:
        tool_name = call.get("name")
        tool_args = call.get("args") or {}
        tool = TOOL_BY_NAME.get(tool_name)
        if not tool:
            continue
        raw = tool.invoke(tool_args)
        tool_messages.append(ToolMessage(content=raw, tool_call_id=call.get("id") or tool_name))
        parsed = parse_tool_payload(raw if isinstance(raw, str) else str(raw))
        if parsed:
            if combined is None:
                combined = parsed
            else:
                from app.routing.helpers import merge_responses

                combined = merge_responses(combined, parsed)

    if combined:
        combined["_meta"] = {
            "route": "agent",
            "ai_used": True,
            "passes": 1,
            "stop_after_tool": True,
        }
        return combined

    fallback = extract_formatted_from_messages(
        [ai_msg] + tool_messages  # type: ignore[arg-type]
    )
    if fallback:
        fallback["_meta"] = {"route": "agent", "ai_used": True, "passes": 1, "stop_after_tool": True}
        return fallback

    last_raw = tool_messages[-1].content if tool_messages else ""
    parsed = parse_tool_payload(str(last_raw))
    if parsed:
        parsed["_meta"] = {"route": "agent", "ai_used": True, "passes": 1, "stop_after_tool": True}
        return parsed

    return {
        "reply": _extract_text(getattr(ai_msg, "content", "")) or "Done.",
        "reply_type": "text",
        "options": None,
        "attachments": None,
        "_meta": {"route": "agent", "ai_used": True, "passes": 1},
    }
