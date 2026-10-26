"""Genesis -- build the seed deck from the twelve original cards.

Runs once. The Extractor (vision) reads each card's front and text face in
each language; palettes are measured deterministically from the pixels rather
than guessed by the model. Output: data/cards.json (provenance "original")
and data/style_profile.json, which is the style corpus the Artist and Visual
QA agents are held to later.

    python -m agents.genesis            # full run
    python -m agents.genesis --cards 1 7 11
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from config import ASSETS, DATA, MODEL, client, prompt
from models import Bilingual, Card, Palette, now
from pricing import Meter, Usage, enrich_usage

CARDS = ASSETS / "loteria-cards"

# number -> (slug, Spanish name, English name, category)
CATALOG: dict[int, tuple[str, str, str, str]] = {
    1: ("la-ola-de-calor", "La Ola de Calor", "The Heat Wave", "health"),
    2: ("la-silla", "La Silla", "The Chair", "community"),
    3: ("una-velita", "Una Velita", "A Candle", "energy"),
    4: ("el-arcoiris", "El Arcoíris", "The Rainbow", "community"),
    5: ("la-energia", "La Energía", "The Energy", "energy"),
    6: ("el-menu", "El Menú", "The Menu", "food"),
    7: ("el-metano", "El Metano", "Methane", "energy"),
    8: ("el-plastico", "El Plástico", "Plastic", "waste"),
    9: ("la-salud", "La Salud", "Health", "health"),
    10: ("la-transicion-justa", "La Transición Justa", "The Just Transition", "justice"),
    11: ("la-justicia-climatica", "La Justicia Climática", "Climate Justice", "justice"),
    12: ("la-deforestacion", "La Deforestación", "Deforestation", "land"),
}

TOKEN = {  # filename token used by the print assets
    1: "LaOladeCalor", 2: "LaSilla", 3: "UnaVelita", 4: "ElArcoiris",
    5: "LaEnergia", 6: "ElMenu", 7: "ElMetano", 8: "ElPlastico",
    9: "LaSalud", 10: "LaTransicionJusta", 11: "LaJusticiaClimatica",
    12: "LaDeforestacion",
}
SOCIAL_INDEX = {7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6}

PAPER = (0xED, 0xED, 0xE8)
INK = (0x2E, 0x25, 0x20)


# ---------------------------------------------------------------- manifest

def _first(*candidates: Path) -> Path | None:
    for c in candidates:
        if c and c.is_file():
            return c
    return None


def sources_for(number: int, lang: str) -> dict[str, Path | None]:
    """Locate the best available images for one card in one language.

    Falls back to the social layout where a print face is missing -- English
    card 11 has no print files, and the Spanish set has no separate fronts.
    """
    group = "cards-01-06" if number <= 6 else "cards-07-12"
    tok = TOKEN[number]
    langword = "English" if lang == "en" else "Spanish"
    print_dir = CARDS / group / lang / "print-4x6"
    social_dir = CARDS / group / lang / ("social-4x5" if number > 6 else "social")

    front = _first(
        print_dir / f"GreenLatinos-LoteriaCard-4x6in-Front-{number}-{tok}-{langword}.png",
        print_dir / f"GreenLatinos-LoteriaCard-4x6in-Front-{number}-{tok}-{langword}(1).png",
        # Spanish has no separate fronts for 1-6; the art is identical and the
        # name is printed in Spanish on both, so the English front is correct.
        CARDS / group / "en" / "print-4x6"
        / f"GreenLatinos-LoteriaCard-4x6in-Front-{number}-{tok}-English.png",
    )
    back = _first(
        print_dir / f"GreenLatinos-LoteriaCard-4x6in-Back-{number}-{tok}-{langword}.png",
        print_dir / f"GreenLatinos-LoteriaCard-4x6in-Back-{number}-{tok}-{langword}(1).png",
    )
    social = None
    if number in SOCIAL_INDEX:
        social = _first(
            social_dir
            / f"GreenLatinos-LoteriaCard-Social-{SOCIAL_INDEX[number]}-{tok}-{langword}.png",
            social_dir / f"GreenLatinos-LoteriaCards-{tok}.png",
        )
    return {"front": front, "back": back, "social": social}


# ------------------------------------------------------- palette (measured)

def _hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def _pixels(img):
    """Pillow 14 renames getdata(); support both."""
    fn = getattr(img, "get_flattened_data", None) or img.getdata
    return fn()


def _near(a, b, tol: int) -> bool:
    return sum(abs(x - y) for x, y in zip(a[:3], b[:3])) <= tol


def measure_palette(front: Path) -> Palette:
    """Read the real colours off the card instead of asking a model to guess."""
    im = Image.open(front).convert("RGB")
    w, h = im.size
    # the art panel sits inside the paper margin
    panel = im.crop((int(w * 0.09), int(h * 0.15), int(w * 0.91), int(h * 0.84)))
    pw, ph = panel.size

    def dominant(box) -> tuple[int, int, int]:
        region = panel.crop(box).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
        pal = region.getpalette()
        counts = Counter(_pixels(region))
        for idx, _ in counts.most_common():
            rgb = tuple(pal[idx * 3: idx * 3 + 3])
            if not _near(rgb, INK, 90) and not _near(rgb, PAPER, 60):
                return rgb
        return (0, 0, 0)

    sky = dominant((int(pw * 0.1), 0, int(pw * 0.9), int(ph * 0.18)))
    ground = dominant((int(pw * 0.1), int(ph * 0.80), int(pw * 0.9), ph))
    seam = dominant((int(pw * 0.1), int(ph * 0.42), int(pw * 0.9), int(ph * 0.58)))

    q = panel.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = Counter(_pixels(q))
    motif: list[str] = []
    for idx, _ in counts.most_common():
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        if _near(rgb, PAPER, 60):
            continue
        if any(_near(rgb, c, 40) for c in (sky, ground, seam)):
            continue
        h = _hex(rgb)
        if h not in motif:
            motif.append(h)
        if len(motif) == 5:
            break
    return Palette(sky=_hex(sky), ground=_hex(ground), seam=_hex(seam), motif=motif)


# ------------------------------------------------------------- extraction

def _encode(path: Path, longest: int = 1100) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((longest, longest))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in model output: {text[:200]!r}")
    return json.loads(text[start: end + 1])


def extract(number: int, lang: str, meter: Meter) -> dict:
    """One Extractor call: the card's faces in one language -> structured fields."""
    src = sources_for(number, lang)
    images = [p for p in (src["front"], src["back"]) if p]
    if not src["back"] and src["social"]:
        images = [p for p in (src["front"], src["social"]) if p]
    if not images:
        raise FileNotFoundError(f"no source images for card {number} ({lang})")

    slug, es_name, en_name, _ = CATALOG[number]
    content = [{
        "type": "input_text",
        "text": (
            f"Card number {number}. Language: {'Spanish' if lang == 'es' else 'English'}. "
            f"The card name is '{es_name}'. Transcribe verbatim."
        ),
    }]
    for p in images:
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{_encode(p)}",
        })

    cl = client()
    last_error = None
    for attempt in range(2):
        resp = cl.responses.create(
            model=MODEL,
            instructions=prompt("extractor"),
            input=[{"role": "user", "content": content}],
        )
        meter.record(f"extractor:{lang}", Usage.from_response(MODEL, resp.usage))
        try:
            data = _parse_json(resp.output_text)
            data["_sources"] = [str(p.relative_to(ASSETS)) for p in images]
            return data
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(f"card {number} ({lang}) did not return JSON: {last_error}")


# ------------------------------------------------------------------ verify

def apply_corrections(card: Card) -> dict | None:
    """Apply a reviewed human correction for a card the Verifier flagged.

    The gate is allowed to be wrong about a card, but it is never allowed to be
    silently overridden: every correction names a reviewer, a reason and the
    source image, and is stamped into the card's notes.
    """
    path = DATA / "corrections.json"
    if not path.is_file():
        return None
    entry = json.loads(path.read_text(encoding="utf-8")).get(card.id)
    if not entry:
        return None
    for dotted, value in entry["fields"].items():
        field, _, lang = dotted.partition(".")
        target = getattr(card, field)
        if lang:
            setattr(target, lang, value)
        else:
            setattr(card, field, value)
    return {"reviewed_by": entry["reviewed_by"], "reason": entry["reason"],
            "fields": list(entry["fields"])}


def verify(card: Card) -> list[str]:
    """Deterministic gate. Flags anything a human should look at."""
    problems: list[str] = []
    for field in ("myth", "truth_headline", "body"):
        pair: Bilingual = getattr(card, field)
        for lang in ("en", "es"):
            if not pair.get(lang).strip():
                problems.append(f"{field}.{lang} is empty")
    # Cross-language length ratios catch truncation: if one language dropped a
    # sentence the pair stops being proportionate. Spanish runs ~20% longer
    # than English, so the window is deliberately asymmetric.
    for field, lo, hi in (("body", 0.75, 1.75), ("myth", 0.70, 1.80),
                          ("truth_headline", 0.65, 1.90)):
        pair: Bilingual = getattr(card, field)
        en_len, es_len = len(pair.en), len(pair.es)
        if en_len and es_len and not lo <= es_len / en_len <= hi:
            problems.append(
                f"{field} length ratio {es_len / en_len:.2f} outside [{lo}, {hi}] "
                f"(en={en_len} es={es_len}) - possible truncation"
            )
    if card.myth.en and card.myth.en.strip().lower() == card.body.en.strip().lower():
        problems.append("myth and body are identical (en)")
    return problems


# -------------------------------------------------------------------- run

def build(numbers: list[int]) -> tuple[list[Card], dict]:
    meter = Meter()
    cards: list[Card] = []
    style: dict = {"measured_from": [], "palettes": {}}

    for n in numbers:
        slug, es_name, en_name, category = CATALOG[n]
        print(f"  [{n:>2}] {es_name:<22}", end="", flush=True)
        en = extract(n, "en", meter)
        es = extract(n, "es", meter)

        front = sources_for(n, "en")["front"]
        palette = measure_palette(front) if front else Palette()

        card = Card(
            id=f"{n:02d}",
            number=n,
            slug=slug,
            name=Bilingual(en=en_name, es=es_name),
            category=category,
            motif=(en.get("motif") or es.get("motif") or "").strip(),
            palette=palette,
            myth=Bilingual(en=en.get("myth", "").strip(), es=es.get("myth", "").strip()),
            truth_headline=Bilingual(
                en=en.get("truth_headline", "").strip(),
                es=es.get("truth_headline", "").strip(),
            ),
            body=Bilingual(en=en.get("body", "").strip(), es=es.get("body", "").strip()),
            action=Bilingual(en=en.get("action", "").strip(), es=es.get("action", "").strip()),
            provenance="original",
            status="approved",
            created_by="genesis:extractor+measured-palette",
            approved_by="original campaign",
            notes="Created by Juan Pablo Alvarado as Program Manager at GreenLatinos, "
                  "in partnership with Intersectional Environmentalist.",
        )
        applied = apply_corrections(card)
        problems = verify(card)
        if applied:
            card.notes += (f" | CORRECTED by {applied['reviewed_by']}: "
                           f"{', '.join(applied['fields'])} -- {applied['reason']}")
        if problems:
            card.status = "needs_human"
            card.notes += " | VERIFY: " + "; ".join(problems)
        print(f" {'OK ' if not problems else 'FLAG'} "
              f"myth={len(card.myth.en):>3}/{len(card.myth.es):>3}  "
              f"body={len(card.body.en):>4}/{len(card.body.es):>4}"
              + (f"  <- {problems[0]}" if problems else ""))
        cards.append(card)
        style["palettes"][card.id] = palette.model_dump()
        style["measured_from"].extend(en.get("_sources", []))

    style["generated_at"] = now()
    style["usage"] = meter.report()
    return cards, style


STYLE_RULES = {
    "paper": "#EDEDE8",
    "ink": "#2E2520",
    "panel_ratio": 0.82,
    "rules": [
        "Cream paper ground with visible paper tooth; riso-style grain over the whole card.",
        "Art panel bordered by a heavy dark-brown rule; card number top-left inside the panel.",
        "Background inside the panel is a two-zone gradient with a soft blended horizon seam.",
        "Motif is flat fill only: one uniform thick outline, no shading, no gradients, no text.",
        "Card name in heavy condensed uppercase at the foot of the panel.",
        "Footer outside the panel: LEARN MORE / greenlatinos.org and CONNECT WITH US / @greenlatinos.",
        "Generated cards must NOT carry the GreenLatinos wordmark.",
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the seed deck from the 12 originals.")
    ap.add_argument("--cards", nargs="*", type=int, default=sorted(CATALOG))
    args = ap.parse_args()

    print(f"Genesis: extracting {len(args.cards)} card(s) with {MODEL}\n")
    cards, style = build(args.cards)

    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "cards.json"
    existing = {}
    if out.is_file():
        existing = {c["id"]: c for c in json.loads(out.read_text(encoding="utf-8"))}
    for c in cards:
        existing[c.id] = c.model_dump()
    payload = [existing[k] for k in sorted(existing)]
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    style["rules"] = STYLE_RULES
    (DATA / "style_profile.json").write_text(
        json.dumps(style, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    rep = style["usage"]
    flagged = [c.id for c in cards if c.status == "needs_human"]
    print(f"\nwrote {out.relative_to(DATA.parent)}  ({len(payload)} cards in deck)")
    print(f"wrote data/style_profile.json")
    print(f"cost: ${rep['total_usd']:.4f} over {rep['calls']} calls")
    if flagged:
        print(f"needs review: {', '.join(flagged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
