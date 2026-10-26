import { useEffect, useState } from "react";
import { api } from "../api";
import { t, type Lang } from "../i18n";
import { Caller } from "./Caller";
import { Ajolota } from "./Ajolota";

interface Tablas {
  seed: number;
  boards: { n: number; cards: string[]; grid: string[][] }[];
  names: Record<string, { es: string; en: string }>;
  art: Record<string, string | null>;
  call_order: string[];
}

function src(id: string, art: Record<string, string | null>) {
  const a = art[id];
  return a ? `${api.base}/${a}` : api.cardSvg(id, "front", "es");
}

export function Jugar({ lang }: { lang: Lang }) {
  const [data, setData] = useState<Tablas | null>(null);
  const [busy, setBusy] = useState(false);
  const [picker, setPicker] = useState(false);
  const [calling, setCalling] = useState(false);

  async function load(seed?: number) {
    setBusy(true);
    try { setData(await api.tablas(6, seed)); }
    finally { setBusy(false); }
  }
  useEffect(() => { load(); }, []);

  function printBoards() {
    if (!data) return;
    const grid = (b: Tablas["boards"][0]) => `
      <section class="tabla">
        <div class="head">
          <h2>${lang === "es" ? "Tabla" : "Board"} ${b.n}</h2>
          <span class="seed">Lotería Climática · #${data.seed}</span>
        </div>
        <div class="g">${b.cards.map((id) => `
          <figure>
            <img src="${src(id, data.art)}" alt="">
            <figcaption>${data.names[id]?.es ?? id}</figcaption>
          </figure>`).join("")}</div>
      </section>`;

    // Every dimension is fixed in millimetres. The earlier version used
    // aspect-ratio inside 1fr columns, so each card grew to the column width
    // and a board spilled onto a second sheet. 4 rows x 56mm + gaps + header
    // comes to 250mm, inside Letter's 259mm of usable height.
    const html = `<!doctype html><meta charset="utf-8">
      <title>Lotería Climática — ${lang === "es" ? "tablas" : "boards"}</title>
      <style>
        @page { size: letter portrait; margin: 10mm; }
        html, body { margin:0; padding:0; }
        body { font-family: Archivo, system-ui, sans-serif; color:#2e2520; background:#fff; }
        .tabla { break-after: page; page-break-after: always; }
        .tabla:last-child { break-after: auto; page-break-after: auto; }
        .head { display:flex; align-items:baseline; justify-content:space-between;
                height:12mm; }
        h2 { font-size:18pt; margin:0; letter-spacing:.02em; text-transform:uppercase; }
        .seed { font-size:9pt; opacity:.45; }
        .g { display:grid; grid-template-columns:repeat(4, 40mm);
             grid-auto-rows:56mm; gap:4mm; justify-content:center; }
        figure { margin:0; border:1.6pt solid #2e2520; border-radius:2mm;
                 overflow:hidden; background:#fff; display:flex; flex-direction:column; }
        img { width:40mm; height:50mm; object-fit:cover; display:block; }
        figcaption { flex:1; font-size:6.5pt; line-height:1.1; text-align:center;
                     padding:1mm .5mm; font-weight:700; text-transform:uppercase;
                     display:flex; align-items:center; justify-content:center; }
        @media print { .tabla { break-inside: avoid; } }
      </style>
      ${data.boards.map(grid).join("")}`;

    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.onload = () => setTimeout(() => w.print(), 400);
  }

  function printDeck() {
    if (!data) return;
    const ids = Object.keys(data.names).sort();
    const html = `<!doctype html><meta charset="utf-8">
      <title>Lotería Climática — ${lang === "es" ? "mazo" : "deck"}</title>
      <style>
        @page { size: letter portrait; margin: 10mm; }
        html, body { margin:0; padding:0; }
        body { font-family: Archivo, system-ui, sans-serif; background:#fff; }
        .g { display:grid; grid-template-columns:repeat(3, 60mm);
             grid-auto-rows:88mm; gap:5mm; justify-content:center; }
        figure { margin:0; break-inside:avoid; page-break-inside:avoid;
                 border:1.6pt solid #2e2520; border-radius:2mm; overflow:hidden;
                 background:#fff; display:flex; flex-direction:column; }
        img { width:60mm; height:80mm; object-fit:cover; display:block; }
        figcaption { flex:1; font-size:7.5pt; text-align:center; font-weight:700;
                     text-transform:uppercase; display:flex; align-items:center;
                     justify-content:center; }
      </style>
      <div class="g">${ids.map((id) => `
        <figure><img src="${src(id, data.art)}" alt="">
        <figcaption>${id} · ${data.names[id]?.es ?? ""}</figcaption></figure>`).join("")}</div>`;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.onload = () => setTimeout(() => w.print(), 600);
  }

  return (
    <section>
      <div className="hero tight">
        <h1>{t("play_title", lang)}</h1>
        <p className="lede">{t("play_lede", lang)}</p>
      </div>

      <div className="caller-invite">
        <Ajolota size={92} pose="waving" />
        <div>
          <h2>{t("caller_title", lang)}</h2>
          <p>{t("caller_lede", lang)}</p>
          <button className="primary big" onClick={() => setCalling(true)}>
            {t("start_calling", lang)}
          </button>
        </div>
      </div>

      {calling && <Caller lang={lang} onClose={() => setCalling(false)} />}

      <div className="play-actions">
        <button className="primary" disabled={busy} onClick={() => load()}>
          {data ? t("new_boards", lang) : t("generate_boards", lang)}
        </button>
        <button disabled={!data} onClick={printBoards}>↓ {t("print_boards", lang)}</button>
        <button disabled={!data} onClick={printDeck}>↓ {t("print_deck", lang)}</button>
        <button onClick={() => setPicker(true)}>↓ {t("download_deck", lang)}</button>
      </div>
      {data && <p className="source-note">#{data.seed} · {t("seed_note", lang)}</p>}

      {picker && (
        <div className="modal-bg" onClick={() => setPicker(false)} role="dialog" aria-modal="true">
          <div className="picker" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setPicker(false)} aria-label="×">✕</button>
            <h3>{t("choose_language", lang)}</h3>
            <p className="source-note">{t("deck_blurb", lang)}</p>
            <div className="picker-grid">
              {(["es", "en"] as const).map((l) => (
                <div className="picker-col" key={l}>
                  <strong>{l === "es" ? t("in_spanish", lang) : t("in_english", lang)}</strong>
                  <a className="btn-link" href={api.deckUrl(l, "pdf")} download
                     onClick={() => setPicker(false)}>↓ {t("as_pdf", lang)}</a>
                  <a className="btn-link ghost" href={api.deckUrl(l, "pptx")} download
                     onClick={() => setPicker(false)}>↓ {t("as_pptx", lang)}</a>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="how">
        <h3>{t("how_to_play", lang)}</h3>
        <p>{t("how_to_play_body", lang)}</p>
      </div>

      {busy && <p className="dots"><span /><span /><span /></p>}

      {data && (
        <>
          <div className="tabla-grid">
            {data.boards.map((b) => (
              <div className="tabla-card" key={b.n}>
                <h3>{t("board", lang)} {b.n}</h3>
                <div className="tabla-16">
                  {b.cards.map((id) => (
                    <figure key={id}>
                      <img src={src(id, data.art)} alt="" loading="lazy" />
                      <figcaption>{data.names[id]?.es ?? id}</figcaption>
                    </figure>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <details className="call-order">
            <summary>{t("call_order", lang)} ({data.call_order.length})</summary>
            <ol>{data.call_order.map((id) => (
              <li key={id}>{data.names[id]?.es ?? id}</li>
            ))}</ol>
          </details>
        </>
      )}
    </section>
  );
}
