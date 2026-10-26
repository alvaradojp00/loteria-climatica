"""The demand ledger -- one row per conversation turn.

This is the raw material the gap detector reads. It is the reason the deck can
grow from what people actually ask rather than from what we assume they need.

Pseudonymous by design: `user_ref` is a stable hash, never an identifier, and
raw text is kept only so a human can read back what was asked.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DATA
from models import GapRecord, LedgerRow

DB = DATA / "ledger.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT, channel TEXT, user_ref TEXT, lang TEXT, lane TEXT,
    user_text TEXT, topic TEXT, tactic TEXT, matched_card TEXT,
    answered INTEGER, cost_usd REAL, created_at TEXT
);
CREATE INDEX IF NOT EXISTS turns_created ON turns(created_at);
CREATE INDEX IF NOT EXISTS turns_topic ON turns(topic);

CREATE TABLE IF NOT EXISTS gaps (
    gap_id TEXT PRIMARY KEY,
    topic TEXT, sample_questions TEXT, distinct_conversations INTEGER,
    unanswered_rate REAL, harm_weight REAL, recency REAL, score REAL,
    origin TEXT, minted_card TEXT, created_at TEXT
);
"""


@contextmanager
def conn():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        c.executescript(SCHEMA)
        yield c
        c.commit()
    finally:
        c.close()


def pseudonym(raw: str) -> str:
    """Stable per-person reference that is not an identifier."""
    return "u_" + hashlib.sha256(f"loteria::{raw}".encode()).hexdigest()[:12]


def write(row: LedgerRow) -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO turns (run_id, channel, user_ref, lang, lane, user_text,"
            " topic, tactic, matched_card, answered, cost_usd, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (row.run_id, row.channel, row.user_ref, row.lang, row.lane, row.user_text,
             row.topic, row.tactic, row.matched_card, int(row.answered),
             row.cost_usd, row.created_at),
        )


def recent(days: int = 14) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM turns WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",),
        ).fetchall()
    return [dict(r) for r in rows]


def count_since(days: int = 7) -> int:
    with conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM turns WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",),
        ).fetchone()[0]


def save_gaps(gaps: list[GapRecord]) -> None:
    with conn() as c:
        for g in gaps:
            c.execute(
                "INSERT INTO gaps (gap_id, topic, sample_questions,"
                " distinct_conversations, unanswered_rate, harm_weight, recency,"
                " score, origin, minted_card, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(gap_id) DO UPDATE SET"
                " distinct_conversations=excluded.distinct_conversations,"
                " unanswered_rate=excluded.unanswered_rate,"
                " recency=excluded.recency, score=excluded.score,"
                " sample_questions=excluded.sample_questions",
                (g.gap_id, g.topic, json.dumps(g.sample_questions, ensure_ascii=False),
                 g.distinct_conversations, g.unanswered_rate, g.harm_weight,
                 g.recency, g.score, g.origin, g.minted_card, g.created_at),
            )


def open_gaps() -> list[GapRecord]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM gaps WHERE minted_card IS NULL ORDER BY score DESC"
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["sample_questions"] = json.loads(d["sample_questions"] or "[]")
        out.append(GapRecord.model_validate(d))
    return out


def mark_minted(gap_id: str, card_id: str) -> None:
    with conn() as c:
        c.execute("UPDATE gaps SET minted_card=? WHERE gap_id=?", (card_id, gap_id))
