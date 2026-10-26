import { useEffect, useState } from "react";
import { api, checkAdmin } from "./api";
import { t, type Lang } from "./i18n";
import { Home } from "./components/Home";
import { Deck, CardModal } from "./components/Deck";
import { Ask } from "./components/Ask";
import { Jugar } from "./components/Jugar";
import { Taller } from "./components/Taller";
import { Boletin } from "./components/Boletin";
import { Resources } from "./components/Resources";
import { About } from "./components/About";

type Tab = "home" | "deck" | "ayuda" | "boletin" | "jugar" | "recursos" | "about" | "taller";

const PUBLIC: { id: Tab; key: string }[] = [
  { id: "home", key: "nav_home" },
  { id: "deck", key: "nav_deck" },
  { id: "ayuda", key: "nav_ayuda" },
  { id: "boletin", key: "nav_boletin" },
  { id: "jugar", key: "nav_jugar" },
  { id: "recursos", key: "nav_recursos" },
  { id: "about", key: "nav_about" },
];

const TICKER: Record<Lang, string[]> = {
  es: ["54 cartas · 2 idiomas", "Juega con tu familia",
       "El mito, la verdad, y qué hacer", "Imprime tus tablas gratis",
       "Pregúntale a La Comadre"],
  en: ["54 cards · 2 languages", "Play it with your family",
       "The myth, the truth, and what to do", "Print your boards free",
       "Ask La Comadre"],
};

export default function App() {
  const [tab, setTab] = useState<Tab>(() =>
    window.location.hash === "#taller" ? "taller" : "home");
  const [lang, setLang] = useState<Lang>(() =>
    (localStorage.getItem("lc-lang") as Lang) ??
    (navigator.language.startsWith("es") ? "es" : "en"));
  const [focus, setFocus] = useState<string | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => { localStorage.setItem("lc-lang", lang); }, [lang]);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)); }, []);
  useEffect(() => {
    const sync = () => { checkAdmin().then(setIsAdmin); };
    sync();
    window.addEventListener("lc-admin-change", sync);
    return () => window.removeEventListener("lc-admin-change", sync);
  }, []);
  useEffect(() => {
    const onHash = () => setTab(window.location.hash === "#taller" ? "taller" : "home");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <div className="app">
      <nav className="nav">
        <div className="wrap nav-inner">
          <button className="brand" onClick={() => setTab("deck")}>
            Lotería <span>Climática</span>
          </button>
          {(isAdmin ? [...PUBLIC, { id: "taller" as Tab, key: "nav_taller" }] : PUBLIC).map((x) => (
            <button key={x.id} aria-current={tab === x.id ? "page" : undefined}
                    onClick={() => { setTab(x.id); window.scrollTo(0, 0); }}
                    className={x.id === "taller" ? "nav-admin" : undefined}>
              {t(x.key, lang)}
            </button>
          ))}
          <div className="lang-toggle" role="group" aria-label="language">
            <button aria-pressed={lang === "es"} onClick={() => setLang("es")}>ES</button>
            <button aria-pressed={lang === "en"} onClick={() => setLang("en")}>EN</button>
          </div>
        </div>
      </nav>

      <div className="ticker" aria-hidden="true">
        <div className="ticker-track">
          {[...TICKER[lang], ...TICKER[lang]].map((line, i) => (
            <span key={i}>{line}</span>
          ))}
        </div>
      </div>

      <main className="wrap">
        {!health && <p className="banner">{t("backend_down", lang)}</p>}

        {tab === "home" && <Home lang={lang} go={(x) => { setTab(x as Tab); window.scrollTo(0, 0); }} />}
        {tab === "deck" && <Deck lang={lang} focus={focus} onFocus={setFocus}
                          onPlay={() => setTab("jugar")}
                          onAsk={() => setTab("ayuda")} />}
        {tab === "ayuda" && <Ask lang={lang} onCard={setFocus} />}
        {tab === "boletin" && <Boletin lang={lang} onCard={setFocus} />}
        {tab === "jugar" && <Jugar lang={lang} />}
        {tab === "recursos" && <Resources lang={lang} />}
        {tab === "about" && <About lang={lang} />}
        {tab === "taller" && <Taller lang={lang} onCard={setFocus} />}

        {tab !== "deck" && focus && (
          <CardModal id={focus} lang={lang} onClose={() => setFocus(null)} />
        )}
      </main>

      <footer className="wrap">
        {tab === "deck" && (
          <p>
            {lang === "es"
              ? "Las cartas 1–12 fueron creadas por Juan Pablo Alvarado en GreenLatinos, en colaboración con Intersectional Environmentalist, y se muestran aquí con crédito."
              : "Cards 1–12 were created by Juan Pablo Alvarado at GreenLatinos, in partnership with Intersectional Environmentalist, and are shown here with attribution."}
          </p>
        )}
        <p className="source-note foot-row">
          <span>Lotería Climática · {lang === "es"
            ? "proyecto independiente de Juan Pablo Alvarado"
            : "an independent project by Juan Pablo Alvarado"}</span>
          {!isAdmin && (
            <button className="foot-admin"
                    onClick={() => { window.location.hash = "taller"; setTab("taller"); }}>
              {lang === "es" ? "Operador" : "Operator"}
            </button>
          )}
        </p>
      </footer>
    </div>
  );
}
