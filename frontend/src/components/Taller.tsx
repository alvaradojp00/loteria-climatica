import { useEffect, useRef, useState } from "react";
import { api, getAdminToken, setAdminToken } from "../api";
import { t, type Lang } from "../i18n";

interface Ev { type: string; data: any }

const LABEL: Record<string, string> = {
  agent_started: "▸", agent_done: "✓", tool_called: "·", evidence_found: "📎",
  frame_selected: "◆", qa_rejected: "✕", rework: "↺", spend: "$", final: "■", error: "!",
};


function Gate({ lang, onIn }: { lang: Lang; onIn: () => void }) {
  const [pw, setPw] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  useEffect(() => {
    api.health().then((h: any) => setIsDefault(!!h.admin_default)).catch(() => {});
  }, []);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function go() {
    setBusy(true); setErr("");
    try {
      const { token } = await api.adminLogin(pw);
      setAdminToken(token);
      onIn();
    } catch (e: any) {
      // show what the server actually said -- "wrong password" and "locked
      // out for 15 minutes" are different problems for the person typing
      const raw = String(e?.message ?? "");
      const m = raw.match(/"detail"\s*:\s*"([^"]+)"/);
      setErr(m ? m[1] : t("wrong_password", lang));
    }
    finally { setBusy(false); }
  }

  return (
    <section className="gate">
      <h1>{t("admin_title", lang)}</h1>
      <p className="lede">{t("admin_sub", lang)}</p>
      <div className="gate-box">
        <label className="kv" htmlFor="pw">{t("password", lang)}</label>
        <input id="pw" type="password" value={pw} autoFocus
               onChange={(e) => setPw(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && go()} />
        <button className="primary" disabled={busy || !pw} onClick={go}>
          {t("enter", lang)}
        </button>
        {err && <p className="err-text">{err}</p>}
        {isDefault && (
          <p className="source-note gate-hint">
            {lang === "es"
              ? "Esta copia usa la contraseña por defecto: "
              : "This copy is using the default password: "}
            <code>loteria-admin</code>
            <br />
            {lang === "es"
              ? "Define ADMIN_PASSWORD en .env para cambiarla."
              : "Set ADMIN_PASSWORD in .env to change it."}
          </p>
        )}
      </div>
    </section>
  );
}


function ListPanel({ lang }: { lang: Lang }) {
  const es = lang === "es";
  const [data, setData] = useState<any>(null);
  const [aud, setAud] = useState<any>(null);

  const [send, setSend] = useState<any>(null);
  useEffect(() => { api.subscribers().then(setData).catch(() => setData(null)); }, []);
  useEffect(() => { api.sending().then(setSend).catch(() => setSend(null)); }, []);
  if (!data) return null;
  const s = data.stats;

  return (
    <section className="list-panel">
      <h3>{es ? "La lista" : "The list"}</h3>
      <div className="list-stats">
        <div><b>{s.total}</b><span>{es ? "personas" : "people"}</span></div>
        <div><b>{s.sms_consented}</b><span>{es ? "aceptan SMS" : "SMS opted in"}</span></div>
        <div><b>{s.spanish}</b><span>{es ? "en español" : "in Spanish"}</span></div>
        <div><b>{s.last_7_days}</b><span>{es ? "esta semana" : "this week"}</span></div>
      </div>
      <div className="list-actions">
        <a className="btn-link" href={api.subscribersCsv()} download>
          ↓ {es ? "Descargar CSV" : "Download CSV"}
        </a>
        <button onClick={() => api.audience("email").then(setAud)}>
          {es ? "Audiencia de correo" : "Email audience"}
        </button>
        <button onClick={() => api.audience("sms").then(setAud)}>
          {es ? "Audiencia de SMS" : "SMS audience"}
        </button>
      </div>
      {send && !send.any_configured && (
        <div className="send-off">
          <p className="kv">{es ? "Envíos" : "Sending"}</p>
          <p style={{ margin: ".2rem 0 .5rem" }}>
            {es
              ? "Ningún canal está conectado todavía. Descarga el CSV y manda desde tu propia herramienta."
              : "No channel is connected yet. Download the CSV and send from your own tool."}
          </p>
          <ul>
            {send.channels.map((c: any) => (
              <li key={c.channel}>
                <b>{c.label}</b> — {es ? "falta" : "needs"} {c.missing_env.join(", ")}
                <span className="source-note"> · {c.provider_hint}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {aud && (
        <p className="source-note">
          {aud.count} {es ? "personas pueden recibir" : "people can be reached on"}{" "}
          <b>{aud.channel}</b>.{" "}
          {es
            ? "Descarga el CSV y pásalo al proveedor de envíos; quien no dio permiso para ese canal no aparece aquí."
            : "Download the CSV and hand it to your sending provider; anyone who did not consent to that channel is not in this list."}
        </p>
      )}
    </section>
  );
}

export function Taller({ lang, onCard }: { lang: Lang; onCard: (id: string) => void }) {
  const [gaps, setGaps] = useState<any>(null);
  const [claim, setClaim] = useState("");
  const [events, setEvents] = useState<Ev[]>([]);
  const [spend, setSpend] = useState(0);
  const [byAgent, setByAgent] = useState<Record<string, number>>({});
  const [card, setCard] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    if (!getAdminToken()) { setAuthed(false); return; }
    fetch(`${api.base}/api/admin/check`, {
      headers: { "X-Admin-Token": getAdminToken() ?? "" },
    }).then((r) => setAuthed(r.ok)).catch(() => setAuthed(false));
  }, []);

  useEffect(() => { if (authed) api.gaps().then(setGaps).catch(() => setGaps(null)); },
            [card, authed]);
  useEffect(() => { logRef.current?.scrollTo(0, logRef.current.scrollHeight); }, [events]);

  function mint(text: string, gapId?: string) {
    if (!text.trim() || running) return;
    setEvents([]); setSpend(0); setByAgent({}); setCard(null); setRunning(true);
    const es = new EventSource(api.tallerStream(text, gapId));
    es.onmessage = (m) => {
      const ev: Ev = JSON.parse(m.data);
      if (ev.type === "spend") {
        setSpend(ev.data.total_usd ?? 0);
        setByAgent(ev.data.agents ?? {});
      }
      if (ev.type === "card") { setCard(ev.data); }
      setEvents((l) => [...l, ev]);
      if (ev.type === "card" || ev.type === "error") { es.close(); setRunning(false); }
    };
    es.onerror = () => { es.close(); setRunning(false); };
  }

  if (authed === null) return <section><p className="dots"><span /><span /><span /></p></section>;
  if (!authed) return <Gate lang={lang} onIn={() => setAuthed(true)} />;

  const cadence = gaps?.cadence;
  const maxAgent = Math.max(0.0001, ...Object.values(byAgent).map(Number));

  return (
    <section>
      <div className="admin-bar">
        <span className="kv">{t("admin_sub", lang)}</span>
        <button onClick={() => {
          setAdminToken(null);
          setAuthed(false);
          if (window.location.hash === "#taller") window.location.hash = "";
        }}>
          {t("sign_out", lang)}
        </button>
      </div>
      <ListPanel lang={lang} />
      <h2>El Taller de Cartas</h2>
      <p className="lede" style={{ maxWidth: "62ch" }}>
        {lang === "es"
          ? "La fábrica. Un reclamo entra, seis agentes trabajan, dos compuertas pueden rechazarlo, y sale una carta bilingüe con su evidencia."
          : "The factory. A claim goes in, six agents work, two gates can reject it, and a bilingual card with its evidence comes out."}
      </p>

      <div className="taller-grid">
        <aside>
          <div className="side-note" style={{ marginBottom: "1rem" }}>
            <h3>{lang === "es" ? "Cadencia" : "Cadence"}</h3>
            {cadence ? (
              <>
                <p style={{ margin: 0 }}>
                  <b style={{ fontFamily: "var(--display)", fontSize: "1.4rem" }}>
                    {cadence.conversations_last_7_days}
                  </b>{" "}
                  {lang === "es" ? "pláticas en 7 días" : "conversations in 7 days"}
                </p>
                <p className="source-note" style={{ margin: ".3rem 0 0" }}>
                  {lang === "es" ? "umbral" : "threshold"} {cadence.threshold} ·{" "}
                  <b>{cadence.cadence === "weekly"
                    ? (lang === "es" ? "semanal" : "weekly")
                    : (lang === "es" ? "mensual" : "monthly")}</b>
                </p>
              </>
            ) : <p className="source-note">—</p>}
          </div>

          <h3>{lang === "es" ? "Huecos detectados" : "Detected gaps"}</h3>
          <p className="source-note">
            {lang === "es"
              ? `Se necesitan ${gaps?.min_distinct_conversations ?? 3} pláticas distintas antes de poder hacer una carta.`
              : `${gaps?.min_distinct_conversations ?? 3} distinct conversations are required before a card can be minted.`}
          </p>
          {(gaps?.gaps ?? []).slice(0, 8).map((g: any) => (
            <div className="gap-row" key={g.gap_id}>
              <span>
                <b>{g.score.toFixed(2)}</b> {g.topic}
                <br />
                <small className="source-note">
                  {g.distinct_conversations} {lang === "es" ? "personas" : "people"} ·{" "}
                  {Math.round(g.unanswered_rate * 100)}% {lang === "es" ? "sin respuesta" : "unanswered"}
                </small>
              </span>
              <button
                disabled={running || !gaps.mintable.includes(g.gap_id)}
                onClick={() => mint(g.sample_questions[0] ?? g.topic, g.gap_id)}
              >
                {lang === "es" ? "Hacer" : "Mint"}
              </button>
            </div>
          ))}
          {(gaps?.gaps ?? []).length === 0 && (
            <p className="source-note">{lang === "es" ? "Sin huecos todavía — usa el chat y vuelve." : "No gaps yet — use the chat and come back."}</p>
          )}
        </aside>

        <div>
          <textarea
            rows={2}
            value={claim}
            placeholder={lang === "es" ? "O escribe un reclamo para convertirlo en carta…" : "Or type a claim to turn into a card…"}
            onChange={(e) => setClaim(e.target.value)}
          />
          <button className="primary" style={{ marginTop: ".6rem" }}
                  disabled={running || !claim.trim()} onClick={() => mint(claim)}>
            {running ? (lang === "es" ? "Trabajando…" : "Working…") : (lang === "es" ? "Hacer la carta" : "Mint the card")}
          </button>

          <div className="stream" ref={logRef} style={{ marginTop: "1rem" }}>
            {events.length === 0 && <div style={{ opacity: .5 }}>
              {lang === "es" ? "Los agentes aparecen aquí mientras trabajan." : "The agents show up here as they work."}
            </div>}
            {events.map((e, i) => (
              <div key={i} className={`ev ${e.type === "qa_rejected" || e.type === "rework" ? "reject" : ""} ${e.type === "spend" ? "spend" : ""}`}>
                {LABEL[e.type] ?? "·"}{" "}
                {e.type === "agent_started" && `${e.data.agent} started`}
                {e.type === "agent_done" && `${e.data.agent} done`}
                {e.type === "tool_called" && `tool ${e.data.tool}`}
                {e.type === "evidence_found" && `${e.data.count ?? e.data.signals} citations — ${(e.data.sources ?? []).join(", ")}`}
                {e.type === "frame_selected" && `frame ${e.data.frame} (lift ${e.data.lift}) · rejected ${e.data.rejected?.length ?? 0}`}
                {e.type === "qa_rejected" && `${e.data.gate} REJECTED: ${(e.data.problems ?? [])[0]?.slice(0, 150)}`}
                {e.type === "rework" && `rework pass ${e.data.attempt}`}
                {e.type === "spend" && `${e.data.agent} $${e.data.call?.cost_usd?.toFixed(5)} — total $${e.data.total_usd?.toFixed(5)}`}
                {e.type === "final" && `done — ${e.data.name ?? ""} ${e.data.status ?? ""}`}
                {e.type === "error" && `error: ${e.data.error}`}
              </div>
            ))}
          </div>

          <div style={{ marginTop: "1rem" }}>
            <p className="kv">{lang === "es" ? "Gasto por agente" : "Spend by agent"} — ${spend.toFixed(5)}</p>
            {Object.entries(byAgent).map(([agent, usd]) => (
              <div key={agent} style={{ marginBottom: ".4rem" }}>
                <small>{agent} ${Number(usd).toFixed(5)}</small>
                <div className="meter"><i style={{ width: `${(Number(usd) / maxAgent) * 100}%` }} /></div>
              </div>
            ))}
          </div>

          {card && (
            <div className="topline" style={{ marginTop: "1.2rem" }}>
              <p className="kv">{lang === "es" ? "Carta nueva" : "New card"} {card.id}</p>
              <h3>{card.name.es}</h3>
              <p className="truth">{card.truth_headline.es}</p>
              <p className="source-note">
                {lang === "es" ? "marco" : "frame"} {card.frame?.frame} · {card.evidence?.length} {lang === "es" ? "fuentes" : "sources"} ·{" "}
                {card.status === "needs_human"
                  ? (lang === "es" ? "pendiente de revisión" : "needs review")
                  : (lang === "es" ? "borrador" : "draft")}
              </p>
              <button onClick={() => onCard(card.id)}>{lang === "es" ? "Ver la carta" : "Open the card"}</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
