/** All HTTP in one place, so components stay about the UI. */

const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8010";

export type { Lang } from "./i18n";
export interface Bilingual { en: string; es: string }

export interface CardSummary {
  id: string; number: number; slug: string;
  name: Bilingual; category: string;
  provenance: "original" | "generated";
  status: string; frame: string | null;
  art: string | null;
}

export interface Evidence {
  claim: string; source_name: string; url: string; excerpt: string;
}

export interface FrameChoice {
  frame: string; measured_lift: number | null;
  audience_note: string; rationale: string; rejected: string[];
}

export interface CardFull extends CardSummary {
  myth: Bilingual; truth_headline: Bilingual; body: Bilingual; action: Bilingual;
  evidence: Evidence[]; frame_detail?: FrameChoice | null;
  notes: string; created_by: string; motif: string;
}

let adminToken: string | null = localStorage.getItem("lc-admin") ?? null;

export function setAdminToken(tok: string | null) {
  adminToken = tok;
  if (tok) localStorage.setItem("lc-admin", tok);
  else localStorage.removeItem("lc-admin");
  // the shell shows the operator tab only while signed in
  window.dispatchEvent(new CustomEvent("lc-admin-change"));
}

/** Is the stored token still good? Used to decide whether to show the tab. */
export async function checkAdmin(): Promise<boolean> {
  if (!adminToken) return false;
  try {
    const r = await fetch(`${BASE}/api/admin/check`, {
      headers: { "X-Admin-Token": adminToken },
    });
    return r.ok;
  } catch { return false; }
}
export function getAdminToken() { return adminToken; }

function authHeaders(): Record<string, string> {
  return adminToken ? { "X-Admin-Token": adminToken } : {};
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { headers: authHeaders() });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const api = {
  base: BASE,
  health: () => get<{ ok: boolean; cards: number; generated: number; model: string }>("/api/health"),
  deck: (category?: string) =>
    get<{ count: number; categories: string[]; cards: CardSummary[] }>(
      `/api/deck${category ? `?category=${encodeURIComponent(category)}` : ""}`),
  card: (id: string) => get<any>(`/api/cards/${id}`),
  chat: (message: string, history: { role: string; content: string }[]) =>
    post<{ text: string; cards: string[]; tactic: string | null; lang: Lang;
           usage: { total_usd: number } }>("/api/chat", { message, history }),
  ask: (message: string, history: { role: string; content: string }[]) =>
    post<{ mode: "question" | "forward"; explanation: any; counter: any }>(
      "/api/ask", { message, history }),
  contra: (material: string, defend = true) =>
    post<any>("/api/contra", { material, defend }),
  gaps: () => get<any>("/api/gaps"),
  boletin: () => get<any>("/api/boletin"),
  stats: () => get<any>("/api/stats"),
  pricing: () => get<any>("/api/pricing"),
  approve: (id: string) => post<any>(`/api/taller/approve/${id}`, {}),
  cardSvg: (id: string, face: "front" | "back", lang: Lang) =>
    `${BASE}/api/cards/${id}/svg?face=${face}&lang=${lang}`,
  artUrl: (path: string) => `${BASE.replace(/\/$/, "")}/../${path}`,
  tablas: (count = 6, seed?: number) =>
    get<any>(`/api/tablas?count=${count}` + (seed ? `&seed=${seed}` : "")),
  subscribe: (body: Record<string, unknown>) =>
    post<{ ok: boolean; status: string }>("/api/subscribe", body),
  subscribers: () => get<any>("/api/admin/subscribers"),
  subscribersCsv: () => `${BASE}/api/admin/subscribers.csv`,
  sending: () => get<any>("/api/admin/sending"),
  audience: (channel: string) => get<any>(`/api/admin/audience?channel=${channel}`),
  resources: () => get<any>("/api/resources"),
  deckUrl: (lang: string, fmt: "pdf" | "pptx") =>
    `${BASE}/api/export/deck?lang=${lang}&fmt=${fmt}`,
  adminLogin: (password: string) =>
    post<{ token: string }>("/api/admin/login", { password }),
  tallerStream: (claim: string, gapId?: string) =>
    `${BASE}/api/taller/stream?claim=${encodeURIComponent(claim)}` +
    `&token=${encodeURIComponent(adminToken ?? "")}` +
    (gapId ? `&gap_id=${encodeURIComponent(gapId)}` : ""),
};
