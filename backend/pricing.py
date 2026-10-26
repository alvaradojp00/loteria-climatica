"""Token accounting.

Prices are the OpenAI Standard short-context rates used in Lecture 11,
USD per 1M tokens. `input_tokens` from the Responses API is inclusive of
cache reads and cache writes, so uncached input is the remainder.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PRICES: dict[str, dict[str, float]] = {
    # model          input  cached  cache_write  output
    "gpt-6-luna": {"input": 0.10, "cached": 0.01, "cache_write": 0.125, "output": 0.50},
    "gpt-6.1-sol": {"input": 2.00, "cached": 0.10, "cache_write": 2.50, "output": 10.00},
    "gpt-6-astra": {"input": 10.00, "cached": 1.00, "cache_write": 12.50, "output": 50.00},
}

PRICE_SOURCE = "https://openai.com/api/pricing/ (as presented in MGT 409 Lecture 11)"


@dataclass
class Usage:
    """A single model call's measured token usage. Never estimated."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0

    @classmethod
    def from_response(cls, model: str, usage) -> "Usage":
        """Read the real fields off a Responses API result."""
        if usage is None:
            return cls(model=model)
        ind = getattr(usage, "input_tokens_details", None)
        outd = getattr(usage, "output_tokens_details", None)
        get = lambda o, k: (getattr(o, k, 0) or 0) if o is not None else 0
        return cls(
            model=model,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cached_tokens=get(ind, "cached_tokens"),
            cache_write_tokens=get(ind, "cache_write_tokens"),
            reasoning_tokens=get(outd, "reasoning_tokens"),
        )

    @property
    def uncached_input(self) -> int:
        return max(0, self.input_tokens - self.cached_tokens - self.cache_write_tokens)

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            model=self.model if self.model == other.model else "mixed",
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )


def cost_usd(usage: Usage) -> float:
    p = PRICES.get(usage.model)
    if p is None:  # unknown model: do not guess a price
        return 0.0
    return (
        usage.uncached_input * p["input"]
        + usage.cached_tokens * p["cached"]
        + usage.cache_write_tokens * p["cache_write"]
        + usage.output_tokens * p["output"]
    ) / 1_000_000


def enrich_usage(usage: Usage) -> dict:
    d = {
        "model": usage.model,
        "input_tokens": usage.input_tokens,
        "uncached_input_tokens": usage.uncached_input,
        "cached_tokens": usage.cached_tokens,
        "cache_write_tokens": usage.cache_write_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
        "total_tokens": usage.input_tokens + usage.output_tokens,
    }
    d["cost_usd"] = round(cost_usd(usage), 8)
    return d


@dataclass
class Meter:
    """Per-agent spend, for the live meters and the tokenomics section."""

    per_agent: dict[str, Usage] = field(default_factory=dict)
    calls: int = 0

    def record(self, agent: str, usage: Usage) -> float:
        self.calls += 1
        prev = self.per_agent.get(agent)
        self.per_agent[agent] = prev + usage if prev else usage
        return cost_usd(usage)

    def total(self) -> Usage:
        out = Usage(model="mixed")
        for u in self.per_agent.values():
            out = out + u
        return out

    def report(self) -> dict:
        return {
            "calls": self.calls,
            "agents": {a: enrich_usage(u) for a, u in sorted(self.per_agent.items())},
            "total_usd": round(sum(cost_usd(u) for u in self.per_agent.values()), 8),
            "price_source": PRICE_SOURCE,
        }


def project_costs(cost_per_run: float, runs_per_user_month: int = 8) -> dict:
    """The scale table the report asks for."""
    per_user = cost_per_run * runs_per_user_month
    return {
        "cost_per_run": round(cost_per_run, 6),
        "runs_per_user_per_month": runs_per_user_month,
        "cost_per_user_per_month": round(per_user, 6),
        "cost_100_users_per_month": round(per_user * 100, 2),
        "cost_10000_users_per_month": round(per_user * 10_000, 2),
    }
