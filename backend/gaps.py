"""The gap detector and the cadence gate. Deterministic -- not agents.

    gap_score = frequency x unanswered_rate x harm_weight x recency

An agent here would be slower, costlier and non-reproducible, and this is
arithmetic. Keeping it out of the model layer is also what makes it safe:
the rule that stops someone from spamming a claim into the deck has to be a
rule, not a judgement call.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime, timezone

import ledger
from models import GapRecord

# A card is only minted from demand that several different people expressed.
# One person asking something strange is not demand -- it is also the obvious
# attack, so this threshold is a guardrail as much as a quality bar.
MIN_DISTINCT_CONVERSATIONS = 3

# Trailing-7-day conversation count at which the factory moves from monthly to
# weekly. Set from the pilot week; see the report.
WEEKLY_THRESHOLD = 25

HALF_LIFE_DAYS = 10.0

# Claims that can get somebody hurt outrank claims that are merely wrong.
HARM_TERMS = {
    2.0: ("calor", "heat", "muerte", "death", "asma", "asthma", "salud", "health",
          "hospital", "niños", "children", "embaraz", "pregnan", "anciano", "elder"),
    1.5: ("agua", "water", "inunda", "flood", "incendio", "fire", "humo", "smoke",
          "huracán", "hurricane", "tormenta", "storm", "gas", "plomo", "lead"),
    1.2: ("recibo", "bill", "luz", "electric", "trabajo", "job", "costo", "cost"),
}

STOP = set("""
 el la los las un una unos unas de del y o a en que es son por para con sin no se
 lo al su sus mi tu este esta eso esto como más muy ya si pero porque cuando
 the a an of and or to in that is are for with on it this these those not be as
 i you we they my your our their do does did can will just about from what why how
""".split())


def normalise(text: str) -> list[str]:
    text = text.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        text = text.replace(a, b)
    return [w for w in re.findall(r"[a-z]{4,}", text) if w not in STOP]


def harm_weight(text: str) -> float:
    low = text.lower()
    for weight, terms in sorted(HARM_TERMS.items(), reverse=True):
        if any(t in low for t in terms):
            return weight
    return 1.0


def recency(timestamps: list[str]) -> float:
    """Exponential decay, so a spike last week beats a trickle last year."""
    now = datetime.now(timezone.utc)
    scores = []
    for ts in timestamps:
        try:
            when = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        days = max(0.0, (now - when).total_seconds() / 86400)
        scores.append(math.pow(0.5, days / HALF_LIFE_DAYS))
    return max(scores) if scores else 0.0


def cluster(rows: list[dict]) -> dict[str, list[dict]]:
    """Group turns by their strongest shared keyword.

    Deliberately simple and inspectable: the topic key is a real word from the
    questions, so a human reading the gap queue can see why rows grouped.
    """
    by_word: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        for word in set(normalise(row.get("user_text", ""))):
            by_word[word].append(row)
    clusters: dict[str, list[dict]] = {}
    claimed: set[int] = set()
    for word, group in sorted(by_word.items(), key=lambda kv: -len(kv[1])):
        fresh = [r for r in group if r["id"] not in claimed]
        if len(fresh) < 2:
            continue
        clusters[word] = fresh
        claimed.update(r["id"] for r in fresh)
    return clusters


def detect(days: int = 14) -> list[GapRecord]:
    """Score every topic the deck could not answer."""
    rows = ledger.recent(days)
    gaps: list[GapRecord] = []
    for topic, group in cluster(rows).items():
        people = {r["user_ref"] for r in group}
        unanswered = [r for r in group if not r["answered"] or not r["matched_card"]]
        if not unanswered:
            continue
        rate = len(unanswered) / len(group)
        harm = max(harm_weight(r["user_text"]) for r in group)
        rec = recency([r["created_at"] for r in group])
        score = len(people) * rate * harm * rec
        gaps.append(GapRecord(
            gap_id=f"gap_{topic}",
            topic=topic,
            sample_questions=[r["user_text"][:200] for r in unanswered[:4]],
            distinct_conversations=len(people),
            unanswered_rate=round(rate, 3),
            harm_weight=harm,
            recency=round(rec, 3),
            score=round(score, 3),
            origin="ledger",
        ))
    gaps.sort(key=lambda g: g.score, reverse=True)
    ledger.save_gaps(gaps)
    return gaps


def cadence() -> dict:
    """Monthly when quiet, weekly when busy. A threshold on a count."""
    recent_count = ledger.count_since(7)
    weekly = recent_count >= WEEKLY_THRESHOLD
    return {
        "conversations_last_7_days": recent_count,
        "threshold": WEEKLY_THRESHOLD,
        "cadence": "weekly" if weekly else "monthly",
        "cards_per_cycle": 1,
        "next_mint_window": "every 7 days" if weekly else "every 30 days",
    }


def mintable() -> list[GapRecord]:
    """Gaps that clear the guardrail and may be sent to El Taller."""
    return [g for g in ledger.open_gaps()
            if g.distinct_conversations >= MIN_DISTINCT_CONVERSATIONS]


if __name__ == "__main__":
    import json

    print(json.dumps(cadence(), indent=2))
    found = detect()
    print(f"\n{len(found)} gap(s); {len(mintable())} clear the "
          f"{MIN_DISTINCT_CONVERSATIONS}-conversation guardrail\n")
    for g in found[:10]:
        flag = "MINTABLE" if g.distinct_conversations >= MIN_DISTINCT_CONVERSATIONS else "held"
        print(f"  {g.score:6.2f}  {g.topic:<18} people={g.distinct_conversations} "
              f"unanswered={g.unanswered_rate:.0%} harm={g.harm_weight}  [{flag}]")
