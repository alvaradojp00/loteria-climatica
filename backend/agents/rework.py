"""Re-run part of a card that was held, keeping everything that passed.

A held card has already paid for its research and its framing. Reworking it
should not pay again: this re-runs only the stage that failed.

    python -m agents.rework --copy 19 36 37 52 54      # writer + transcreator
    python -m agents.rework --art 27 --brief "a spiral storm seen from above"
    python -m agents.rework --truth 44 --truth-text "..."
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import archivista
from agents import pool
from agents.gates import verify_content, visual_lint
from config import BudgetTracker
from events import RunContext, write_trail
from models import Bilingual, Card, Evidence, SpecialistReport


def _report(card: Card) -> SpecialistReport:
    return SpecialistReport(
        role="researcher", status="ok",
        findings=f"Evidence already gathered for card {card.id}.",
        citations=[Evidence.model_validate(e) if isinstance(e, dict) else e
                   for e in card.evidence],
        confidence=0.8,
    )


async def rework_copy(card: Card, reframe: bool = False) -> Card:
    """Re-write the English and Spanish faces with the frame enforced.

    `reframe` re-runs the Framer first. Needed when the original frame was
    chosen on measured lift alone and the evidence cannot carry it -- enforcing
    such a frame just produces claims the Verifier then rejects.
    """
    ctx = RunContext(lane="taller", channel="rework")
    ctx.budget = BudgetTracker(run_limit_usd=0.25)
    ctx.bind()

    report = _report(card)
    if reframe:
        findings = " ".join(c.claim for c in report.citations)[:1200]
        card.frame = await pool.framer(card.myth.en or card.myth.es, findings)
    frame = card.frame
    feedback = (
        f"The previous draft was rejected for frame drift. The frame is "
        f"{frame.frame.upper()}. Make that frame unmistakable in the body: a "
        f"reader should be able to name it from the copy alone. "
        f"Previous reviewer note: {card.notes[:300]}"
    )
    draft = await pool.writer(card.myth.en or card.myth.es, report, frame, feedback)
    spanish = await pool.transcreator(draft)
    verdict = await verify_content(draft, report.citations, frame)

    card.myth = Bilingual(en=draft.myth, es=spanish.myth)
    card.truth_headline = Bilingual(en=draft.truth_headline, es=spanish.truth_headline)
    card.body = Bilingual(en=draft.body, es=spanish.body)
    card.action = Bilingual(en=draft.action, es=spanish.action)
    card.status = "draft" if verdict.passed else "needs_human"
    card.notes = (f"Reworked for frame fit 2026-10-26. "
                  + ("" if verdict.passed else
                     "Still held: " + "; ".join(verdict.problems)[:300]))
    write_trail({"rework": card.id, "stage": "copy", "passed": verdict.passed})
    print(f"  {card.id} {card.name.es:<22} frame={frame.frame:<8} -> {card.status}"
          + ("" if verdict.passed else f"  ({verdict.problems[0][:90]})"))
    return card


async def rework_art(card: Card, brief: str) -> Card:
    """Re-draw the motif from a sharper brief."""
    ctx = RunContext(lane="taller", channel="rework")
    ctx.budget = BudgetTracker(run_limit_usd=0.10)
    ctx.bind()

    feedback = ""
    for attempt in range(3):
        art = await pool.artist(brief, card.palette, feedback)
        problems = visual_lint(art.svg, card.palette)
        if not problems:
            card.motif_svg = art.svg
            card.motif = brief
            print(f"  {card.id} {card.name.es:<22} -> redrawn ({art.svg.count('<')} shapes)")
            write_trail({"rework": card.id, "stage": "art", "passed": True})
            return card
        feedback = "\n".join(f"- {p}" for p in problems)
        print(f"  {card.id} attempt {attempt + 1} rejected: {problems[0][:90]}")
    print(f"  {card.id} art still failing; left unchanged")
    return card


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy", nargs="*", default=[])
    ap.add_argument("--reframe", action="store_true",
                    help="re-run the Framer before rewriting")
    ap.add_argument("--art", nargs="*", default=[])
    ap.add_argument("--verify", nargs="*", default=[],
                    help="re-run the Verifier only, keeping the copy")
    ap.add_argument("--brief", default="")
    args = ap.parse_args()

    deck = {c.id: c for c in archivista.deck()}

    if args.copy:
        print(f"reworking copy for {len(args.copy)} card(s) with the frame enforced\n")
        for cid in args.copy:
            card = deck.get(cid)
            if not card or not card.frame:
                print(f"  {cid}: not found or has no frame")
                continue
            archivista.save(await rework_copy(card, reframe=args.reframe))

    for cid in args.verify:
        card = deck.get(cid)
        if not card:
            print(f"  {cid}: not found")
            continue
        ctx = RunContext(lane="taller", channel="reverify")
        ctx.budget = BudgetTracker(run_limit_usd=0.08)
        ctx.bind()
        report = _report(card)

        class _D:
            name_es = card.name.es
            myth = card.myth.en
            truth_headline = card.truth_headline.en
            body = card.body.en
            action = card.action.en

        verdict = await verify_content(_D(), report.citations, card.frame)
        card.status = "draft" if verdict.passed else "needs_human"
        card.notes = ("Re-verified 2026-10-26." if verdict.passed
                      else "Still held: " + "; ".join(verdict.problems)[:300])
        archivista.save(card)
        print(f"  {card.id} {card.name.es:<22} -> {card.status}"
              + ("" if verdict.passed else f"  ({verdict.problems[0][:90]})"))

    for cid in args.art:
        card = deck.get(cid)
        if not card:
            print(f"  {cid}: not found")
            continue
        archivista.save(await rework_art(card, args.brief or card.motif))

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
