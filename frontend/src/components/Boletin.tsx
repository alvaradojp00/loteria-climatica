import { useEffect, useState } from "react";
import { api } from "../api";
import { t, type Lang } from "../i18n";
import { Ajolota } from "./Ajolota";

/** El Boletín, read as a front page rather than a feed: a dated masthead, a
 *  lead story, then the rest. The prebunk line is the thing people take away,
 *  so it is set as the pull quote, not buried under the explanation. */

export function Boletin({ lang, onCard }: { lang: Lang; onCard: (id: string) => void }) {
  const [brief, setBrief] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.boletin().then(setBrief).catch((e) => setErr(String(e.message || e)));
  }, []);

  const fmt = (iso: string) =>
    new Date(iso + "T00:00:00").toLocaleDateString(lang === "es" ? "es-MX" : "en-US",
      { day: "numeric", month: "long", year: "numeric" });

  if (err) return (
    <section>
      <div className="hero tight"><h1>El Boletín</h1></div>
      <p>{t("no_brief", lang)}</p>
      <code className="source-note">python -m agents.boletin --adapter fixture</code>
    </section>
  );
  if (!brief) return (
    <section><div className="hero tight"><h1>El Boletín</h1></div>
      <p className="dots"><span /><span /><span /></p></section>
  );

  const txt = (b: any) => b?.[lang] || b?.en || "";
  const [lead, ...rest] = brief.toplines;

  return (
    <section className="boletin">
      <header className="masthead">
        <div>
          <h1>El Boletín</h1>
          <p className="dateline">
            {fmt(brief.period_start)} — {fmt(brief.period_end)}
            <span className="sep">·</span>
            {lang === "es" ? "cada dos semanas" : "every two weeks"}
          </p>
        </div>
        <p className="masthead-note">{t("brief_lede", lang)}</p>
      </header>

      {lead && (
        <article className="lead-story">
          <div>
            <span className="tag">{lang === "es" ? "Lo que más circuló" : "Biggest this fortnight"}</span>
            <h2>{txt(lead.headline)}</h2>
            <p className="standfirst">{txt(lead.what_is_claimed)}</p>
            <p className="kv">{lang === "es" ? "La técnica" : "The technique"}</p>
            <p className="tactic-line">{lead.tactic}</p>
          </div>
          <aside className="prebunk-card">
            <Ajolota size={62} pose="reading" />
            <p className="kv">{t("say_first", lang)}</p>
            <blockquote>{txt(lead.prebunk)}</blockquote>
            <CardLink t={lead} lang={lang} onCard={onCard} />
          </aside>
        </article>
      )}

      {rest.length > 0 && (
        <>
          <h2 className="rule">{lang === "es" ? "También circulando" : "Also circulating"}</h2>
          <div className="story-grid">
            {rest.map((tl: any, i: number) => (
              <article className="story" key={i}>
                <span className="tag ghost">{tl.tactic}</span>
                <h3>{txt(tl.headline)}</h3>
                <p>{txt(tl.what_is_claimed)}</p>
                <p className="kv">{t("say_first", lang)}</p>
                <blockquote>{txt(tl.prebunk)}</blockquote>
                <CardLink t={tl} lang={lang} onCard={onCard} />
              </article>
            ))}
          </div>
        </>
      )}

      <p className="source-note colophon">
        {lang === "es" ? "Fuente de monitoreo" : "Monitoring source"}: <b>{brief.adapter_used}</b>
      </p>
    </section>
  );
}

function CardLink({ t: tl, lang, onCard }: { t: any; lang: Lang; onCard: (id: string) => void }) {
  if (tl.covering_card) {
    return (
      <p className="source-note">
        {lang === "es" ? "Ya hay carta:" : "Covered by"}{" "}
        <button className="chip" onClick={() => onCard(tl.covering_card)}>
          {lang === "es" ? "carta" : "card"} {tl.covering_card}
        </button>
      </p>
    );
  }
  return (
    <p className="source-note">
      {lang === "es"
        ? "Ninguna carta cubre esto todavía — está en la cola del Taller."
        : "No card covers this yet — it is in the workshop queue."}
    </p>
  );
}
