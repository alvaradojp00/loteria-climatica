import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { type Lang } from "../i18n";
import { Ajolota } from "./Ajolota";

/** El Gritón — the caller.
 *
 *  In lotería somebody calls the cards aloud while everyone marks their
 *  board. Here Ajolota does the calling, and each card comes with a line to
 *  read out: the myth, the truth, and a question for the table. That question
 *  is the whole point of the project — the game is the excuse for the
 *  conversation, so the caller has to hand people something to say.
 *
 *  The talking points are assembled from the card's own fields rather than
 *  generated, so calling a game costs nothing and works offline.
 */

interface CallerCard {
  id: string;
  name: { es: string; en: string };
  myth: { es: string; en: string };
  truth_headline: { es: string; en: string };
  art: string | null;
}

const PROMPTS: Record<Lang, string[]> = {
  es: [
    "¿Quién ha oído esta en el chat de la familia?",
    "¿A quién se la han mandado?",
    "¿Esta se parece a algo que dice alguien que conoces?",
    "¿Quién se la creyó alguna vez? Yo también, no pasa nada.",
    "¿Dónde la han visto: Facebook, WhatsApp, TikTok?",
    "Si te llega hoy, ¿qué le contestarías?",
  ],
  en: [
    "Who's heard this one in the family chat?",
    "Who's had this forwarded to them?",
    "Does this sound like somebody you know?",
    "Who believed it once? Me too — that's the point.",
    "Where have you seen it: Facebook, WhatsApp, TikTok?",
    "If it reached you today, what would you say back?",
  ],
};

export function Caller({ lang, onClose }: { lang: Lang; onClose: () => void }) {
  const [deck, setDeck] = useState<CallerCard[]>([]);
  const [order, setOrder] = useState<string[]>([]);
  const [at, setAt] = useState(0);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    api.tablas(1).then(async (t: any) => {
      const ids: string[] = t.call_order;
      const cards = await Promise.all(ids.slice(0, 54).map((id) => api.card(id)));
      setDeck(cards);
      setOrder(ids);
    });
  }, []);

  const card = useMemo(
    () => deck.find((c) => c.id === order[at]),
    [deck, order, at],
  );
  const prompt = PROMPTS[lang][at % PROMPTS[lang].length];

  useEffect(() => { setRevealed(false); }, [at]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        revealed ? setAt((n) => Math.min(n + 1, order.length - 1)) : setRevealed(true);
      }
      if (e.key === "ArrowLeft") setAt((n) => Math.max(0, n - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, order.length, revealed]);

  if (!card) {
    return (
      <div className="caller">
        <p className="dots"><span /><span /><span /></p>
      </div>
    );
  }

  const art = card.art ? `${api.base}/${card.art}` : api.cardSvg(card.id, "front", "es");
  const last = at === order.length - 1;

  return (
    <div className="caller">
      <div className="caller-bar">
        <span className="kv">
          {lang === "es" ? "Carta" : "Card"} {at + 1} / {order.length}
        </span>
        <div className="caller-progress"><i style={{ width: `${((at + 1) / order.length) * 100}%` }} /></div>
        <button onClick={onClose}>{lang === "es" ? "Salir" : "Exit"}</button>
      </div>

      <div className="caller-stage">
        <figure className="caller-card">
          <img src={art} alt={card.name.es} />
        </figure>

        <div className="caller-script">
          <Ajolota size={92} pose={revealed ? "excited" : "waving"} />
          <p className="caller-name">
            {lang === "es" ? "¡" : ""}{card.name.es}{lang === "es" ? "!" : "!"}
          </p>

          {!revealed ? (
            <>
              <p className="caller-hint">
                {lang === "es"
                  ? "Que todos la marquen. Cuando estén listos, lee lo que trae atrás."
                  : "Let everyone mark it. When they're ready, read what's on the back."}
              </p>
              <button className="primary big" onClick={() => setRevealed(true)}>
                {lang === "es" ? "Leer el mito y la verdad" : "Read the myth and the truth"}
              </button>
            </>
          ) : (
            <>
              <p className="kv">{lang === "es" ? "El mito" : "The myth"}</p>
              <p className="caller-myth">{card.myth[lang] || card.myth.en}</p>
              <p className="kv">{lang === "es" ? "La verdad" : "The truth"}</p>
              <p className="caller-truth">{card.truth_headline[lang] || card.truth_headline.en}</p>
              <p className="caller-prompt">{prompt}</p>
            </>
          )}

          <div className="caller-nav">
            <button disabled={at === 0} onClick={() => setAt((n) => n - 1)}>←</button>
            <button className="primary" disabled={last}
                    onClick={() => setAt((n) => n + 1)}>
              {last
                ? (lang === "es" ? "Fin del mazo" : "End of deck")
                : (lang === "es" ? "Siguiente carta →" : "Next card →")}
            </button>
          </div>
          <p className="source-note">
            {lang === "es"
              ? "Espacio o → avanza · ← regresa · Esc sale"
              : "Space or → advances · ← goes back · Esc exits"}
          </p>
        </div>
      </div>
    </div>
  );
}
