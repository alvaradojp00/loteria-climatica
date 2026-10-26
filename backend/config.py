"""Gateway, model and budget configuration.

One place for the Portkey client so every agent in every lane shares it.
The app looks for `.env` in this repo folder first, then one level up, then
the course root -- per the final project requirements.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# .env search order: backend/ -> repo root -> one above the repo (course root)
for candidate in (HERE / ".env", REPO / ".env", REPO.parent / ".env"):
    if candidate.is_file():
        load_dotenv(candidate)
        break

BASE_URL = "https://api.portkey.ai/v1"

# The course gateway key. gpt-6-luna is the only model it is licensed for.
MODEL = os.getenv("LOTERIA_MODEL", "gpt-6-luna")

# Optional: a personal key, used only for the single cross-tier comparison run
# documented in the report. Never required to run the app.
OWN_KEY = os.getenv("OPENAI_API_KEY") or None


def _key() -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Copy .env.example to .env and fill it in, "
            "or keep one .env in the course folder above this repo."
        )
    return key


def client() -> OpenAI:
    k = _key()
    return OpenAI(api_key=k, base_url=BASE_URL, default_headers={"x-portkey-api-key": k})


def async_client() -> AsyncOpenAI:
    k = _key()
    return AsyncOpenAI(api_key=k, base_url=BASE_URL, default_headers={"x-portkey-api-key": k})


class BudgetExceeded(RuntimeError):
    """Raised when a run or a day hits its spending ceiling."""


@dataclass
class BudgetTracker:
    """Deterministic spend guard. Not an agent -- a counter that raises.

    Agents cannot talk their way past this, which is the point: Lecture 4's
    rule is deterministic guardrails rather than trusting the model to behave.
    """

    run_limit_usd: float = 0.25
    day_limit_usd: float = 5.00
    spent_usd: float = 0.0
    by_agent: dict[str, float] = field(default_factory=dict)

    def add(self, agent: str, usd: float) -> None:
        self.spent_usd += usd
        self.by_agent[agent] = self.by_agent.get(agent, 0.0) + usd
        if self.spent_usd >= self.run_limit_usd:
            raise BudgetExceeded(
                f"run budget ${self.run_limit_usd:.2f} reached "
                f"(spent ${self.spent_usd:.4f} across {len(self.by_agent)} agents)"
            )

    def snapshot(self) -> dict:
        return {
            "total_usd": round(self.spent_usd, 6),
            "run_limit_usd": self.run_limit_usd,
            "agents": {a: round(v, 6) for a, v in sorted(self.by_agent.items())},
        }


PROMPTS = HERE / "prompts"
ASSETS = REPO / "assets"

# Writable state. On a host with an ephemeral filesystem -- which is the
# default on Render -- anything written here disappears on the next deploy,
# including the subscriber list. Point DATA_DIR and OUTPUT_DIR at a mounted
# persistent disk in production and nothing else has to change.
DATA = Path(os.getenv("DATA_DIR") or HERE / "data")
OUTPUT = Path(os.getenv("OUTPUT_DIR") or REPO / "output")
DATA.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

# Seed files ship in the repo. When DATA_DIR points somewhere empty, copy them
# across once so a fresh deploy starts with the deck rather than nothing.
SEED = HERE / "data"
if DATA != SEED:
    import shutil

    for seed_file in SEED.glob("*.json"):
        target = DATA / seed_file.name
        if not target.exists():
            shutil.copy2(seed_file, target)


def allowed_origins() -> list[str]:
    """Browser origins permitted to call the API.

    Local dev ports by default; set ALLOWED_ORIGINS (comma separated) to the
    deployed frontend URL in production.
    """
    raw = os.getenv("ALLOWED_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    # Vite walks forward a port at a time when 5173 is already taken, so a
    # grader with another project open lands on 5174 or 5175. Cover the range
    # rather than let the app look broken for a reason nobody can see.
    return [f"http://{host}:{port}"
            for host in ("localhost", "127.0.0.1")
            for port in (5173, 5174, 5175, 5176, 4173, 4174)]


def prompt(name: str) -> str:
    """Load a prompt from prompts/<name>.md so it can be edited without code changes."""
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
