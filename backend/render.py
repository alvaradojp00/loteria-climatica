"""The card template. Deterministic -- not a model output.

This is why generated cards look like the originals instead of looking
AI-made: the paper, the panel, the horizon gradient, the grain, the number,
the nameplate and the type are all template. The only thing an agent
contributes is the central motif, as constrained SVG paths.

    python render.py --card 01 --face front --out ../output/preview
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from config import DATA, REPO
from models import Card

# --- the measured visual system -------------------------------------------
PAPER = "#EDEDE8"
INK = "#2E2520"
W, H = 1200, 1800           # 4x6 at 300dpi
PANEL = (96, 250, 1008, 1512)   # x0, y0, x1, y1 -- the art panel
RULE = 14                   # panel border weight
STROKE = 18                 # motif outline weight: one uniform width, always

# Type stack. Archivo Black / Anton are the closest free equivalents to the
# originals' heavy condensed grotesque; the fallbacks keep the card legible if
# neither is installed.
DISPLAY = "'Archivo Black','Anton',Impact,'Haettenschweiler',sans-serif"
BODY = "'Inter','Helvetica Neue',Arial,sans-serif"


def _grain(seed: int = 7) -> str:
    """Riso-style grain. The single most important cue that it was printed."""
    return f"""
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"
                  seed="{seed}" result="noise"/>
    <feColorMatrix in="noise" type="saturate" values="0" result="mono"/>
    <feComponentTransfer in="mono" result="grain">
      <feFuncA type="linear" slope="0.17"/>
    </feComponentTransfer>
    <feComposite operator="in" in="grain" in2="SourceGraphic"/>
  </filter>
  <filter id="paperTooth" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="3" seed="{seed + 4}"/>
    <feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer><feFuncA type="linear" slope="0.09"/></feComponentTransfer>
  </filter>"""


def _horizon(sky: str, ground: str, seam: str) -> str:
    """The signature move: two zones with a soft blended seam, not a hard line."""
    return f"""
  <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="{sky}"/>
    <stop offset="34%"  stop-color="{sky}"/>
    <stop offset="47%"  stop-color="{seam}"/>
    <stop offset="60%"  stop-color="{ground}"/>
    <stop offset="100%" stop-color="{ground}"/>
  </linearGradient>"""


def _fit(text: str, max_chars: int) -> list[str]:
    return textwrap.wrap(text.upper(), width=max_chars) or [""]


def _lines(lines: list[str], x: int, y: int, size: int, lead: float,
           fill: str = INK, anchor: str = "middle", family: str = DISPLAY,
           style: str = "", extra: str = "") -> str:
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y + int(i * size * lead)}" font-family="{family}" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'{style} {extra}>{escape(line)}</text>'
        )
    return "\n  ".join(out)


# --- faces -----------------------------------------------------------------

def front_svg(card: Card, lang: str = "es") -> str:
    p = card.palette
    x0, y0, x1, y1 = PANEL
    pw, ph = x1 - x0, y1 - y0
    name = (card.name.es if lang == "es" else card.name.en).upper()
    # the nameplate shrinks rather than wrapping -- the originals never wrap
    name_size = 96 if len(name) <= 15 else 78 if len(name) <= 20 else 62

    motif = card.motif_svg or _placeholder_motif()

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img" aria-label="{escape(name)}">
  <defs>{_grain()}{_horizon(p.sky, p.ground, p.seam)}
    <clipPath id="panelClip"><rect x="{x0}" y="{y0}" width="{pw}" height="{ph}"/></clipPath>
  </defs>

  <rect width="{W}" height="{H}" fill="{PAPER}"/>
  <rect width="{W}" height="{H}" filter="url(#paperTooth)" opacity="0.5"/>

  <g clip-path="url(#panelClip)">
    <rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="url(#horizon)"/>
    <!-- motif: the only agent-generated region on the card -->
    <g transform="translate({x0 + pw / 2}, {y0 + ph * 0.46}) scale(1.0)"
       fill="none" stroke="{INK}" stroke-width="{STROKE}"
       stroke-linejoin="round" stroke-linecap="round">
      {motif}
    </g>
    <text x="{x0 + 46}" y="{y0 + 92}" font-family="{DISPLAY}" font-size="72"
          fill="{INK}">{card.number}</text>
    {_lines([name], x0 + pw // 2, y1 - 54, name_size, 1.0)}
    <rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" filter="url(#grain)" opacity="0.9"/>
  </g>
  <rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="none"
        stroke="{INK}" stroke-width="{RULE}"/>

  <text x="86" y="{H - 96}" font-family="{BODY}" font-size="26" font-weight="700"
        fill="{INK}" letter-spacing="2">LEARN MORE</text>
  <text x="86" y="{H - 48}" font-family="{DISPLAY}" font-size="46" fill="{INK}"
        font-style="italic">loteriaclimatica.org</text>
  <text x="{W - 86}" y="{H - 96}" font-family="{BODY}" font-size="26" font-weight="700"
        fill="{INK}" text-anchor="end" letter-spacing="2">PLAY THE DECK</text>
  <text x="{W - 86}" y="{H - 48}" font-family="{DISPLAY}" font-size="46" fill="{INK}"
        text-anchor="end" font-style="italic">#LoteriaClimatica</text>
</svg>"""


def back_svg(card: Card, lang: str = "en") -> str:
    p = card.palette
    truth = card.truth_headline.get(lang)
    myth = card.myth.get(lang)
    body = card.body.get(lang)

    truth_lines = _fit(truth, 17)
    truth_size = 126 if len(truth_lines) <= 4 else 104 if len(truth_lines) <= 6 else 86
    myth_lines = _fit(myth, 36)
    body_lines = textwrap.wrap(body, width=56)
    body_size = 34 if len(body_lines) <= 11 else 30

    truth_y = 300
    myth_y = truth_y + int(len(truth_lines) * truth_size * 0.94) + 170
    body_y = myth_y + int(len(myth_lines) * 50) + 80

    strike = []
    for i, line in enumerate(myth_lines):
        yy = myth_y + i * 50
        strike.append(
            f'<text x="{W // 2}" y="{yy}" font-family="{DISPLAY}" font-size="44" '
            f'fill="{INK}" text-anchor="middle" font-style="italic" '
            f'text-decoration="line-through">{escape(line.upper())}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img" aria-label="{escape(card.name.get(lang))} - truth and myth">
  <defs>{_grain(11)}
    <linearGradient id="wash" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{p.sky}"   stop-opacity="1"/>
      <stop offset="40%"  stop-color="{p.seam}"  stop-opacity="0.95"/>
      <stop offset="66%"  stop-color="{p.ground}" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="{PAPER}"   stop-opacity="0"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="34"/>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" fill="{PAPER}"/>
  <rect x="40" y="60" width="{W - 80}" height="{int(H * 0.58)}"
        fill="url(#wash)" filter="url(#soft)"/>
  <rect width="{W}" height="{H}" filter="url(#paperTooth)" opacity="0.5"/>

  <rect x="{W // 2 - 110}" y="{truth_y - 148}" width="220" height="74" rx="37" fill="{INK}"/>
  <text x="{W // 2}" y="{truth_y - 97}" font-family="{BODY}" font-size="40"
        font-weight="700" fill="{PAPER}" text-anchor="middle" letter-spacing="3">TRUTH:</text>

  {_lines(truth_lines, W // 2, truth_y, truth_size, 0.94, style='font-style="italic"')}

  <rect x="{W // 2 - 96}" y="{myth_y - 118}" width="192" height="66" rx="33"
        fill="none" stroke="{INK}" stroke-width="4"/>
  <text x="{W // 2}" y="{myth_y - 72}" font-family="{BODY}" font-size="36"
        font-weight="700" fill="{INK}" text-anchor="middle" letter-spacing="3">MYTH:</text>
  {chr(10).join("  " + s for s in strike)}

  {_lines(body_lines, W // 2, body_y, body_size, 1.42, family=BODY,
          style='font-weight="700"')}
</svg>"""


def _placeholder_motif() -> str:
    """Used only when no Artist output exists yet."""
    return ('<circle cx="0" cy="0" r="210" fill="none"/>'
            '<path d="M -150 90 L 0 -160 L 150 90 Z"/>')


# --- api -------------------------------------------------------------------

def original_front(card: Card) -> str | None:
    """Repo-relative path to an original card's real printed front.

    Cards 1-12 keep their own artwork. The template draws the frame for
    generated cards; it never redraws someone else's illustration.
    """
    if card.provenance != "original":
        return None
    # Prefer the web-optimised copy: the print masters are 3-6 MB each and the
    # deck page needs twelve at once. make_web_art.py writes these.
    web = REPO / "assets" / "web" / f"{card.number:02d}-{card.slug}.jpg"
    if web.is_file():
        return f"assets/web/{web.name}"

    from agents.genesis import sources_for

    path = (sources_for(card.number, "en")["front"]
            or sources_for(card.number, "es")["front"])
    return str(path.relative_to(REPO)).replace("\\", "/") if path else None


def load_deck() -> list[Card]:
    raw = json.loads((DATA / "cards.json").read_text(encoding="utf-8"))
    return [Card.model_validate(r) for r in raw]


def render(card: Card, face: str = "front", lang: str = "es") -> str:
    return front_svg(card, lang) if face == "front" else back_svg(card, lang)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", default="01")
    ap.add_argument("--face", default="front", choices=["front", "back", "both"])
    ap.add_argument("--lang", default=None)
    ap.add_argument("--out", default="../output/preview")
    args = ap.parse_args()

    deck = {c.id: c for c in load_deck()}
    if args.card == "all":
        targets = list(deck.values())
    else:
        targets = [deck[args.card]]

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    faces = ["front", "back"] if args.face == "both" else [args.face]
    for card in targets:
        for face in faces:
            if face == "front" and card.provenance == "original":
                print(f"skip  {card.id} front - uses original artwork "
                      f"({original_front(card)})")
                continue
            lang = args.lang or ("es" if face == "front" else "en")
            path = out / f"{card.id}-{card.slug}-{face}-{lang}.svg"
            path.write_text(render(card, face, lang), encoding="utf-8")
            print("wrote", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
