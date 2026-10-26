"""Export the deck as a slide deck.

One slide per card: the front, the myth/truth face, and the text you would see
if you clicked the card on the site. Opens with the story so the deck can be
handed to somebody cold -- a teacher, an organiser, a relative.

Card faces are rasterised from the same SVG the site renders, through headless
Chromium, so the printed deck and the web deck cannot drift apart.

    python export_deck.py                 # everything
    python export_deck.py --cards 01 13   # a couple, for a quick look
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render
from config import ASSETS, OUTPUT, REPO
from models import Card

RASTER = OUTPUT / "cards_png"
W, H = Inches(13.333), Inches(7.5)          # 16:9
PAPER = RGBColor(0xED, 0xED, 0xE8)
INK = RGBColor(0x2E, 0x25, 0x20)
SOFT = RGBColor(0x5C, 0x50, 0x47)
GREEN = RGBColor(0x2E, 0x6B, 0x3F)
ORANGE = RGBColor(0xF0, 0x4E, 0x23)

DISPLAY = "Archivo Black"
LANG_UI = {
    "es": {"myth": "MITO", "truth": "VERDAD", "do": "QUÉ PUEDES HACER",
           "sources": "FUENTES", "original": "Carta original · GreenLatinos / Intersectional Environmentalist",
           "generated": "Carta generada · marco: {f}",
           "sub": "El mito, la verdad, y qué hacer.",
           "valley": "EL VALLE", "table": "LA MESA"},
    "en": {"myth": "MYTH", "truth": "TRUTH", "do": "WHAT YOU CAN DO",
           "sources": "SOURCES", "original": "Original card · GreenLatinos / Intersectional Environmentalist",
           "generated": "Generated card · frame: {f}",
           "sub": "The myth, the truth, and what to do.",
           "valley": "THE VALLEY", "table": "THE TABLE"},
}
BODY = "Jost"


VALLEY = {
    "es": ("Soy del sur de Texas, del Río Grande Valley. Allá el clima no es un tema de "
           "debate: es el aire acondicionado que no alcanza, el recibo de la luz en agosto, "
           "la tormenta que inunda la calle de siempre, el tío que trabaja afuera todo el día."),
    "en": ("I'm from South Texas — the Rio Grande Valley. Climate there is not a debate "
           "topic. It's the AC that can't keep up, the August electric bill, the storm that "
           "floods the same street every time, the tío who works outside all day."),
}
VALLEY2 = {
    "es": ("También es donde aprendí que la información que de verdad te mueve no llega en "
           "un reporte. Llega de tu mamá, de tu comadre, del grupo de WhatsApp de la familia."),
    "en": ("It's also where I learned that the information that actually moves you doesn't "
           "arrive in a report. It arrives from your mom, your comadre, the family WhatsApp group."),
}
TABLE = {
    "es": [("Crecí jugando lotería con mis abuelitos. Alguien canta las cartas, los demás "
            "marcan con frijolitos, y entre carta y carta se habla de todo. El juego nunca "
            "fue nada más el juego: era la excusa para estar en la misma mesa."),
           ("Como Program Manager en GreenLatinos, y junto con Intersectional Environmentalist, "
            "creé las primeras "
            "doce cartas de la Lotería Climática. En 2025, GreenLatinos y Resource Media "
            "probaron ese mensaje con 1,797 adultos latinos: la salud, la familia y la fe "
            "mueven a la gente; señalar villanos genéricos no. Ese dato enmarca cada carta nueva."),
           ("Doce cartas se hacen en meses; la desinformación cambia en días. Por eso esto no "
            "es un folleto, es una fábrica: la gente pregunta, el sistema escucha lo que "
            "ninguna carta contesta, y fabrica la que falta.")],
    "en": [("I grew up playing lotería with my abuelitos. Somebody calls the cards, everyone "
            "else marks with beans, and between cards you talk about everything. The game was "
            "never just the game: it was the excuse to be at the same table."),
           ("As Program Manager at GreenLatinos, alongside Intersectional Environmentalist, I "
            "created the first "
            "twelve Climate Lotería cards. In 2025, GreenLatinos and Resource Media tested "
            "that messaging with 1,797 Latino adults: health, family and faith move people; "
            "naming generic villains does not. That data frames every new card."),
           ("Twelve cards take months to make; disinformation changes in days. So this is not "
            "a pamphlet, it is a factory: people ask, the system notices what no card answers, "
            "and it manufactures the missing one.")],
}



def _shot(page, svg: str, dst: Path, reuse: bool = True) -> Path:
    """Screenshot one card face.

    The SVG is wrapped in a fixed-size page and captured as a viewport
    screenshot rather than by locating the <svg> element. Playwright's
    element screenshot waits for the node to be "stable", and the riso grain
    filter keeps some cards repainting, so that wait could time out after
    twenty-odd cards. A fixed viewport has nothing to wait for.
    """
    if reuse and dst.is_file() and dst.stat().st_size > 10_000:
        return dst          # already rendered; a re-run resumes rather than restarts
    page.set_viewport_size({"width": 800, "height": 1200})
    page.set_content(
        '<!doctype html><style>html,body{margin:0;padding:0;overflow:hidden}'
        'svg{display:block;width:800px;height:1200px}</style>' + svg,
        wait_until="load",
    )
    page.screenshot(path=str(RASTER / "_tmp.png"), animations="disabled")
    return _compress(RASTER / "_tmp.png", dst)


# ----------------------------------------------------------------- raster

def _compress(src: Path, dst: Path, width: int = 900) -> Path:
    """A 54-card PPTX of full-resolution PNGs is a few hundred MB. JPEG at
    900px is indistinguishable on a projector and ships in single digits."""
    im = Image.open(src).convert("RGB")
    im.thumbnail((width, width * 3))
    im.save(dst, "JPEG", quality=85, optimize=True)
    src.unlink(missing_ok=True)
    return dst



def rasterise(deck: list[Card], only: set[str] | None, lang: str) -> dict[str, dict[str, Path]]:
    """Render every card face to PNG with the same engine the browser uses."""
    RASTER.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict[str, Path]] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 1200},
                                device_scale_factor=1.5)
        done = 0
        for card in deck:
            if only and card.id not in only:
                continue
            faces: dict[str, Path] = {}

            front_art = render.original_front(card)
            if front_art:
                faces["front"] = REPO / front_art
            else:
                svg = render.render(card, "front", "es")
                faces["front"] = _shot(page, svg, RASTER / f"{card.id}-front.jpg")

            svg = render.render(card, "back", lang)
            faces["back"] = _shot(page, svg, RASTER / f"{card.id}-back-{lang}.jpg")

            out[card.id] = faces
            done += 1
            print(f"  {card.id} {card.name.es:<24} rasterised", flush=True)
            if done % 18 == 0:          # recycle before memory becomes the problem
                page.close(); browser.close()
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 800, "height": 1200},
                                        device_scale_factor=1.5)
        browser.close()
    return out


# ------------------------------------------------------------------ slides

def _bg(slide, colour=PAPER):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = colour


def _text(slide, left, top, width, height, runs, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for text, size, bold, colour, font, space in runs:
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        para.alignment = align
        para.space_after = Pt(space)
        run = para.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = colour
        run.font.name = font
    return box


def story_slides(prs: Presentation, lang: str) -> None:
    blank = prs.slide_layouts[6]

    s = prs.slides.add_slide(blank); _bg(s)
    _text(s, Inches(1), Inches(2.3), Inches(11.3), Inches(3), [
        ("LOTERÍA CLIMÁTICA", 60, True, INK, DISPLAY, 10),
        (LANG_UI[lang]["sub"], 22, False, SOFT, BODY, 0),
    ])

    s = prs.slides.add_slide(blank); _bg(s)
    photo = ASSETS / "web" / "juan-pablo.jpg"
    if photo.is_file():
        s.shapes.add_picture(str(photo), Inches(0.9), Inches(1.6), height=Inches(4.2))
    _text(s, Inches(5.6), Inches(1.5), Inches(7), Inches(5), [
        (LANG_UI[lang]["valley"], 34, True, INK, DISPLAY, 10),
        (VALLEY[lang], 16, False, INK, BODY, 8),
        (VALLEY2[lang], 16, False, INK, BODY, 0),
    ])

    s = prs.slides.add_slide(blank); _bg(s)
    _text(s, Inches(1), Inches(1.3), Inches(11.3), Inches(5), [
        (LANG_UI[lang]["table"], 34, True, INK, DISPLAY, 10),
    ] + [(para, 17, False, INK, BODY, 10) for para in TABLE[lang]])


def card_slide(prs: Presentation, card: Card, faces: dict[str, Path], lang: str) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)

    card_h = Inches(5.6)
    s.shapes.add_picture(str(faces["front"]), Inches(0.55), Inches(0.95), height=card_h)
    s.shapes.add_picture(str(faces["back"]), Inches(4.35), Inches(0.95), height=card_h)

    _text(s, Inches(0.55), Inches(0.3), Inches(7), Inches(0.6), [
        (f"{card.id} · {card.name.es}", 24, True, INK, DISPLAY, 0),
    ])

    ui = LANG_UI[lang]
    pick = lambda b: (b.es or b.en) if lang == "es" else (b.en or b.es)
    runs = [
        (ui["myth"], 11, True, ORANGE, BODY, 2),
        (pick(card.myth), 13, False, SOFT, BODY, 10),
        (ui["truth"], 11, True, GREEN, BODY, 2),
        (pick(card.truth_headline), 19, True, INK, DISPLAY, 8),
        (pick(card.body), 12, False, INK, BODY, 8),
    ]
    action = pick(card.action)
    if action:
        runs += [(ui["do"], 11, True, GREEN, BODY, 2),
                 (action, 12, False, INK, BODY, 8)]
    if card.evidence:
        srcs = ", ".join(dict.fromkeys(e.source_name for e in card.evidence))[:180]
        runs += [(ui["sources"], 10, True, SOFT, BODY, 2),
                 (srcs, 9, False, SOFT, BODY, 0)]
    _text(s, Inches(8.25), Inches(0.95), Inches(4.6), Inches(5.8), runs)

    tag = (ui["original"] if card.provenance == "original"
           else ui["generated"].format(f=card.frame.frame if card.frame else "—"))
    _text(s, Inches(0.55), Inches(6.75), Inches(12.2), Inches(0.4),
          [(tag, 9, False, SOFT, BODY, 0)])



# -------------------------------------------------------------------- pdf

def write_pdf(deck: list[Card], faces: dict, lang: str, out: Path) -> None:
    """A PDF of the same slides.

    Rendered through Chromium rather than converted from the PPTX, because
    there is no Office or LibreOffice to convert with -- and this way the PDF
    and the site share one set of fonts and colours.
    """
    import base64

    ui = LANG_UI[lang]
    pick = lambda b: (b.es or b.en) if lang == "es" else (b.en or b.es)

    def b64(path: Path) -> str:
        return ("data:image/jpeg;base64,"
                + base64.b64encode(Path(path).read_bytes()).decode())

    slides = [f'''<section class="s title">
        <h1>LOTERÍA CLIMÁTICA</h1><p class="sub">{ui["sub"]}</p></section>''']

    photo = ASSETS / "web" / "event" / "jp-speaking.jpg"
    if photo.is_file():
        slides.append(f'''<section class="s two">
          <img class="photo" src="{b64(photo)}">
          <div><h2>{ui["valley"]}</h2><p>{VALLEY[lang]}</p><p>{VALLEY2[lang]}</p></div>
        </section>''')

    paras = "".join(f"<p>{t}</p>" for t in TABLE[lang])
    slides.append(f'<section class="s"><h2>{ui["table"]}</h2>{paras}</section>')

    for card in deck:
        f = faces.get(card.id)
        if not f:
            continue
        action = pick(card.action)
        srcs = ", ".join(dict.fromkeys(e.source_name for e in card.evidence))[:180]
        tag = (ui["original"] if card.provenance == "original"
               else ui["generated"].format(f=card.frame.frame if card.frame else "—"))
        slides.append(f'''<section class="s card">
          <h3>{card.id} · {card.name.es}</h3>
          <div class="row">
            <img src="{b64(f["front"])}"><img src="{b64(f["back"])}">
            <div class="txt">
              <p class="k myth">{ui["myth"]}</p><p class="m">{pick(card.myth)}</p>
              <p class="k">{ui["truth"]}</p><p class="t">{pick(card.truth_headline)}</p>
              <p class="b">{pick(card.body)}</p>
              {f'<p class="k">{ui["do"]}</p><p class="b">{action}</p>' if action else ""}
              {f'<p class="k">{ui["sources"]}</p><p class="src">{srcs}</p>' if srcs else ""}
            </div>
          </div>
          <p class="foot">{tag}</p>
        </section>''')

    html = f'''<!doctype html><meta charset="utf-8">
    <style>
      @page {{ size: 13.333in 7.5in; margin: 0; }}
      * {{ box-sizing: border-box; }}
      body {{ margin:0; font-family: Jost, Archivo, system-ui, sans-serif; color:#2e2520; }}
      .s {{ width:13.333in; height:7.5in; padding:.5in .6in; background:#edede8;
            break-after:page; page-break-after:always; overflow:hidden; }}
      .s:last-child {{ break-after:auto; page-break-after:auto; }}
      h1 {{ font-size:62pt; margin:0; letter-spacing:-.01em; }}
      .title {{ display:flex; flex-direction:column; justify-content:center; }}
      .sub {{ font-size:20pt; color:#5c5047; }}
      h2 {{ font-size:30pt; margin:0 0 .18in; }}
      h3 {{ font-size:20pt; margin:0 0 .12in; }}
      .two {{ display:grid; grid-template-columns:4in 1fr; gap:.5in; align-items:center; }}
      .photo {{ width:100%; border-radius:.14in; }}
      p {{ font-size:13pt; line-height:1.45; margin:0 0 .13in; }}
      .row {{ display:grid; grid-template-columns:2.6in 2.6in 1fr; gap:.3in; }}
      .row img {{ width:100%; border-radius:.1in; align-self:start; }}
      .txt p {{ font-size:11pt; margin:0 0 .09in; }}
      .k {{ font-size:8pt; letter-spacing:.1em; font-weight:600; color:#2e6b3f; margin-bottom:.03in; }}
      .k.myth {{ color:#f04e23; }}
      .m {{ color:#5c5047; }}
      .t {{ font-family: Archivo, sans-serif; font-weight:800; font-size:16pt; line-height:1.15; }}
      .src {{ font-size:8.5pt; color:#5c5047; }}
      .foot {{ position:absolute; font-size:8pt; color:#5c5047; margin-top:.12in; }}
    </style>{"".join(slides)}'''

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.set_content(html, wait_until="load")
        pg.pdf(path=str(out), width="13.333in", height="7.5in",
               print_background=True, margin={"top":"0","bottom":"0","left":"0","right":"0"})
        b.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", nargs="*", default=None)
    ap.add_argument("--lang", choices=["es", "en", "both"], default="both")
    ap.add_argument("--pdf", action="store_true", default=True,
                    help="also write a PDF of the slides (default on)")
    args = ap.parse_args()

    deck = render.load_deck()
    only = set(args.cards) if args.cards else None
    langs = ["es", "en"] if args.lang == "both" else [args.lang]

    for lang in langs:
        print(f"\n=== {lang.upper()} — rasterising "
              f"{len(only) if only else len(deck)} card(s)…")
        faces = rasterise(deck, only, lang)

        prs = Presentation()
        prs.slide_width, prs.slide_height = Emu(int(W)), Emu(int(H))
        story_slides(prs, lang)
        for card in deck:
            if card.id in faces:
                card_slide(prs, card, faces[card.id], lang)

        OUTPUT.mkdir(parents=True, exist_ok=True)
        pptx_path = OUTPUT / f"loteria-climatica-{lang}.pptx"
        prs.save(pptx_path)
        print(f"  wrote {pptx_path.name}  ({len(prs.slides._sldIdLst)} slides, "
              f"{pptx_path.stat().st_size // 1024} KB)")

        pdf_path = OUTPUT / f"loteria-climatica-{lang}.pdf"
        write_pdf(deck, faces, lang, pdf_path)
        print(f"  wrote {pdf_path.name}  ({pdf_path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
