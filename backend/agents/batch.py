"""Mint several cards in one run.

The claims below are the narratives the partner organisations document as
circulating in Spanish-language channels. In production these arrive from the
gap detector -- from what people actually asked La Comadre and from what El
Boletin saw being pushed. This file is the seeded equivalent, so the deck can
be built before the ledger has traffic in it.

    python -m agents.batch              # mint everything not already minted
    python -m agents.batch --only 2 5
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.taller import mint, save
from config import BudgetExceeded
from render import load_deck

from agents.queue_claims import QUEUE



async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, help="1-based indices into the queue")
    ap.add_argument("--budget", type=float, default=0.35)
    ap.add_argument("--limit", type=int, default=0, help="stop after N new cards")
    args = ap.parse_args()

    items = QUEUE if not args.only else [QUEUE[i - 1] for i in args.only]
    target = len(QUEUE) + 12
    minted, skipped, failed = [], [], []
    spend = 0.0

    for key, claim in items:
        existing = {c.gap_id for c in load_deck() if c.gap_id}
        if key in existing:
            print(f"- {key}: already minted, skipping")
            skipped.append(key)
            continue
        print(f"\n=== {key}\n    {claim}")
        try:
            card = await mint(claim, gap_id=key, budget_usd=args.budget)
        except BudgetExceeded as exc:
            print(f"    BUDGET STOP: {exc}")
            failed.append((key, "budget"))
            continue
        except Exception as exc:
            print(f"    FAILED: {type(exc).__name__}: {exc}")
            failed.append((key, str(exc)[:80]))
            continue
        save(card)
        f = card.frame
        print(f"    -> {card.id} {card.name.es} [{card.category}] {card.status}")
        print(f"       frame={f.frame} lift={f.measured_lift} evidence={len(card.evidence)}")
        print(f"       {card.truth_headline.en}")
        minted.append(card)
        if args.limit and len(minted) >= args.limit:
            print(f"    reached --limit {args.limit}")
            break

    print(f"\nminted {len(minted)}, skipped {len(skipped)}, failed {len(failed)}")
    if failed:
        for k, why in failed:
            print(f"  ! {k}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
