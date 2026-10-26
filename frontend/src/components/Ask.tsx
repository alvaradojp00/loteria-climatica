import { useRef, useState } from "react";
import { api } from "../api";
import { t, type Lang } from "../i18n";
import { Ajolota, AjolotaThinking } from "./Ajolota";

const EXAMPLE = `*URGENTE - COMPARTE CON TU FAMILIA* 🙏

Los paneles solares que están instalando en el barrio son peligrosos. Cuando hace frío dejan de funcionar y por eso se cayó la luz en Texas. Además las baterías explotan.

Pásalo a 10 personas`;

const SEEDS: Record<Lang, string[]> = {
  es: [
    "¿Es cierto que China contamina más y lo que hagamos aquí no cambia nada?",
    "Mi tío dice que el calor de ahora es igual que siempre",
    "¿Las turbinas de viento matan ballenas?",
  ],
  en: [
    "Is it true that renewables are what raised my electric bill?",
    "My uncle says today's heat is the same as it always was",
    "Do wind turbines kill whales?",
  ],
};

interface Turn {
  you: string;
  explanation?: string;
  sayThis?: string;
  oneMove?: string;
  cards?: string[];
  counter?: any;
  error?: string;
}

export function Ask({ lang, onCard }: { lang: Lang; onCard: (id: string) => void }) {
  const [log, setLog] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  async function send(message: string) {
    if (!message.trim() || busy) return;
    setText("");
    const idx = log.length;
    setLog((l) => [...l, { you: message }]);
    setBusy(true);
    try {
      const history = log.slice(-4).flatMap((turn) => ([
        { role: "user", content: turn.you },
        { role: "assistant", content: turn.explanation ?? "" },
      ]));
      const out = await api.ask(message, history);
      setLog((l) => l.map((turn, i) => i === idx ? {
        ...turn,
        explanation: out.explanation?.text,
        sayThis: out.explanation?.say_this,
        oneMove: out.explanation?.one_move,
        cards: out.explanation?.cards ?? [],
        counter: out.counter,
      } : turn));
    } catch (e: any) {
      setLog((l) => l.map((turn, i) => i === idx
        ? { ...turn, error: t("backend_down", lang) } : turn));
    } finally {
      setBusy(false);
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ behavior: "smooth" }));
    }
  }

  return (
    <section>
      <div className="hero tight">
        <h1>{t("ask_title", lang)}</h1>
        <p className="lede">{t("ask_lede", lang)}</p>
      </div>

      <div className="ask-shell">
        <div>
          {log.length === 0 && (
            <div className="bubble bot intro">
              <div className="she">
                <Ajolota size={104} pose="waving" />
                <p style={{ margin: 0 }}>
                  {lang === "es"
                    ? "Soy la Comadre Ajolota. ¿Qué te mandaron? Pégalo aquí y lo vemos juntas — y te doy algo que sí puedas decirle a tu gente."
                    : "I'm Comadre Ajolota. What did they send you? Paste it here and we'll look at it together — and I'll give you something you can actually say to your people."}
                </p>
              </div>
              <div className="cites">
                {SEEDS[lang].map((s) => (
                  <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
                ))}
                <button className="chip alt" onClick={() => setText(EXAMPLE)}>
                  {t("use_example", lang)}
                </button>
              </div>
            </div>
          )}

          {log.map((turn, i) => (
            <div key={i} className="turn">
              <div className="bubble user">{turn.you}</div>

              {turn.error && <div className="bubble bot err">{turn.error}</div>}

              {turn.explanation && (
                <div className="bubble bot">
                  <Ajolota size={46} pose="excited" className="avatar" />
                  {turn.explanation}
                  {turn.cards && turn.cards.length > 0 && (
                    <div className="cites">
                      {turn.cards.map((c) => (
                        <button key={c} className="chip" onClick={() => onCard(c)}>
                          {t("card", lang)} {c}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {turn.sayThis && (
                <div className="say-this">
                  <p className="kv">{t("say_this", lang)}</p>
                  <blockquote>{turn.sayThis}</blockquote>
                  <div className="say-actions">
                    <button onClick={() => {
                      navigator.clipboard.writeText(turn.sayThis ?? "");
                      setCopied(i);
                    }}>{copied === i ? t("copied", lang) : t("copy", lang)}</button>
                    {turn.oneMove && <p className="move">{turn.oneMove}</p>}
                  </div>
                </div>
              )}

              {turn.counter?.status === "ok" && (
                <div className="counter">
                  {turn.counter.packet?.embedded_instructions && (
                    <div className="warn">
                      <p className="kv">{t("safety_notice", lang)}</p>
                      <p style={{ margin: 0 }}>{t("hidden_text", lang)}</p>
                    </div>
                  )}

                  {turn.counter.tactic?.tactic && (
                    <>
                      <p className="kv">{t("technique", lang)}</p>
                      <p style={{ margin: "0 0 .6rem" }}>
                        <span className="chip tactic">{turn.counter.tactic.tactic}</span>
                      </p>
                      {turn.counter.tactic.plain_tell && (
                        <p className="source-note">
                          <b>{t("how_to_spot", lang)}:</b> {turn.counter.tactic.plain_tell}
                        </p>
                      )}
                    </>
                  )}

                  <p className="kv">{t("reply_ready", lang)}</p>
                  <div className="prebunk">{turn.counter.reply}</div>
                  <button style={{ marginTop: ".6rem" }}
                          onClick={() => {
                            navigator.clipboard.writeText(turn.counter.reply);
                            setCopied(i);
                          }}>
                    {copied === i ? t("copied", lang) : t("copy", lang)}
                  </button>

                  {turn.counter.evidence?.length > 0 && (
                    <details style={{ marginTop: ".9rem" }}>
                      <summary>{t("evidence", lang)} ({turn.counter.evidence.length})</summary>
                      <ul>{turn.counter.evidence.map((e: any, j: number) => (
                        <li key={j}>
                          <a href={e.url} target="_blank" rel="noreferrer">{e.source_name}</a>
                          {e.claim ? ` — ${e.claim}` : ""}
                        </li>
                      ))}</ul>
                    </details>
                  )}
                </div>
              )}
            </div>
          ))}

          {busy && <AjolotaThinking label={t("thinking", lang)} />}
          <div ref={endRef} />

          <div className="composer">
            <textarea
              rows={3}
              value={text}
              placeholder={t("ask_placeholder", lang)}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(text); }
              }}
            />
            <button className="primary" disabled={busy || !text.trim()} onClick={() => send(text)}>
              {busy ? t("thinking", lang) : t("send", lang)}
            </button>
          </div>
          <p className="source-note">{t("enter_sends", lang)}</p>
        </div>

        <aside className="side-note">
          <h3>{lang === "es" ? "Dos ayudas a la vez" : "Two kinds of help"}</h3>
          <p>{lang === "es"
            ? "La Comadre te explica qué dice la evidencia. La Contra te arma la respuesta que puedes mandar al chat de la familia."
            : "La Comadre explains what the evidence says. La Contra builds the message you can send back to the family chat."}</p>
          <p>{lang === "es"
            ? "Si pegas un mensaje reenviado, trabajan las dos. Si solo preguntas, contesta La Comadre."
            : "Paste a forwarded message and both work. Just ask a question and La Comadre answers."}</p>
        </aside>
      </div>
    </section>
  );
}
