"""Typed shapes for everything that moves between agents.

Lecture 2's rule: AI models need a strict schema or you get prose instead of
usable rows. Every handoff in this system is one of these.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "es"]
Provenance = Literal["original", "generated"]
Status = Literal["draft", "needs_human", "approved", "rejected"]
FrameName = Literal["health", "family", "faith", "economy_jobs", "villain"]
Lane = Literal["comadre", "contra", "taller", "boletin"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Bilingual(BaseModel):
    en: str = ""
    es: str = ""

    def get(self, lang: str) -> str:
        return self.es if lang == "es" else self.en


class Evidence(BaseModel):
    """A claim backed by a real, fetched source. No source, no claim."""

    claim: str
    source_name: str
    url: str
    excerpt: str = ""
    retrieved_at: str = Field(default_factory=now)


class FrameChoice(BaseModel):
    """Which value frame was used, why, and what was rejected.

    The rejected alternatives matter as much as the pick -- they are the
    evidence that the agent consulted measured data rather than taste.
    """

    frame: FrameName
    measured_lift: float | None = None
    audience_note: str = ""
    rationale: str = ""
    rejected: list[str] = Field(default_factory=list)


class Palette(BaseModel):
    sky: str = "#F04E23"      # upper zone of the horizon gradient
    ground: str = "#49B848"   # lower zone
    seam: str = "#F2C230"     # the bleed where they meet
    motif: list[str] = Field(default_factory=list)


class Card(BaseModel):
    """One lotería card. Cards 1-12 are extracted; the rest are manufactured."""

    id: str                      # "01"
    number: int
    slug: str                    # "la-ola-de-calor"
    name: Bilingual              # LA OLA DE CALOR / THE HEAT WAVE
    category: str = "general"
    motif: str = ""              # short description of the central object
    motif_svg: str = ""          # generated cards only
    palette: Palette = Field(default_factory=Palette)

    myth: Bilingual = Field(default_factory=Bilingual)
    truth_headline: Bilingual = Field(default_factory=Bilingual)
    body: Bilingual = Field(default_factory=Bilingual)
    action: Bilingual = Field(default_factory=Bilingual)

    provenance: Provenance = "generated"
    status: Status = "draft"
    frame: FrameChoice | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    created_by: str = ""         # agent chain that produced it
    created_at: str = Field(default_factory=now)
    approved_by: str | None = None
    gap_id: str | None = None    # the demand that caused it to exist
    notes: str = ""


class ClaimPacket(BaseModel):
    """What the Extractor returns from a pasted forward or screenshot.

    `embedded_instructions` is the injection tripwire: if the payload contains
    instruction-shaped text, the boss quarantines instead of complying.
    """

    claim_text: str
    language: Lang = "en"
    platform: str | None = None
    visible_engagement: str | None = None
    embedded_instructions: bool = False
    instruction_excerpt: str = ""
    notes: str = ""


class SpecialistReport(BaseModel):
    """The uniform envelope every boss->specialist handoff returns.

    Bosses synthesize only from these. A boss asserting a fact that is not in
    a report is a bug the Verifier catches.
    """

    role: str
    status: Literal["ok", "empty", "refused", "error"] = "ok"
    findings: str = ""
    citations: list[Evidence] = Field(default_factory=list)
    confidence: float = 0.0
    detail: dict = Field(default_factory=dict)


class Route(BaseModel):
    """El Despachador's only output: a pick and a confidence. No prose."""

    lane: Lane
    confidence: float
    reason: str = ""


class LedgerRow(BaseModel):
    """One turn of demand. The raw material the gap detector reads."""

    run_id: str
    channel: str
    user_ref: str
    lang: str
    lane: str
    user_text: str
    topic: str = ""
    tactic: str | None = None
    matched_card: str | None = None
    answered: bool = True
    cost_usd: float = 0.0
    created_at: str = Field(default_factory=now)


class SignalRecord(BaseModel):
    """One item of monitored disinformation, from any ingest adapter."""

    source: str                  # "fixture" | "open" | "junkipedia"
    platform: str = ""
    language: str = "en"
    captured_at: str = Field(default_factory=now)
    claim_text: str = ""
    url: str = ""
    reach_estimate: int | None = None
    tactic: str | None = None
    topic_cluster: str | None = None


class GapRecord(BaseModel):
    """A topic the deck cannot answer, scored by measured demand."""

    gap_id: str
    topic: str
    sample_questions: list[str] = Field(default_factory=list)
    distinct_conversations: int = 0
    unanswered_rate: float = 0.0
    harm_weight: float = 1.0
    recency: float = 1.0
    score: float = 0.0
    origin: Literal["ledger", "boletin", "manual"] = "ledger"
    minted_card: str | None = None
    created_at: str = Field(default_factory=now)


class Topline(BaseModel):
    """One item in a biweekly brief."""

    headline: Bilingual
    what_is_claimed: Bilingual
    tactic: str
    prebunk: Bilingual
    frame: FrameChoice | None = None
    covering_card: str | None = Field(
        default=None,
        description="Two-digit id of the card that already answers this, e.g. \"07\". "
                    "Null when no card covers it.",
    )
    gap_id: str | None = None
    reading: list[Evidence] = Field(default_factory=list)


class Brief(BaseModel):
    brief_id: str
    period_start: str
    period_end: str
    adapter_used: str
    toplines: list[Topline] = Field(default_factory=list)
    created_at: str = Field(default_factory=now)
