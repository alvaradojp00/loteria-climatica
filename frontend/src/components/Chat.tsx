import { useRef, useState } from "react";
import { api, type Lang } from "../api";

interface Msg { role: "user" | "bot"; content: string; cards?: string[]; tactic?: string | null }

const SEEDS: Record<Lang, string[]> = {
  es: [
    "Mi tía dice que los paneles solares no sirven cuando hace frío",
    "¿Es cierto que China contamina más y lo que hagamos aquí no cambia nada?",
    "Me mandaron que el calor de ahora es igual que siempre",
  ],
  en: [
    "My aunt says solar panels stop working in the cold",
    "Is it true that renewables are what raised my electric bill?",
    "Someone sent me that wind turbines are killing whales",
  ],
};

export function Chat({ lang, onCard }: { lang: Lang; onCard: (id: string) => void }) {
  const [log, setLog] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [spend, setSpend] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);

  async function send(message: string) {
    if (!message.trim() || busy) return;
    setText("");
    setLog((l) => [...l, { role: "user", content: message }]);
    setBusy(true);
    try {
      const history = log.slice(-6).map((m) => ({
        role: m.role === "user" ? "user" : "assistant", content: m.content,
      }));
      const out = await api.chat(message, history);
      setSpend((s) => s + (out.usage?.total_usd ?? 0));
      setLog((l) => [...l, { role: "bot", content: out.text, cards: out.cards, tactic: out.tactic }]);
    } catch (e) {
      setLog((l) => [...l, {
        role: "bot",
        content: lang === "es"
          ? "Se me cayó la conexión. ¿Está corriendo el backend en el puerto 8000?"
          : "I lost the connection. Is the backend running on port 8000?",
      }]);
    } finally {
      setBusy(false);
      requestAnimationFrame(() => boxRef.current?.scrollTo(0, boxRef.current.scrollHeight));
    }
  }

  return (
    <section>
      <h2>La Comadre</h2>
      <p className="lede" style={{ maxWidth: "62ch" }}>
        {lang === "es"
          ? "La amiga que sí leyó los reportes. Pregúntale en español o en inglés — te contesta en el idioma en que le escribas."
          : "The friend who actually read the reports. Ask in English or Spanish — she answers in whichever you use."}
      </p>

      <div className="chat-shell">
        <div>
          <div className="chat-log" ref={boxRef}>
            {log.length === 0 && (
              <div className="bubble bot">
                {lang === "es"
                  ? "¿Qué te mandaron? Pégalo aquí y lo vemos juntas."
                  : "What did they send you? Paste it here and we'll look at it together."}
                <div className="cites">
                  {SEEDS[lang].map((s) => (
                    <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
                  ))}
                </div>
              </div>
            )}
            {log.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.content}
                {(m.cards?.length || m.tactic) && (
                  <div className="cites">
                    {m.tactic && <span className="chip tactic">{m.tactic}</span>}
                    {m.cards?.map((c) => (
                      <button key={c} className="chip" onClick={() => onCard(c)}>
                        {lang === "es" ? "carta" : "card"} {c}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && (
              <div className="bubble bot dots"><span /><span /><span /></div>
            )}
          </div>

          <div className="composer">
            <textarea
              rows={2}
              value={text}
              placeholder={lang === "es" ? "Escribe o pega el mensaje…" : "Type or paste the message…"}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(text); }
              }}
            />
            <button className="primary" disabled={busy || !text.trim()} onClick={() => send(text)}>
              {lang === "es" ? "Enviar" : "Send"}
            </button>
          </div>
          <p className="source-note" style={{ marginTop: ".5rem" }}>
            Enter {lang === "es" ? "envía" : "sends"} · Shift+Enter {lang === "es" ? "salto de línea" : "newline"}
            {spend > 0 && <> · {lang === "es" ? "costo de esta plática" : "this conversation"}: ${spend.toFixed(5)}</>}
          </p>
        </div>

        <aside className="side-note">
          <h3>{lang === "es" ? "Cómo contesta" : "How she answers"}</h3>
          <p>{lang === "es"
            ? "Sólo con lo que traen las cartas y la biblioteca de reportes. Si no tiene el dato, lo dice."
            : "Only from the deck and the curated report library. If she doesn't have the number, she says so."}</p>
          <p>{lang === "es"
            ? "Nombra la táctica cuando el mensaje está armado para engañar, no nada más equivocado."
            : "She names the tactic when a claim is built to mislead rather than simply wrong."}</p>
          <p className="source-note">
            {lang === "es"
              ? "Cada pregunta se guarda sin identificarte. Lo que nadie puede contestar se vuelve una carta nueva."
              : "Every question is logged pseudonymously. What the deck cannot answer becomes a new card."}
          </p>
        </aside>
      </div>
    </section>
  );
}
