import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { type Lang } from "../i18n";

/** Structure borrowed from how CAAD and Climate Power present a library:
 *  filter rows for type and topic, a featured block, then a stacked list of
 *  cards carrying tags, a title, the organisation, and a line on why it is
 *  worth your click. Every link points at a specific page, never a homepage. */

interface Item {
  id: string;
  title: { en: string; es: string };
  org: string;
  url: string;
  type: string;
  topics: string[];
  why: { en: string; es: string };
  featured?: boolean;
}

const TYPE_LABEL: Record<string, { es: string; en: string }> = {
  report: { es: "Reporte", en: "Report" },
  polling: { es: "Encuesta", en: "Polling" },
  tool: { es: "Herramienta", en: "Tool" },
  coalition: { es: "Coalición", en: "Coalition" },
  "fact-check": { es: "Verificación", en: "Fact-check" },
  action: { es: "Actuar", en: "Take action" },
};

const TOPIC_LABEL: Record<string, { es: string; en: string }> = {
  "spanish-language": { es: "en español", en: "Spanish-language" },
  latino: { es: "latinos", en: "Latino" },
  disinformation: { es: "desinformación", en: "disinformation" },
  "extreme-weather": { es: "clima extremo", en: "extreme weather" },
  "clean-energy": { es: "energía limpia", en: "clean energy" },
  platforms: { es: "plataformas", en: "platforms" },
  health: { es: "salud", en: "health" },
  ai: { es: "IA", en: "AI" },
};

const lbl = (m: Record<string, { es: string; en: string }>, k: string, lang: Lang) =>
  m[k] ? m[k][lang] : k;

export function Resources({ lang }: { lang: Lang }) {
  const [data, setData] = useState<any>(null);
  const [type, setType] = useState<string | null>(null);
  const [topic, setTopic] = useState<string | null>(null);

  useEffect(() => { api.resources().then(setData).catch(() => setData(null)); }, []);

  const items: Item[] = data?.items ?? [];
  const shown = useMemo(() => items.filter((i) =>
    (!type || i.type === type) && (!topic || i.topics.includes(topic))), [items, type, topic]);
  const featured = items.filter((i) => i.featured);

  if (!data) return <section><h1>{lang === "es" ? "Recursos" : "Resources"}</h1>
    <p className="dots"><span /><span /><span /></p></section>;

  return (
    <section className="library">
      <div className="hero tight">
        <h1>{lang === "es" ? "Recursos" : "Resources"}</h1>
        <p className="lede">
          {lang === "es"
            ? "Lo que leí para armar este mazo, y a dónde ir cuando quieras más. Cada liga va a una página específica — un reporte, una encuesta, una herramienta — nunca a la portada de una organización."
            : "What I read to build this deck, and where to go when you want more. Every link points at a specific page — a report, a poll, a tool — never an organisation's front door."}
        </p>
      </div>

      {!type && !topic && (
        <>
          <h2 className="rule">{lang === "es" ? "Empieza aquí" : "Start here"}</h2>
          <div className="featured-grid">
            {featured.map((i) => (
              <a className="feat" key={i.id} href={i.url} target="_blank" rel="noreferrer">
                <span className="tag">{lbl(TYPE_LABEL, i.type, lang)}</span>
                <h3>{i.title[lang]}</h3>
                <p className="org">{i.org}</p>
                <p>{i.why[lang]}</p>
                <span className="go">{lang === "es" ? "Leer" : "Read"} →</span>
              </a>
            ))}
          </div>
        </>
      )}

      <h2 className="rule">{lang === "es" ? "La biblioteca" : "The library"}</h2>

      <div className="filter-rows">
        <div className="filter-row">
          <span className="kv">{lang === "es" ? "Tipo" : "Type"}</span>
          <button aria-pressed={!type} onClick={() => setType(null)}>
            {lang === "es" ? "Todos" : "All"}
          </button>
          {data.types.map((tp: string) => (
            <button key={tp} aria-pressed={type === tp}
                    onClick={() => setType(type === tp ? null : tp)}>
              {lbl(TYPE_LABEL, tp, lang)}
            </button>
          ))}
        </div>
        <div className="filter-row">
          <span className="kv">{lang === "es" ? "Tema" : "Topic"}</span>
          <button aria-pressed={!topic} onClick={() => setTopic(null)}>
            {lang === "es" ? "Todos" : "All"}
          </button>
          {data.topics.map((tp: string) => (
            <button key={tp} aria-pressed={topic === tp}
                    onClick={() => setTopic(topic === tp ? null : tp)}>
              {lbl(TOPIC_LABEL, tp, lang)}
            </button>
          ))}
        </div>
        {(type || topic) && (
          <button className="clear" onClick={() => { setType(null); setTopic(null); }}>
            {lang === "es" ? "Limpiar filtros" : "Clear all"}
          </button>
        )}
      </div>

      <p className="count">{shown.length} {lang === "es" ? "recursos" : "resources"}</p>

      <div className="lib-list">
        {shown.map((i) => (
          <a className="lib-item" key={i.id} href={i.url} target="_blank" rel="noreferrer">
            <div className="lib-tags">
              <span className="tag">{lbl(TYPE_LABEL, i.type, lang)}</span>
              {i.topics.map((tp) => (
                <span className="tag ghost" key={tp}>{lbl(TOPIC_LABEL, tp, lang)}</span>
              ))}
            </div>
            <h3>{i.title[lang]}</h3>
            <p className="org">{i.org}</p>
            <p className="why">{i.why[lang]}</p>
            <span className="url">{new URL(i.url).hostname.replace("www.", "")}</span>
          </a>
        ))}
      </div>

      <h2 className="rule">{lang === "es" ? "Cómo reportar" : "How to report"}</h2>
      <p className="lede" style={{ maxWidth: "62ch" }}>
        {lang === "es"
          ? "Reportar no borra el mensaje, pero cuenta. Y hay algo más importante: no lo reenvíes para preguntar. Toma captura."
          : "Reporting doesn't delete the message, but it counts. And one thing matters more: don't forward it to ask about it. Screenshot instead."}
      </p>
      <div className="report-grid">
        {data.reporting.map((r: any) => (
          <div className="report" key={r.platform}>
            <strong>{r.platform}</strong>
            <p>{lang === "es" ? r.es : r.en}</p>
            {(lang === "es" ? r.note_es : r.note_en) && (
              <p className="source-note">{lang === "es" ? r.note_es : r.note_en}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
