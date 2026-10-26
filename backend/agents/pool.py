"""The shared specialist pool.

Four bosses draw on these same agents. One Researcher means the Boletin and
El Taller cite evidence to the same standard; one Framer means every lane
routes through the same measured data. One prompt to improve, one place to fix.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai.capabilities import WebSearch

from agents.base import build, run
from config import DATA
from events import emit
from models import Evidence, FrameChoice, SpecialistReport


# ----------------------------------------------------------------- outputs

class ResearchOut(BaseModel):
    findings: str
    citations: list[Evidence] = Field(default_factory=list)
    confidence: float = 0.0
    status: Literal["ok", "empty"] = "ok"


class CardDraft(BaseModel):
    name_es: str
    name_en: str
    myth: str
    truth_headline: str
    body: str
    action: str = ""
    category: str = "general"
    motif_brief: str


class SpanishFace(BaseModel):
    myth: str
    truth_headline: str
    body: str
    action: str = ""


class ArtistOut(BaseModel):
    svg: str
    shape_count: int = 0
    colors_used: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------ frames

_FRAMES: dict | None = None


def frame_guidance() -> dict:
    global _FRAMES
    if _FRAMES is None:
        _FRAMES = json.loads((DATA / "frames.json").read_text(encoding="utf-8"))
    return _FRAMES


def get_frame_guidance(topic: str = "", audience: str = "") -> str:
    """Measured persuasion data from the 2025 GreenLatinos / Grow Progress test.

    Returns the five value frames with their measured lift on each outcome,
    the subgroups each is strongest with, and the subgroups where each
    backlashes. 1,797 Latinx adults, randomised, weighted.
    """
    g = frame_guidance()
    emit("tool_called", tool="get_frame_guidance", topic=topic, audience=audience)
    return json.dumps(
        {
            "study": g["study"],
            "outcomes": g["outcomes"],
            "frames": {
                k: {
                    "label": v["label"],
                    "topline_lift": v["topline_lift"],
                    "persuasive_with": v["persuasive_with"],
                    "backlash_with": v["backlash_with"],
                    "verdict": v["verdict"],
                }
                for k, v in g["frames"].items()
            },
            "selection_rules": g["selection_rules"],
        },
        ensure_ascii=False,
    )


# -------------------------------------------------------------- specialists

async def researcher(claim: str) -> SpecialistReport:
    """Find real evidence, or report that there is none."""
    agent = build("researcher", ResearchOut, capabilities=[WebSearch()])
    out: ResearchOut = await run(
        agent,
        f"Claim circulating in Latine communities:\n\n{claim}\n\n"
        "Find what the evidence actually says. Cite specific pages.",
        label="researcher",
    )
    if out.citations:
        emit("evidence_found", count=len(out.citations),
             sources=[c.source_name for c in out.citations])
    return SpecialistReport(
        role="researcher",
        status="ok" if out.status == "ok" and out.citations else "empty",
        findings=out.findings,
        citations=out.citations,
        confidence=out.confidence,
    )


async def framer(claim: str, findings: str, audience: str = "general mixed audience") -> FrameChoice:
    """Choose the value frame from measured lift, and record what was rejected."""
    agent = build("framer", FrameChoice, tools=[get_frame_guidance])
    out: FrameChoice = await run(
        agent,
        f"Claim: {claim}\n\nEvidence summary: {findings}\n\nAudience: {audience}\n\n"
        "Call get_frame_guidance, then choose the frame with the best measured "
        "lift for the outcome this claim attacks.",
        label="framer",
    )
    emit("frame_selected", frame=out.frame, lift=out.measured_lift,
         rejected=out.rejected)
    return out


async def writer(claim: str, report: SpecialistReport, frame: FrameChoice,
                 feedback: str = "") -> CardDraft:
    """Write the English face of the card inside the chosen frame."""
    agent = build("writer", CardDraft)
    cites = "\n".join(
        f"- {c.claim} [{c.source_name}] {c.url}\n  excerpt: {c.excerpt[:260]}"
        for c in report.citations
    )
    task = (
        f"Myth to answer:\n{claim}\n\n"
        f"Evidence you may use (nothing outside this):\n{cites}\n\n"
        f"Researcher summary: {report.findings}\n\n"
        f"Value frame: {frame.frame.upper()} "
        f"(measured lift {frame.measured_lift}; {frame.audience_note})\n"
        f"Framing rationale: {frame.rationale}\n"
    )
    if feedback:
        task += f"\nThis draft was rejected. Fix exactly these problems:\n{feedback}\n"
    return await run(agent, task, label="writer")


async def transcreator(draft: CardDraft) -> SpanishFace:
    """Spanish that reads as Spanish, not as translated English."""
    agent = build("transcreator", SpanishFace)
    return await run(
        agent,
        f"Card name: {draft.name_es}\n\nEnglish myth: {draft.myth}\n"
        f"English truth headline: {draft.truth_headline}\n"
        f"English body: {draft.body}\n"
        f"English action: {draft.action}\n",
        label="transcreator",
    )


async def artist(motif_brief: str, palette, feedback: str = "") -> ArtistOut:
    """Draw the one region of the card that is not template."""
    agent = build("artist", ArtistOut)
    task = (
        f"Motif to draw: {motif_brief}\n\n"
        f"Card palette -- sky behind the motif: {palette.sky}, "
        f"ground below it: {palette.ground}, seam: {palette.seam}\n"
        f"Fills available to you: {', '.join(palette.motif) or 'choose flat saturated colours'}\n"
    )
    if feedback:
        task += f"\nThe previous attempt was rejected. Fix exactly these problems:\n{feedback}\n"
    return await run(agent, task, label="artist")
