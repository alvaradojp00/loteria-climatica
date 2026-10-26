"""The two shared gates. Either can reject a card back to the specialist.

They reject upward across pipeline boundaries: the Verifier fails a Taller
card, a Contra draft and a Boletin topline alike. One guardrail, three
enforcement points.

The visual gate is deliberately deterministic. Style conformance is a question
with a right answer -- is the fill inside the palette, is there text in the
motif, is it inside the safe box -- and a model asked to judge it would be
slower, costlier and less consistent than the arithmetic.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from agents.base import build, run
from events import emit
from models import Evidence

# --- content gate ----------------------------------------------------------


class VerifyOut(BaseModel):
    passed: bool
    problems: list[str] = Field(default_factory=list)
    severity: Literal["none", "fixable", "blocking"] = "none"
    notes: str = ""


async def verify_content(draft, citations: list[Evidence], frame) -> VerifyOut:
    agent = build("verifier", VerifyOut)
    cites = "\n".join(
        f"- {c.claim} [{c.source_name}] {c.url}\n  excerpt: {c.excerpt[:300]}"
        for c in citations
    ) or "(no citations supplied)"
    out: VerifyOut = await run(
        agent,
        f"CARD DRAFT\n"
        f"name: {draft.name_es}\n"
        f"myth: {draft.myth}\n"
        f"truth_headline: {draft.truth_headline}\n"
        f"body: {draft.body}\n"
        f"action: {draft.action}\n\n"
        f"FRAME: {frame.frame} (measured lift {frame.measured_lift}; "
        f"{frame.audience_note}); rejected: {', '.join(frame.rejected) or 'none recorded'}\n\n"
        f"EVIDENCE AVAILABLE\n{cites}\n",
        label="verifier",
    )
    if not out.passed:
        emit("qa_rejected", gate="verifier", severity=out.severity, problems=out.problems)
    return out


# --- visual gate (deterministic) -------------------------------------------

ALLOWED_TAGS = {"path", "circle", "ellipse", "rect", "polygon", "polyline", "line", "g"}
BANNED_TAGS = {"text", "tspan", "image", "foreignObject", "svg", "style", "script",
               "linearGradient", "radialGradient", "filter", "use", "symbol"}
SAFE_BOX = (-300, -330, 300, 300)   # x0, y0, x1, y1
NUM = re.compile(r"-?\d+(?:\.\d+)?")
HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def _hex_distance(a: str, b: str) -> int:
    a, b = a.lstrip("#"), b.lstrip("#")
    return sum(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) for i in (0, 2, 4))


def _attr(tag: str, name: str, default: float = 0.0) -> float:
    m = re.search(rf'\b{name}\s*=\s*"(-?[\d.]+)"', tag)
    return float(m.group(1)) if m else default


def _extent(svg: str) -> tuple[list[float], list[float]]:
    """Real bounds of the motif.

    Parsed per element rather than by scraping every number: `width="450"` on a
    rect at `x="-225"` is an extent, not a coordinate, and treating it as one
    reported half the deck as out of bounds when it was centred correctly.
    """
    xs: list[float] = []
    ys: list[float] = []
    for tag in re.findall(r"<[^>]+>", svg):
        kind = re.match(r"<\s*([A-Za-z]+)", tag)
        if not kind:
            continue
        name = kind.group(1)
        if name == "rect":
            x, y = _attr(tag, "x"), _attr(tag, "y")
            xs += [x, x + _attr(tag, "width")]
            ys += [y, y + _attr(tag, "height")]
        elif name in {"circle", "ellipse"}:
            cx, cy = _attr(tag, "cx"), _attr(tag, "cy")
            rx = _attr(tag, "r") or _attr(tag, "rx")
            ry = _attr(tag, "r") or _attr(tag, "ry")
            xs += [cx - rx, cx + rx]
            ys += [cy - ry, cy + ry]
        elif name == "line":
            xs += [_attr(tag, "x1"), _attr(tag, "x2")]
            ys += [_attr(tag, "y1"), _attr(tag, "y2")]
        elif name in {"path", "polygon", "polyline"}:
            body = re.search(r'\b(?:d|points)\s*=\s*"([^"]*)"', tag)
            if not body:
                continue
            nums = [float(n) for n in NUM.findall(re.sub(r"[A-Za-z]", " ", body.group(1)))]
            xs += nums[0::2]
            ys += nums[1::2]
    return xs, ys


def visual_lint(svg: str, palette) -> list[str]:
    """Style conformance against the measured originals. No model involved."""
    problems: list[str] = []

    tags = re.findall(r"<\s*([A-Za-z][A-Za-z0-9]*)", svg)
    for t in tags:
        if t in BANNED_TAGS:
            problems.append(f"forbidden element <{t}> in motif "
                            f"(the motif carries no text, images or gradients)")
        elif t not in ALLOWED_TAGS:
            problems.append(f"unexpected element <{t}>")
    if not tags:
        problems.append("motif is empty")

    shapes = [t for t in tags if t != "g"]
    if len(shapes) > 26:
        problems.append(f"{len(shapes)} shapes: too intricate to read at thumbnail size")
    if 0 < len(shapes) < 3:
        problems.append(f"only {len(shapes)} shape(s): too sparse for a card motif")

    if "stroke-width" in svg:
        problems.append("motif overrides stroke-width (one uniform outline is set by the template)")
    if re.search(r'stroke\s*=\s*"(?!none)', svg):
        problems.append("motif sets its own stroke colour (it inherits the template's)")
    if "opacity" in svg:
        problems.append("motif uses opacity (fills are flat and solid)")

    fills = {f.upper() for f in HEX.findall(svg)}
    if len(fills) > 5:
        problems.append(f"{len(fills)} fill colours: at most 5")
    allowed = {c.upper() for c in list(palette.motif) + [palette.sky, palette.ground, palette.seam]}
    for f in fills:
        if allowed and min((_hex_distance(f, a) for a in allowed), default=999) > 210:
            problems.append(f"fill {f} is outside the card palette")
    for f in fills:
        if _hex_distance(f, palette.ground) < 48:
            problems.append(f"fill {f} is too close to the ground colour to read against it")

    xs, ys = _extent(svg)
    if xs and ys:
        x0, y0, x1, y1 = SAFE_BOX
        if min(xs) < x0 - 40 or max(xs) > x1 + 40 or min(ys) < y0 - 40 or max(ys) > y1 + 40:
            problems.append(
                f"motif spans x[{min(xs):.0f},{max(xs):.0f}] y[{min(ys):.0f},{max(ys):.0f}], "
                f"outside the safe box and will be clipped"
            )
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        if span < 300:
            problems.append(f"motif only spans {span:.0f}px: too small in the panel")

    if problems:
        emit("qa_rejected", gate="visual_qa", problems=problems)
    return problems
