"""The event bus: agent actions -> async queue -> SSE -> live dashboard.

Lecture 10's pattern. The UI knows a fixed set of event types; anything else
is logged but not rendered.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import OUTPUT
from pricing import Meter, Usage, enrich_usage

EVENT_TYPES = {
    "routed",
    "agent_started",
    "agent_done",
    "tool_called",
    "evidence_found",
    "frame_selected",
    "qa_rejected",
    "rework",
    "spend",
    "final",
    "error",
}

_run: ContextVar["RunContext | None"] = ContextVar("_run", default=None)


@dataclass
class RunContext:
    """Per-run state shared by every agent in the run."""

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    lane: str = ""
    channel: str = "web"
    user_ref: str = "anon"
    lang: str | None = None
    queue: asyncio.Queue | None = None
    meter: Meter = field(default_factory=Meter)
    budget: Any = None
    trail: list[dict] = field(default_factory=list)

    def bind(self) -> None:
        _run.set(self)


def current() -> RunContext | None:
    return _run.get()


def emit(event_type: str, **data: Any) -> None:
    """Put an event on the queue and append it to the audit trail."""
    ctx = current()
    if ctx is None:
        return
    payload = {"type": event_type, "data": data}
    ctx.trail.append(payload)
    if ctx.queue is not None:
        try:
            ctx.queue.put_nowait(payload)
        except asyncio.QueueFull:  # never let telemetry block real work
            pass


def record_usage(agent: str, usage: Usage) -> float:
    """Meter a call, charge the budget, and push a spend event."""
    ctx = current()
    if ctx is None:
        return 0.0
    cost = ctx.meter.record(agent, usage)
    if ctx.budget is not None:
        ctx.budget.add(agent, cost)  # may raise BudgetExceeded -- deliberately
    emit(
        "spend",
        agent=agent,
        call=enrich_usage(usage),
        total_usd=round(sum(c for c in _agent_costs(ctx).values()), 8),
        agents=_agent_costs(ctx),
    )
    return cost


def _agent_costs(ctx: RunContext) -> dict[str, float]:
    from pricing import cost_usd

    return {a: round(cost_usd(u), 8) for a, u in ctx.meter.per_agent.items()}


def sse(payload: dict) -> str:
    """Format one event for an SSE stream."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def write_trail(extra: dict | None = None) -> Path:
    """Append this run to output/audit_trail.json. Never overwrites."""
    ctx = current()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "audit_trail.json"
    entries = []
    if path.is_file():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []
    entry = {
        "run_id": ctx.run_id if ctx else "unknown",
        "lane": ctx.lane if ctx else "",
        "channel": ctx.channel if ctx else "",
        "events": ctx.trail if ctx else [],
        "usage": ctx.meter.report() if ctx else {},
    }
    if extra:
        entry.update(extra)
    entries.append(entry)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
