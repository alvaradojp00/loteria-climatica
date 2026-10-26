"""El Taller de Cartas -- the card factory.

La Maestra takes a gap, delegates to the shared pool, and submits the result
to two independent gates. Either gate can send the card back. After two
rework passes the card stops as `needs_human` rather than shipping.

    python -m agents.taller --claim "Los paneles solares no sirven cuando hace frio"
    python -m agents.taller --from-gaps 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import pool
import archivista
from agents.gates import verify_content, visual_lint
from config import BudgetExceeded, BudgetTracker, DATA
from events import RunContext, emit, write_trail
from models import Bilingual, Card, Palette
from render import load_deck

MAX_REWORK = 2

# Category palettes, taken from the measured originals in style_profile.json.
# Colour is chosen by rule, never by the model -- which is a large part of why
# a generated card reads as a member of this deck.
CATEGORY_PALETTE: dict[str, Palette] = {
    "health":    Palette(sky="#FF5701", ground="#5FA52D", seam="#F2C230", motif=["#F6D64A", "#8A4A22", "#E8E2D2", "#7A5BA6"]),
    "energy":    Palette(sky="#1F78C0", ground="#60AB2D", seam="#2275B3", motif=["#F2A227", "#6F3214", "#F6D64A", "#E8E2D2"]),
    "community": Palette(sky="#FF7A07", ground="#945920", seam="#2487C1", motif=["#B8732C", "#E8E2D2", "#4F7F3F", "#F6D64A"]),
    "food":      Palette(sky="#E0452A", ground="#4F7F3F", seam="#F2C230", motif=["#F6D64A", "#B8732C", "#E8E2D2", "#7A5BA6"]),
    "waste":     Palette(sky="#2487C1", ground="#3F8E5A", seam="#9ED3E8", motif=["#E8E2D2", "#F2A227", "#7A5BA6", "#8A4A22"]),
    "justice":   Palette(sky="#F04E23", ground="#2E7D5B", seam="#F2C230", motif=["#F6D64A", "#E8E2D2", "#7A5BA6", "#B8732C"]),
    "land":      Palette(sky="#3B9A3B", ground="#8A5A2B", seam="#CFE06A", motif=["#4F7F3F", "#E8E2D2", "#F2A227", "#6F3214"]),
    "water":     Palette(sky="#1F78C0", ground="#2E7D5B", seam="#9ED3E8", motif=["#E8E2D2", "#F6D64A", "#8A4A22", "#4F7F3F"]),
    "general":   Palette(sky="#F04E23", ground="#5FA52D", seam="#F2C230", motif=["#F6D64A", "#E8E2D2", "#8A4A22", "#7A5BA6"]),
}


def slugify(name: str) -> str:
    s = name.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


async def mint(claim: str, *, gap_id: str | None = None,
               audience: str = "general mixed audience",
               budget_usd: float = 0.35,
               queue=None) -> Card:
    """Manufacture one card from one claim. The showcase pipeline.

    `queue` is the SSE event bus when a browser is watching; None when the
    scheduler runs it.
    """
    ctx = RunContext(lane="taller", channel="scheduler", queue=queue)
    ctx.budget = BudgetTracker(run_limit_usd=budget_usd)
    ctx.bind()
    emit("agent_started", agent="maestra")

    next_number = archivista.next_number()
    taken = ", ".join(sorted(c.name.es for c in archivista.deck()))

    # 1. Evidence. No evidence, no card -- the Maestra stops rather than invent.
    report = await pool.researcher(claim)
    if report.status == "empty" or not report.citations:
        emit("final", status="abandoned", reason="no evidence found")
        write_trail({"claim": claim, "outcome": "abandoned_no_evidence"})
        raise RuntimeError("no evidence found for this claim; card abandoned")

    # 2. Frame, from the measured study.
    frame = await pool.framer(claim, report.findings, audience)

    # 3-7. Draft, transcreate, draw, and submit to both gates.
    feedback_text = ""
    feedback_art = ""
    draft = None
    spanish = None
    art = None
    palette = CATEGORY_PALETTE["general"]
    content_ok = False
    art_ok = False
    verdict = None

    name_feedback = f"Card names already in this deck, which yours must differ from: {taken}"
    for attempt in range(MAX_REWORK + 1):
        if not content_ok:
            draft = await pool.writer(
                claim, report, frame,
                (feedback_text + "\n" + name_feedback).strip(),
            )
            # La Archivista owns the deck: a colliding name is rejected by
            # arithmetic before either gate gets a say.
            clash = archivista.name_collision(draft.name_es)
            if clash:
                emit("qa_rejected", gate="archivista",
                     problems=[f"card name {draft.name_es!r} already used by card {clash}"])
                feedback_text = (f"The name {draft.name_es!r} is already card {clash}. "
                                 f"Choose a different concrete object. {name_feedback}")
                content_ok = False
                continue
            palette = CATEGORY_PALETTE.get(draft.category, CATEGORY_PALETTE["general"])

        if not art_ok:
            art = await pool.artist(draft.motif_brief, palette, feedback_art)

        # the two gates are independent; run them together
        verdict, art_problems = await asyncio.gather(
            verify_content(draft, report.citations, frame)
            if not content_ok else _already_passed(),
            _lint(art.svg, palette) if not art_ok else _no_problems(),
        )

        content_ok = content_ok or verdict.passed
        art_ok = art_ok or not art_problems

        if content_ok and art_ok:
            break
        if attempt < MAX_REWORK:
            emit("rework", attempt=attempt + 1,
                 content_ok=content_ok, art_ok=art_ok)
            feedback_text = "\n".join(f"- {p}" for p in verdict.problems)
            feedback_art = "\n".join(f"- {p}" for p in art_problems)

    # 8. Spanish face, once the English has settled.
    spanish = await pool.transcreator(draft)

    status = "draft" if (content_ok and art_ok) else "needs_human"
    notes = "" if status == "draft" else (
        "Stopped for human review after "
        f"{MAX_REWORK} rework passes. "
        + ("content: " + "; ".join(verdict.problems) if verdict and not content_ok else "")
    )

    card = Card(
        id=f"{next_number:02d}",
        number=next_number,
        slug=slugify(draft.name_es),
        name=Bilingual(en=draft.name_en, es=draft.name_es),
        category=draft.category,
        motif=draft.motif_brief,
        motif_svg=art.svg,
        palette=palette,
        myth=Bilingual(en=draft.myth, es=spanish.myth),
        truth_headline=Bilingual(en=draft.truth_headline, es=spanish.truth_headline),
        body=Bilingual(en=draft.body, es=spanish.body),
        action=Bilingual(en=draft.action, es=spanish.action),
        provenance="generated",
        status=status,
        frame=frame,
        evidence=report.citations,
        created_by="taller: researcher->framer->writer->transcreator->artist "
                   "+ verifier & visual_qa",
        gap_id=gap_id,
        notes=notes,
    )
    emit("final", card=card.id, name=card.name.es, status=status,
         spend=ctx.meter.report()["total_usd"])
    write_trail({"claim": claim, "card": card.id, "status": status,
                 "frame": frame.frame, "rejections": [
                     e for e in ctx.trail if e["type"] == "qa_rejected"]})
    return card


async def _lint(svg, palette):
    return visual_lint(svg, palette)


async def _no_problems():
    return []


class _Passed:
    passed = True
    problems: list[str] = []
    severity = "none"
    notes = ""


async def _already_passed():
    return _Passed()


def save(card: Card) -> Path:
    path = DATA / "cards.json"
    deck = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    deck = [c for c in deck if c["id"] != card.id]
    deck.append(card.model_dump())
    deck.sort(key=lambda c: c["number"])
    path.write_text(json.dumps(deck, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", required=True)
    ap.add_argument("--audience", default="general mixed audience")
    ap.add_argument("--budget", type=float, default=0.35)
    args = ap.parse_args()

    print(f"El Taller: minting a card for\n  {args.claim!r}\n")
    try:
        card = await mint(args.claim, audience=args.audience, budget_usd=args.budget)
    except BudgetExceeded as exc:
        print(f"BUDGET STOP: {exc}")
        return 2
    save(card)
    f = card.frame
    print(f"  card {card.id}  {card.name.es}  [{card.category}]  status={card.status}")
    print(f"  frame: {f.frame} (measured lift {f.measured_lift})")
    print(f"  rejected: {', '.join(f.rejected) or '-'}")
    print(f"  myth : {card.myth.en}")
    print(f"  truth: {card.truth_headline.en}")
    print(f"  es   : {card.truth_headline.es}")
    print(f"  evidence: {len(card.evidence)} citations")
    if card.notes:
        print(f"  notes: {card.notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
