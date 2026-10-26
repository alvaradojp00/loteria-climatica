import { useEffect, useState } from "react";
import { api, type CardSummary } from "../api";
import { category, t, type Lang } from "../i18n";

export function artSrc(c: { art: string | null; id: string }): string {
  return c.art ? `${api.base}/${c.art}` : api.cardSvg(c.id, "front", "es");
}

export function CardModal({ id, lang, onClose }: { id: string; lang: Lang; onClose: () => void }) {
  const [card, setCard] = useState<any>(null);
  const [face, setFace] = useState<"front" | "back">("front");

  useEffect(() => { setFace("front"); api.card(id).then(setCard).catch(() => setCard(null)); }, [id]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [onClose]);

  if (!card) return null;
  const txt = (k: string) => card[k]?.[lang] || card[k]?.en || "";
  const frontSrc = card.art ? `${api.base}/${card.art}` : api.cardSvg(card.id, "front", "es");
  const backSrc = api.cardSvg(card.id, "back", lang);

  return (
    <div className="modal-bg" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label={t("close", lang)}>✕</button>
        <div className="modal-grid">
          <figure className="card-stage">
            <div className="card-faces">
              {face === "front"
                ? (card.art
                    ? <img src={frontSrc} alt={card.name.es} />
                    : <object data={frontSrc} type="image/svg+xml" aria-label={card.name.es} />)
                : <object data={backSrc} type="image/svg+xml" aria-label={txt("truth_headline")} />}
            </div>
            <div className="face-switch">
              <button aria-pressed={face === "front"} onClick={() => setFace("front")}>
                {lang === "es" ? "Frente" : "Front"}
              </button>
              <button aria-pressed={face === "back"} onClick={() => setFace("back")}>
                {lang === "es" ? "Mito y verdad" : "Myth & truth"}
              </button>
            </div>
            <a className="dl" href={face === "front" ? frontSrc : backSrc} download>
              ↓ {t("download_card", lang)}
            </a>
          </figure>

          <div className="modal-body">
            <p className="kv">{t("card", lang)} {card.id} · {category(card.category, lang)}</p>
            <h2>{card.name.es}</h2>
            {lang === "en" && <p className="kv" style={{ marginTop: "-.6rem" }}>{card.name.en}</p>}

            <p className="kv">{t("myth", lang)}</p>
            <p className="myth">{txt("myth")}</p>

            <p className="kv">{t("truth", lang)}</p>
            <p className="truth">{txt("truth_headline")}</p>
            <p>{txt("body")}</p>

            {txt("action") && (<>
              <p className="kv">{t("action", lang)}</p>
              <p>{txt("action")}</p>
            </>)}

            {card.evidence?.length > 0 && (
              <details open>
                <summary>{t("evidence", lang)} ({card.evidence.length})</summary>
                <ul>{card.evidence.map((e: any, i: number) => (
                  <li key={i}>
                    <a href={e.url} target="_blank" rel="noreferrer">{e.source_name}</a>
                    {e.claim ? ` — ${e.claim}` : ""}
                  </li>
                ))}</ul>
              </details>
            )}

            <p className="source-note" style={{ marginTop: "1.2rem" }}>
              {card.provenance === "original" ? t("original_note", lang) : t("generated_note", lang)}
              {card.status === "needs_human" && <> · <b>{t("pending", lang)}</b></>}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Deck({ lang, focus, onFocus, onPlay, onAsk }: {
  lang: Lang; focus: string | null; onFocus: (id: string | null) => void;
  onPlay: () => void; onAsk: () => void;
}) {
  const [cards, setCards] = useState<CardSummary[]>([]);
  const [cats, setCats] = useState<string[]>([]);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    api.deck(filter ?? undefined)
      .then((d) => { setCards(d.cards); if (!filter) setCats(d.categories); })
      .catch(() => setCards([]));
  }, [filter]);

  return (
    <section>
      <div className="hero-split">
        <div>
          <h1>{lang === "es"
            ? <>Lotería <b>Climática</b></>
            : <>Climate <b>Lotería</b></>}</h1>
          <p className="lede">{t("deck_lede", lang)}</p>
          <div className="hero-cta">
            <button className="primary" onClick={onPlay}>{t("nav_jugar", lang)}</button>
            <button onClick={onAsk}>{t("nav_ayuda", lang)}</button>
          </div>
        </div>
        <div className="fan" aria-hidden="true">
          {cards.slice(0, 5).map((c) => (
            c.art
              ? <img key={c.id} src={artSrc(c)} alt="" loading="lazy" />
              : <object key={c.id} data={artSrc(c)} type="image/svg+xml" />
          ))}
        </div>
      </div>

      <div className="filters">
        <button aria-pressed={filter === null} onClick={() => setFilter(null)}>
          {t("all", lang)}
        </button>
        {cats.map((c) => (
          <button key={c} aria-pressed={filter === c} onClick={() => setFilter(c)}>
            {category(c, lang)}
          </button>
        ))}
      </div>

      <div className="deck-grid">
        {cards.map((c) => (
          <button key={c.id} className="card-tile" onClick={() => onFocus(c.id)}>
            {c.art
              ? <img src={artSrc(c)} alt="" loading="lazy" />
              : <object data={artSrc(c)} type="image/svg+xml" aria-hidden="true" />}
            <div className="card-meta">
              <strong>{c.name.es}</strong>
              <small>{c.number} · {category(c.category, lang)}</small>
            </div>
          </button>
        ))}
      </div>

      {focus && <CardModal id={focus} lang={lang} onClose={() => onFocus(null)} />}
    </section>
  );
}
