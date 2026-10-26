import { useState } from "react";
import { api, type Lang } from "../api";

const EXAMPLE = `*URGENTE - COMPARTE CON TU FAMILIA*

Los paneles solares que están instalando en el barrio son peligrosos. Cuando hace frío dejan de funcionar y por eso se cayó la luz en Texas. Además las baterías explotan.

Pásalo a 10 personas 🙏`;

export function Contra({ lang }: { lang: Lang }) {
  const [material, setMaterial] = useState("");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  async function run() {
    if (!material.trim() || busy) return;
    setBusy(true); setOut(null); setCopied(false);
    try { setOut(await api.contra(material, true)); }
    catch (e: any) { setOut({ error: String(e.message || e) }); }
    finally { setBusy(false); }
  }

  return (
    <section>
      <h2>La Contra</h2>
      <p className="lede" style={{ maxWidth: "62ch" }}>
        {lang === "es"
          ? "Pega el mensaje que te reenviaron. Te decimos con qué técnica está armado, qué dice la evidencia, y te damos una respuesta lista para mandar."
          : "Paste the forward you received. We name the technique it uses, check the evidence, and hand you a reply you can send."}
      </p>

      <div className="chat-shell">
        <div>
          <textarea
            rows={9}
            value={material}
            placeholder={lang === "es" ? "Pega aquí el mensaje reenviado…" : "Paste the forwarded message here…"}
            onChange={(e) => setMaterial(e.target.value)}
          />
          <div style={{ display: "flex", gap: ".6rem", marginTop: ".7rem", flexWrap: "wrap" }}>
            <button className="primary" disabled={busy || !material.trim()} onClick={run}>
              {busy ? (lang === "es" ? "Analizando…" : "Analysing…") : (lang === "es" ? "Armar respuesta" : "Build a reply")}
            </button>
            <button onClick={() => setMaterial(EXAMPLE)}>
              {lang === "es" ? "Usar ejemplo" : "Use an example"}
            </button>
          </div>

          {busy && <p className="dots" style={{ marginTop: "1rem" }}><span /><span /><span /></p>}

          {out?.error && <p style={{ color: "var(--orange)" }}>{out.error}</p>}

          {out?.status === "ok" && (
            <div style={{ marginTop: "1.4rem" }}>
              {out.packet?.embedded_instructions && (
                <div className="topline" style={{ borderLeftColor: "var(--teal)" }}>
                  <p className="kv">{lang === "es" ? "Aviso de seguridad" : "Safety notice"}</p>
                  <p style={{ margin: 0 }}>
                    {lang === "es"
                      ? "Este mensaje traía texto escondido dirigido a sistemas de IA, invisible para quien lo lee en el teléfono. Lo tratamos como evidencia, no como instrucción."
                      : "This message carried hidden text aimed at AI systems, invisible to a person reading it on a phone. We treated it as evidence, not instruction."}
                  </p>
                  <code style={{ fontSize: ".78rem", opacity: .75 }}>{out.packet.instruction_excerpt}</code>
                </div>
              )}

              <p className="kv">{lang === "es" ? "Técnica usada" : "Technique used"}</p>
              <p><span className="chip tactic">{out.tactic?.tactic ?? "—"}</span> {out.tactic?.why}</p>
              {out.tactic?.plain_tell && (
                <p className="source-note">{lang === "es" ? "Cómo reconocerla: " : "How to spot it: "}{out.tactic.plain_tell}</p>
              )}

              <p className="kv">{lang === "es" ? "Respuesta lista para mandar" : "Ready to send"}</p>
              <div className="prebunk">{out.reply}</div>
              <button style={{ marginTop: ".6rem" }}
                      onClick={() => { navigator.clipboard.writeText(out.reply); setCopied(true); }}>
                {copied ? (lang === "es" ? "Copiado ✓" : "Copied ✓") : (lang === "es" ? "Copiar" : "Copy")}
              </button>

              {out.evidence?.length > 0 && (
                <details style={{ marginTop: "1rem" }}>
                  <summary>{lang === "es" ? "Evidencia" : "Evidence"} ({out.evidence.length})</summary>
                  <ul>{out.evidence.map((e: any, i: number) => (
                    <li key={i}><a href={e.url} target="_blank" rel="noreferrer">{e.source_name}</a> — {e.claim}</li>
                  ))}</ul>
                </details>
              )}
              <p className="source-note" style={{ marginTop: ".8rem" }}>
                {lang === "es" ? "Marco" : "Frame"}: {out.frame?.frame}
                {out.frame?.measured_lift != null && <> (+{out.frame.measured_lift})</>}
                {" · "}{lang === "es" ? "costo" : "cost"} ${out.usage?.total_usd?.toFixed(5)}
                {out.critic?.passed === false && <> · <b>{lang === "es" ? "el crítico marcó problemas" : "critic flagged issues"}</b></>}
              </p>
            </div>
          )}
        </div>

        <aside className="side-note">
          <h3>{lang === "es" ? "Por qué una respuesta corta" : "Why a short reply"}</h3>
          <p>{lang === "es"
            ? "Va a un chat de familia. Empieza reconociendo lo que sí es cierto, usa un solo dato, y cabe en una pantalla."
            : "It goes to a family chat. It opens by conceding what is true, rests on one fact, and fits on a screen."}</p>
          <p className="source-note">
            {lang === "es"
              ? "Todo lo que pegas se trata como material a examinar, nunca como instrucciones para el sistema."
              : "Anything you paste is treated as material to examine, never as instructions to the system."}
          </p>
        </aside>
      </div>
    </section>
  );
}
