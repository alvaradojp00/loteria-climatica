"""Lane A -- La Comadre. One agent with tools. Deliberately not a mesh.

The job is a single role in a single context: answer a climate question,
grounded in the deck and the source library. A boss-and-specialists version
would add two model calls per turn and buy nothing, because there is no second
domain to consult. The report backs this with measured cost per conversation
rather than asserting it -- see experiments/chat_ab.py.

Every turn writes a row to the demand ledger. That ledger is what lets the deck
grow from what people actually ask.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field

import ledger
import tools
from agents.base import build, run
from config import BudgetTracker
from events import RunContext, emit, write_trail
from models import LedgerRow

MAX_STEPS = 6


class Reply(BaseModel):
    """What one turn of the conversation returns.

    `say_this` is the field that matters. An explanation the person cannot
    repeat is an explanation they will not use: the whole point is that they
    are about to talk to somebody they love about this.
    """

    text: str = Field(description="the answer, plain text, no markdown")
    say_this: str = Field(
        default="",
        description="one or two sentences they can say out loud to the person "
                    "who told them this, in their language, warm, no jargon",
    )
    one_move: str = Field(
        default="",
        description="one concrete thing to do this week, specific and small",
    )
    cards_cited: list[str] = Field(default_factory=list)
    tactic: str | None = None
    topic: str = Field(default="", description="two or three words naming the subject")
    answered: bool = Field(
        default=True,
        description="false when the deck and the library did not cover this",
    )


def _agent():
    return build(
        "comadre",
        Reply,
        tools=[tools.search_cards, tools.search_sources,
               tools.list_tactics, tools.get_resources],
    )


# Spanish/English detection good enough to pick a reply language; the agent
# confirms it from the text itself.
_ES = re.compile(r"[ñáéíóú¿¡]|\b(que|por|para|como|cuando|porque|esta|muy|pero|"
                 r"nada|dice|cierto|verdad|calor|luz|gente|carta)\b", re.I)


def detect_lang(text: str) -> str:
    return "es" if _ES.search(text) else "en"


async def ask(
    message: str,
    *,
    history: list[dict] | None = None,
    channel: str = "web",
    user_ref: str = "anon",
    queue: asyncio.Queue | None = None,
    budget_usd: float = 0.05,
) -> dict:
    """One turn. Channel-agnostic: web, whatsapp and paste all land here."""
    ctx = RunContext(lane="comadre", channel=channel, user_ref=user_ref, queue=queue)
    ctx.budget = BudgetTracker(run_limit_usd=budget_usd)
    ctx.lang = detect_lang(message)
    ctx.bind()

    tools.refresh()  # pick up any card El Taller minted since the last turn

    convo = ""
    for turn in (history or [])[-6:]:
        convo += f"{turn['role']}: {turn['content']}\n"
    # The model drifts into English because every instruction around it is in
    # English. Stating the detected language in the task itself is
    # deterministic, costs nothing, and holds.
    lang_name = "Spanish" if ctx.lang == "es" else "English"
    task = (
        (f"Conversation so far:\n{convo}\n\n" if convo else "")
        + f"They wrote in {lang_name}. Answer in {lang_name}: `text`, "
          f"`say_this` and `one_move` all in {lang_name}.\n\n"
        + f"They wrote:\n{message}"
    )

    reply: Reply = await run(_agent(), task, label="comadre")

    cost = ctx.meter.report()["total_usd"]
    ledger.write(LedgerRow(
        run_id=ctx.run_id,
        channel=channel,
        user_ref=user_ref,
        lang=ctx.lang,
        lane="comadre",
        user_text=message,
        topic=reply.topic,
        tactic=reply.tactic,
        matched_card=reply.cards_cited[0] if reply.cards_cited else None,
        answered=reply.answered and bool(reply.cards_cited),
        cost_usd=cost,
    ))
    emit("final", cards=reply.cards_cited, tactic=reply.tactic, cost_usd=cost)
    write_trail({"message": message, "topic": reply.topic})

    return {
        "text": reply.text,
        "say_this": reply.say_this,
        "one_move": reply.one_move,
        "cards": reply.cards_cited,
        "tactic": reply.tactic,
        "topic": reply.topic,
        "answered": reply.answered,
        "lang": ctx.lang,
        "usage": ctx.meter.report(),
    }


async def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("message", nargs="+")
    ap.add_argument("--user", default="cli")
    args = ap.parse_args()
    out = await ask(" ".join(args.message), user_ref=args.user, channel="cli")
    print(f"\n{out['text']}\n")
    print(f"  SAY THIS: {out['say_this']}")
    print(f"  ONE MOVE: {out['one_move']}")
    print(f"  cards={out['cards']} tactic={out['tactic']} topic={out['topic']!r} "
          f"answered={out['answered']} lang={out['lang']}")
    print(f"  cost=${out['usage']['total_usd']:.5f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_cli()))
