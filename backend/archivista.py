"""La Archivista -- custodian of the deck. Deterministic, not an agent.

Deck reads, name uniqueness, dedupe, numbering and publish-on-approval. Keeping
this out of the model layer is why a bad generation cannot corrupt the deck: a
card that collides with an existing one is rejected by arithmetic, not by
judgement.
"""

from __future__ import annotations

import json
import re
import unicodedata

from config import DATA
from models import Card


def deck() -> list[Card]:
    path = DATA / "cards.json"
    if not path.is_file():
        return []
    return [Card.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"^(el|la|los|las|un|una)\s+", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def taken_names() -> dict[str, str]:
    """Folded name -> card id, so 'El Recibo' and 'el recibo' collide."""
    return {_fold(c.name.es): c.id for c in deck()}


def name_collision(name_es: str, ignore_id: str | None = None) -> str | None:
    hit = taken_names().get(_fold(name_es))
    return None if hit == ignore_id else hit


def topic_collision(myth: str, threshold: float = 0.62) -> str | None:
    """Catch a second card about a claim the deck already answers."""
    words = set(re.findall(r"[a-záéíóúñ]{4,}", myth.lower()))
    if not words:
        return None
    for card in deck():
        for existing in (card.myth.es, card.myth.en):
            other = set(re.findall(r"[a-záéíóúñ]{4,}", existing.lower()))
            if not other:
                continue
            overlap = len(words & other) / min(len(words), len(other))
            if overlap >= threshold:
                return card.id
    return None


def next_number() -> int:
    return max((c.number for c in deck()), default=0) + 1


def save(card: Card) -> None:
    path = DATA / "cards.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    rows = [r for r in rows if r["id"] != card.id]
    rows.append(card.model_dump())
    rows.sort(key=lambda r: r["number"])
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def approve(card_id: str, by: str) -> Card | None:
    rows = deck()
    for c in rows:
        if c.id == card_id:
            c.status = "approved"
            c.approved_by = by
            save(c)
            return c
    return None
