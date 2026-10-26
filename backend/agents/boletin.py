"""Lane D -- El Boletin, the fortnightly brief.

Ingest and clustering are plain code; only the Editor is an agent, and the
Verifier it hands off to is the same one El Taller uses. Gaps found here join
the same queue as gaps from the chat ledger: two demand signals, one factory.

    python -m agents.boletin --adapter fixture
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field

import adapters.base as adapters
import ledger
import tools
from agents import pool
from agents.base import build, run
from config import BudgetTracker, DATA, OUTPUT
from events import RunContext, emit, write_trail
from gaps import harm_weight, normalise
import re

from models import Brief, GapRecord, SignalRecord, Topline

TOPLINE_COUNT = 3


class BriefOut(BaseModel):
    toplines: list[Topline] = Field(default_factory=list)
    period_note: str = ""


def cluster_signals(rows: list[SignalRecord]) -> list[tuple[str, list[SignalRecord]]]:
    """Group monitored items by shared keyword. Deterministic and inspectable."""
    by_word: dict[str, list[SignalRecord]] = defaultdict(list)
    for row in rows:
        for word in set(normalise(row.claim_text)):
            by_word[word].append(row)

    clusters: list[tuple[str, list[SignalRecord]]] = []
    claimed: set[int] = set()
    for word, group in sorted(by_word.items(), key=lambda kv: -len(kv[1])):
        fresh = [r for r in group if id(r) not in claimed]
        if len(fresh) < 2:
            continue
        clusters.append((word, fresh))
        claimed.update(id(r) for r in fresh)
    return clusters


def _score(topic: str, group: list[SignalRecord]) -> float:
    reach = sum(r.reach_estimate or 0 for r in group)
    harm = max(harm_weight(r.claim_text) for r in group)
    return len(group) * harm * (1 + reach / 20000)


async def build_brief(adapter: str | None = None, days: int = 14,
                      budget_usd: float = 0.20) -> Brief:
    ctx = RunContext(lane="boletin", channel="scheduler")
    ctx.budget = BudgetTracker(run_limit_usd=budget_usd)
    ctx.bind()
    emit("agent_started", agent="editor")
    tools.refresh()

    chosen = adapter or adapters.best()
    rows = adapters.collect(chosen, days=days)
    if not rows:
        emit("error", stage="ingest", adapter=chosen, note="empty, falling back to fixture")
        chosen, rows = "fixture", adapters.collect("fixture", days=days)
    emit("evidence_found", adapter=chosen, signals=len(rows))

    clusters = cluster_signals(rows)
    clusters.sort(key=lambda kv: -_score(*kv))
    top = clusters[:TOPLINE_COUNT]

    # one frame decision for the brief as a whole, from the measured study
    lead = " ".join(r.claim_text for r in top[0][1][:3]) if top else ""
    frame = await pool.framer(lead, "monitoring summary, no research pass", "general mixed audience")

    digest = []
    for topic, group in top:
        digest.append({
            "topic": topic,
            "count": len(group),
            "platforms": sorted({r.platform for r in group if r.platform}),
            "reach": sum(r.reach_estimate or 0 for r in group),
            "examples": [r.claim_text[:220] for r in group[:4]],
            "cards": json.loads(tools.search_cards(" ".join(
                r.claim_text for r in group[:3]), "es")).get("matches", [])[:2],
        })

    editor = build("editor", BriefOut, tools=[tools.list_tactics, tools.search_sources])
    out: BriefOut = await run(
        editor,
        f"Monitoring window: last {days} days. Source: {chosen}.\n"
        f"Value frame for this brief: {frame.frame} "
        f"(measured lift {frame.measured_lift}; {frame.audience_note})\n\n"
        f"CLUSTERS:\n{json.dumps(digest, ensure_ascii=False, indent=2)}\n",
        label="editor",
    )

    # The Editor sometimes narrates instead of returning an id. La Archivista
    # owns the deck, so resolve the reference here rather than trusting prose:
    # keep the first id that is a real card, drop anything else.
    known = {c.id for c in tools.deck()}
    for t, entry in zip(out.toplines, digest):
        found = [m for m in re.findall(r"\d{2}", t.covering_card or "") if m in known]
        if found:
            t.covering_card = found[0]
            continue
        # fall back to the deterministic card search already run for this
        # cluster, so a card the deck genuinely has is not lost to prose
        best = entry["cards"][0] if entry["cards"] else None
        t.covering_card = best["card"] if best and best.get("match", 0) >= 0.3 else None

    now = datetime.now(timezone.utc)
    brief = Brief(
        brief_id=now.strftime("%Y-%m-%d"),
        period_start=(now - timedelta(days=days)).date().isoformat(),
        period_end=now.date().isoformat(),
        adapter_used=chosen,
        toplines=out.toplines[:TOPLINE_COUNT],
    )

    # topics with no covering card become gaps, alongside the chat ledger's
    new_gaps = []
    for t, (topic, group) in zip(brief.toplines, top):
        if t.covering_card:
            continue
        gap = GapRecord(
            gap_id=f"gap_boletin_{topic}",
            topic=topic,
            sample_questions=[r.claim_text[:200] for r in group[:3]],
            distinct_conversations=len(group),
            unanswered_rate=1.0,
            harm_weight=max(harm_weight(r.claim_text) for r in group),
            recency=1.0,
            score=round(_score(topic, group), 3),
            origin="boletin",
        )
        t.gap_id = gap.gap_id
        new_gaps.append(gap)
    if new_gaps:
        ledger.save_gaps(new_gaps)
        emit("final", gaps_opened=[g.gap_id for g in new_gaps])

    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"boletin-{brief.brief_id}.json"
    path.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    latest = DATA / "boletin_latest.json"
    latest.write_text(brief.model_dump_json(indent=2), encoding="utf-8")

    emit("final", brief=brief.brief_id, toplines=len(brief.toplines),
         adapter=chosen, spend=ctx.meter.report()["total_usd"])
    write_trail({"brief": brief.brief_id, "adapter": chosen,
                 "signals": len(rows), "gaps": [g.gap_id for g in new_gaps]})
    return brief


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", choices=["fixture", "open", "junkipedia"], default=None)
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    from adapters import junkipedia

    print(f"adapters available: {', '.join(adapters.available())}")
    print(junkipedia.status_note())
    brief = await build_brief(args.adapter, args.days)
    print(f"\nEl Boletin {brief.brief_id}  "
          f"({brief.period_start} to {brief.period_end})  source={brief.adapter_used}\n")
    for i, t in enumerate(brief.toplines, 1):
        print(f"{i}. {t.headline.en}")
        print(f"   {t.headline.es}")
        print(f"   tactic : {t.tactic}")
        print(f"   prebunk: {t.prebunk.es}")
        print(f"   card   : {t.covering_card or 'NONE -> gap ' + (t.gap_id or '')}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
