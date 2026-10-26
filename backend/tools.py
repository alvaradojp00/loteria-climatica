"""The tool library. The name and docstring are the instruction manual.

Shared by every lane: La Comadre cites the same cards La Contra does, and the
Boletin points at the same reading list. Tool returns are kept short on
purpose -- long returns are the quiet way an agent's cost triples.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from config import DATA
from events import emit
from models import Card

MAX_CARDS = 5
MAX_EXCERPT = 420


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", _fold(text))}


@lru_cache(maxsize=1)
def deck() -> tuple[Card, ...]:
    path = DATA / "cards.json"
    if not path.is_file():
        return ()
    return tuple(Card.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def sources() -> dict:
    return json.loads((DATA / "sources.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def tactics() -> dict:
    return json.loads((DATA / "tactics.json").read_text(encoding="utf-8"))


def refresh() -> None:
    """Call after El Taller mints a card so the chat can cite it immediately."""
    deck.cache_clear()


# ------------------------------------------------------------------- tools

def search_cards(query: str, lang: str = "es") -> str:
    """Search the Loteria Climatica deck for cards that answer a claim or question.

    Use this first for any claim. Each card carries the myth as people say it,
    the evidence-backed truth, and one concrete action. Returns the closest
    matches with their card number so you can point the person at it.
    """
    q = _words(query)
    scored: list[tuple[float, Card]] = []
    for card in deck():
        if card.status == "rejected":
            continue
        hay = " ".join([
            card.name.en, card.name.es, card.myth.en, card.myth.es,
            card.truth_headline.en, card.truth_headline.es,
            card.body.en, card.body.es, card.category, card.motif,
        ])
        other = _words(hay)
        if not other or not q:
            continue
        overlap = len(q & other) / len(q)
        if overlap > 0:
            scored.append((overlap, card))
    scored.sort(key=lambda t: -t[0])
    hits = scored[:MAX_CARDS]
    emit("tool_called", tool="search_cards", query=query[:80],
         matched=[c.id for _, c in hits])
    if not hits:
        return json.dumps({"matches": [], "note": "no card covers this yet"})
    return json.dumps({
        "matches": [
            {
                "card": c.id,
                "name": c.name.get(lang),
                "myth": c.myth.get(lang),
                "truth": c.truth_headline.get(lang),
                "body": c.body.get(lang)[:MAX_EXCERPT],
                "action": c.action.get(lang),
                "frame": (c.frame.frame if c.frame else None),
                "match": round(score, 2),
            }
            for score, c in hits
        ]
    }, ensure_ascii=False)


def search_sources(query: str) -> str:
    """Search the curated library of partner-organisation publications.

    CAAD, GreenLatinos, Friends of the Earth and Climate Power En Accion have
    published on this terrain. Returns specific reports, never an
    organisation's homepage.
    """
    q = _words(query)
    out = []
    for org in sources()["organizations"]:
        for pub in org["publications"]:
            hay = _words(pub["title"] + " " + " ".join(pub["topics"]) + " " + org["role"])
            score = len(q & hay) / len(q) if q else 0
            if score > 0:
                out.append({
                    "organization": org["name"],
                    "title": pub["title"],
                    "url": pub["url"],
                    "framing_note": org["framing_note"],
                    "match": round(score, 2),
                })
    out.sort(key=lambda d: -d["match"])
    emit("tool_called", tool="search_sources", query=query[:80], found=len(out))
    return json.dumps({"sources": out[:4]}, ensure_ascii=False)


def list_tactics() -> str:
    """List the named manipulation patterns, with how each works and its tell.

    Use this when a claim is misleading by construction rather than simply
    wrong. Naming the pattern teaches something that outlasts the correction.
    """
    emit("tool_called", tool="list_tactics")
    return json.dumps({
        "tactics": [
            {
                "key": t["key"],
                "name": t["name"]["en"],
                "nombre": t["name"]["es"],
                "how_it_works": t["how_it_works"]["en"],
                "tell": t["tell"]["en"],
            }
            for t in tactics()["tactics"]
        ]
    }, ensure_ascii=False)


def get_resources(topic: str = "") -> str:
    """Get reporting channels and organisations for someone who wants to act.

    Covers how to report a post on each platform and which organisations work
    on this. Use when a person asks what they can do beyond the conversation.
    """
    emit("tool_called", tool="get_resources", topic=topic[:60])
    s = sources()
    return json.dumps({
        "reporting": s["reporting_channels"],
        "organizations": [
            {"name": o["name"], "url": o["url"], "role": o["role"]}
            for o in s["organizations"]
        ],
    }, ensure_ascii=False)
