import { useEffect, useRef, useState } from "react";
import { api, type CardSummary } from "../api";
import { t, type Lang } from "../i18n";
import { Ajolota } from "./Ajolota";

/** The landing page, built to the sketch: banner, who the game is for, the
 *  chatbot, then the brief and the library, and a signup at the foot.
 *
 *  Sections fade up as they enter the viewport — the scroll-driven movement
 *  Climate Power's site uses to make a long page feel alive. IntersectionObserver
 *  rather than a scroll handler, and it respects prefers-reduced-motion.
 */

function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setSeen(true);
      return;
    }
    const io = new IntersectionObserver(
      ([e]) => e.isIntersecting && (setSeen(true), io.disconnect()),
      { rootMargin: "-60px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return { ref, className: `reveal${seen ? " in" : ""}` };
}

function Section({ children, className = "" }:
  { children: React.ReactNode; className?: string }) {
  const r = useReveal<HTMLElement>();
  return <section ref={r.ref} className={`${r.className} ${className}`}>{children}</section>;
}

export function Home({ lang, go }: { lang: Lang; go: (tab: string) => void }) {
  const [cards, setCards] = useState<CardSummary[]>([]);
  const es = lang === "es";

  useEffect(() => { api.deck().then((d) => setCards(d.cards)).catch(() => {}); }, []);

  const art = (c: CardSummary) =>
    c.art ? `${api.base}/${c.art}` : api.cardSvg(c.id, "front", "es");

  return (
    <div className="home">
      {/* ---------------------------------------------------------- banner */}
      <Section className="home-banner">
        <div>
          <h1>{es ? <>Lotería <b>Climática</b></> : <>Climate <b>Lotería</b></>}</h1>
          <p className="lede">{t("deck_lede", lang)}</p>
          <div className="hero-cta">
            <button className="primary" onClick={() => go("deck")}>
              {es ? "Ver las 54 cartas" : "See all 54 cards"}
            </button>
            <button onClick={() => go("jugar")}>{es ? "Jugar" : "Play"}</button>
          </div>
        </div>
        <div className="fan" aria-hidden="true">
          {cards.slice(0, 5).map((c) =>
            c.art ? <img key={c.id} src={art(c)} alt="" loading="lazy" />
                  : <object key={c.id} data={art(c)} type="image/svg+xml" />)}
        </div>
      </Section>

      {/* ------------------------------------------------- who it is for */}
      <Section className="band sand home-who">
        <div>
          <span className="tag">{es ? "Para quién es" : "Who it's for"}</span>
          <h2>{es ? "Para la mesa de tu casa" : "For your kitchen table"}</h2>
          <p>
            {es
              ? "Para quien recibe el mensaje reenviado y no sabe qué contestar. Para el que quiere hablar con su tío sin pelearse. Para la maestra, la organizadora, la prima que siempre acaba explicando las cosas."
              : "For whoever gets the forwarded message and doesn't know what to say back. For anyone who wants to talk to their tío without it turning into a fight. For the teacher, the organiser, the cousin who always ends up explaining things."}
          </p>
          <p>
            {es
              ? "Empezó con doce cartas que hice en GreenLatinos y con los recuerdos de jugar lotería con mis abuelitos. Ahora son 54, y el mazo crece con lo que la gente pregunta."
              : "It started with twelve cards I made at GreenLatinos, and with playing lotería at my grandparents' table. Now there are 54, and the deck grows from what people ask."}
          </p>
          <button onClick={() => go("about")}>
            {es ? "Leer la historia" : "Read the story"} →
          </button>
        </div>
        <img className="home-photo"
             src={`${api.base}/assets/web/event/group-holding-cards.jpg`}
             alt={es ? "Gente sosteniendo las cartas" : "People holding the cards"} />
      </Section>

      {/* ------------------------------------------------------- chatbot */}
      <Section className="home-bot">
        <div className="home-bot-art"><Ajolota size={230} pose="waving" /></div>
        <div>
          <span className="tag">{es ? "La Comadre Ajolota" : "Comadre Ajolota"}</span>
          <h2>{es ? "Pregúntale lo que te mandaron" : "Ask her about what you got sent"}</h2>
          <p>
            {es
              ? "Pega el mensaje reenviado o escribe tu duda. Te dice qué dice la evidencia, con qué técnica está armado el mensaje, y —lo importante— te da la frase que sí puedes decirle a tu gente."
              : "Paste the forwarded message or just ask. She tells you what the evidence says, names the technique the message uses, and — the part that matters — hands you the line you can actually say to your people."}
          </p>
          <button className="primary" onClick={() => go("ayuda")}>
            {es ? "Preguntarle ahora" : "Ask her now"}
          </button>
        </div>
      </Section>

      {/* ------------------------------------------- the brief + library */}
      <Section className="home-two">
        <article className="band leaf">
          <span className="tag">{es ? "Cada dos semanas" : "Every two weeks"}</span>
          <h2>El Boletín</h2>
          <p>
            {es
              ? "Qué está circulando ahora mismo en español, con qué técnica está armado, y una frase que puedes decir en la mesa antes de que la desinformación te llegue."
              : "What is circulating in Spanish right now, the technique behind it, and a line you can say at the table before the disinformation reaches you."}
          </p>
          <button onClick={() => go("boletin")}>{es ? "Leer el boletín" : "Read the brief"} →</button>
        </article>
        <article className="band sky">
          <span className="tag">{es ? "La biblioteca" : "The library"}</span>
          <h2>{es ? "Recursos" : "Resources"}</h2>
          <p>
            {es
              ? "Lo que leí para armar este mazo: reportes, encuestas y verificadores en español. Cada liga va a una página específica, nunca a la portada de una organización. Se actualiza cada semana."
              : "What I read to build this deck: reports, polling and Spanish-language fact-checkers. Every link goes to a specific page, never an organisation's front door. Updated weekly."}
          </p>
          <button onClick={() => go("recursos")}>{es ? "Ver los recursos" : "Browse resources"} →</button>
        </article>
      </Section>

      {/* -------------------------------------------------------- signup */}
      <Section className="home-signup">
        <Signup lang={lang} />
      </Section>
    </div>
  );
}

function Signup({ lang }: { lang: Lang }) {
  const es = lang === "es";
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [err, setErr] = useState("");
  const [consent, setConsent] = useState(false);
  const [sms, setSms] = useState(false);

  const CONSENT = es
    ? "Sí, quiero recibir avisos de cartas nuevas y del boletín."
    : "Yes, send me new cards and the brief.";

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setState("sending"); setErr("");
    try {
      await api.subscribe({
        name: String(f.get("name") || ""),
        email: String(f.get("email") || ""),
        zip: String(f.get("zip") || ""),
        phone: String(f.get("phone") || ""),
        lang,
        sms_consent: sms,
        consent_text: CONSENT,
      });
      setState("done");
    } catch (ex: any) {
      setErr(String(ex.message || ex).replace(/^\d+\s*/, ""));
      setState("error");
    }
  }

  return (
    <div className="joinbox">
      <div className="joinbox-head">
        <Ajolota size={120} pose="excited" />
        <div>
          <span className="tag">{es ? "Súmate" : "Join in"}</span>
          <h2>{es ? "Únete a la lucha contra la desinformación climática"
                  : "Join the fight against climate disinformation"}</h2>
          <p>
            {es
              ? "Te avisamos cuando salga una carta nueva y cuando publiquemos el boletín. Nada más, y te puedes dar de baja con un clic."
              : "We'll tell you when a new card drops and when the brief goes out. Nothing else, and you can leave with one click."}
          </p>
        </div>
      </div>

      {state === "done" ? (
        <p className="joinbox-done">
          {es ? "¡Listo! Nos vemos en el próximo boletín." : "You're in. See you in the next brief."}
        </p>
      ) : (
        <form className="joinbox-form" onSubmit={submit}>
          <label>
            <span className="kv">{es ? "Nombre" : "Name"}</span>
            <input name="name" autoComplete="name" required />
          </label>
          <label>
            <span className="kv">{es ? "Correo" : "Email"}</span>
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            <span className="kv">{es ? "Código postal" : "ZIP code"}</span>
            <input name="zip" inputMode="numeric" autoComplete="postal-code" />
          </label>
          <label>
            <span className="kv">{es ? "Teléfono (opcional)" : "Phone (optional)"}</span>
            <input name="phone" type="tel" autoComplete="tel" />
          </label>

          <div className="joinbox-consents">
            <label className="consent">
              <input type="checkbox" checked={consent}
                     onChange={(e) => setConsent(e.target.checked)} required />
              <span>{CONSENT}</span>
            </label>
            <label className="consent">
              <input type="checkbox" checked={sms}
                     onChange={(e) => setSms(e.target.checked)} />
              <span>{es ? "También pueden mandarme mensajes de texto."
                        : "You can text me too."}</span>
            </label>
          </div>

          <button className="primary big" type="submit"
                  disabled={!consent || state === "sending"}>
            {state === "sending"
              ? (es ? "Mandando…" : "Sending…")
              : (es ? "Apuntarme" : "Sign me up")}
          </button>
          {state === "error" && <p className="err-text">{err}</p>}
        </form>
      )}
    </div>
  );
}
