"""La Bibliotecaria — keeps the resources page current.

Runs weekly. Sweeps the CAAD coalition members and the wider web for work
published since the last run, and proposes additions to the library.

Two rules make this safe to run unattended:

  * It never deletes. Existing entries are left alone; it only appends.
  * It never publishes. Everything it finds lands with `pending: true`, and
    the resources page shows pending items only to an operator. A library is
    a claim about what is worth reading, and that claim stays human.

    python -m agents.librarian              # propose
    python -m agents.librarian --approve all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field
from pydantic_ai.capabilities import WebSearch

from agents.base import build, run
from config import BudgetTracker, DATA
from events import RunContext, emit, write_trail

LIBRARY = DATA / "resources.json"

# The coalition, from caad.info/about. These are the organisations whose new
# work is most likely to belong in a library aimed at Latine families.
COALITION = [
    "Climate Action Against Disinformation", "Center for Countering Digital Hate",
    "Institute for Strategic Dialogue", "InfluenceMap", "Science Feedback",
    "Union of Concerned Scientists", "Friends of the Earth", "350.org",
    "Check My Ads", "Global Center for Climate Justice", "Reality Team",
    "Climate Social Science Network", "Conscious Advertising Network",
    "Global Action Plan", "QuotaClimat", "Amnesty International",
]

# Outside the coalition, but where the Spanish-language work actually lives.
ALSO_WATCH = [
    "GreenLatinos", "Climate Power En Accion", "Factchequeado",
    "Maldita.es", "Chequeado", "Climate Defenders Action",
]


class Found(BaseModel):
    title_en: str
    title_es: str
    org: str
    url: str
    type: str = Field(description="report | polling | tool | coalition | fact-check | action")
    topics: list[str] = Field(default_factory=list)
    why_en: str = Field(description="one sentence on why this is worth a click")
    why_es: str
    published: str = Field(default="", description="YYYY-MM or YYYY-MM-DD if known")


class Sweep(BaseModel):
    items: list[Found] = Field(default_factory=list)
    notes: str = ""


PROMPT = """You keep the reading library for Lotería Climática, a climate
disinformation project aimed at Latine families in the United States.

Find work published recently that belongs in that library. Search the web.

## What belongs

- Research, reporting or tools on climate disinformation, especially in
  Spanish or aimed at Latino audiences.
- Polling on how Latino communities see climate, energy and costs.
- Fact-checks of narratives that travel through WhatsApp and Facebook.
- Practical tools a person could use: how to report a post, how to check an
  installer, how to find a local hearing.

## What does not

- An organisation's front page. Every URL must be a specific page: a report, a
  dataset, an article, a tool.
- Anything already in the library you are shown.
- Opinion columns, press releases announcing other press releases, and
  anything behind a paywall.
- Work you cannot confirm exists. A plausible-looking URL you did not actually
  find in a search result is worse than returning nothing.

## How to judge

Prefer specific over general, Spanish-language over English where quality is
equal, and recent over canonical — the canonical work is already in the
library. Six good items beat twenty thin ones. Returning an empty list is a
legitimate week.

`why_en` and `why_es` are the lines a reader sees. Say what the thing lets them
do or understand, in a sentence, in plain words.
"""


async def sweep(since_days: int = 7, budget_usd: float = 0.30) -> list[Found]:
    ctx = RunContext(lane="librarian", channel="scheduler")
    ctx.budget = BudgetTracker(run_limit_usd=budget_usd)
    ctx.bind()

    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    have_urls = {i["url"] for i in library["items"]}
    have_titles = {i["title"]["en"].lower() for i in library["items"]}

    agent = build("librarian", Sweep, instructions=PROMPT, capabilities=[WebSearch()])
    out: Sweep = await run(
        agent,
        f"Today is {date.today().isoformat()}. Look for work published in roughly "
        f"the last {since_days} days.\n\n"
        f"Coalition members to sweep:\n- " + "\n- ".join(COALITION) + "\n\n"
        f"Also watch:\n- " + "\n- ".join(ALSO_WATCH) + "\n\n"
        f"Already in the library, do not repeat:\n- "
        + "\n- ".join(sorted(have_titles)) + "\n",
        label="librarian",
    )

    fresh = [f for f in out.items
             if f.url not in have_urls and f.title_en.lower() not in have_titles]
    emit("evidence_found", proposed=len(out.items), new=len(fresh))
    write_trail({"sweep": date.today().isoformat(), "new": len(fresh)})
    return fresh


def stage(found: list[Found]) -> int:
    """Append as pending. Nothing becomes visible to the public until approved."""
    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).date().isoformat()
    for f in found:
        library["items"].append({
            "id": f"auto-{abs(hash(f.url)) % 10**8}",
            "title": {"en": f.title_en, "es": f.title_es},
            "org": f.org,
            "url": f.url,
            "type": f.type if f.type in library["types"] else "report",
            "topics": [t for t in f.topics if t in library["topics"]],
            "why": {"en": f.why_en, "es": f.why_es},
            "pending": True,
            "found_on": stamp,
            "published": f.published,
        })
    library["last_sweep"] = stamp
    LIBRARY.write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(found)


def approve(ids: list[str]) -> int:
    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    n = 0
    for item in library["items"]:
        if item.get("pending") and (ids == ["all"] or item["id"] in ids):
            item.pop("pending", None)
            n += 1
    LIBRARY.write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8")
    return n


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--approve", nargs="*", help="ids, or 'all'")
    args = ap.parse_args()

    if args.approve:
        print(f"approved {approve(args.approve)} item(s)")
        return 0

    print(f"sweeping {len(COALITION)} coalition members + {len(ALSO_WATCH)} others…\n")
    found = await sweep(args.days)
    if not found:
        print("nothing new worth adding this week.")
        return 0
    for f in found:
        print(f"  [{f.type}] {f.title_en[:70]}")
        print(f"      {f.org} · {f.url}")
    stage(found)
    print(f"\nstaged {len(found)} item(s) as pending.")
    print("review them, then: python -m agents.librarian --approve all")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
