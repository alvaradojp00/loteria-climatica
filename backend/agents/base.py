"""Shared agent construction, metering and the delegation envelope.

Every agent in every lane is built here, so the model, the budget guard, the
event stream and the audit trail are wired identically everywhere. Typed
outputs come from PydanticAI: each agent declares the shape it must return,
so a handoff that does not validate is an error rather than prose.
"""

from __future__ import annotations

import os
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import MODEL, async_client, prompt
from events import emit, record_usage
from pricing import Usage

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

T = TypeVar("T", bound=BaseModel)

_model: OpenAIResponsesModel | None = None


def model() -> OpenAIResponsesModel:
    """One model object shared by every agent -- one gateway, one place to swap."""
    global _model
    if _model is None:
        _model = OpenAIResponsesModel(MODEL, provider=OpenAIProvider(openai_client=async_client()))
    return _model


def build(
    name: str,
    output_type: type[T],
    prompt_name: str | None = None,
    instructions: str | None = None,
    tools: list | None = None,
    capabilities: list | None = None,
    retries: int = 2,
) -> Agent:
    """Create an agent whose instructions live in prompts/<name>.md."""
    text = instructions if instructions is not None else prompt(prompt_name or name)
    kwargs: dict[str, Any] = {}
    if capabilities:
        kwargs["capabilities"] = capabilities
    return Agent(
        model(),
        name=name,
        output_type=output_type,
        instructions=text,
        tools=tools or [],
        retries=retries,
        **kwargs,
    )


def _usage_of(result) -> Usage:
    """Translate PydanticAI's RunUsage into our measured Usage.

    `input_tokens` from the Responses API is inclusive of cache reads and
    writes, so we keep it whole and let pricing.py work out the remainder.
    """
    u = result.usage
    return Usage(
        model=MODEL,
        input_tokens=getattr(u, "input_tokens", 0) or 0,
        output_tokens=getattr(u, "output_tokens", 0) or 0,
        cached_tokens=getattr(u, "cache_read_tokens", 0) or 0,
        cache_write_tokens=getattr(u, "cache_write_tokens", 0) or 0,
        reasoning_tokens=getattr(u, "output_reasoning_tokens", 0) or 0,
    )


async def run(agent: Agent, task: str, *, label: str | None = None, **kwargs) -> Any:
    """Run one agent, emit its lifecycle, meter it, charge the budget.

    Raises BudgetExceeded through record_usage -- deliberately. A guardrail the
    agent cannot talk its way past.
    """
    name = label or agent.name or "agent"
    emit("agent_started", agent=name)
    try:
        result = await agent.run(task, **kwargs)
    except Exception as exc:
        emit("error", agent=name, error=f"{type(exc).__name__}: {exc}")
        raise
    record_usage(name, _usage_of(result))
    emit("agent_done", agent=name)
    return result.output
