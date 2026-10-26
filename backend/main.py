"""FastAPI routes. A thin layer: define the endpoint, call the lane, return JSON.

The one route that is not thin is /api/taller/stream, which is the showcase --
it streams the agent mesh working, event by event, to the dashboard.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import hashlib
import os
import secrets
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

import archivista
import gaps
import ledger
import render
import senders
import subscribers
import tablas
import tools
from adapters import base as adapters
from adapters import junkipedia
from agents import boletin, comadre, contra, taller
from config import ASSETS, DATA, MODEL, OUTPUT, allowed_origins
from events import sse
from ledger import pseudonym
from pricing import PRICE_SOURCE, PRICES, project_costs

app = FastAPI(title="Lotería Climática", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Headers that cost nothing and close the cheap attacks.

    The operator pages list real contact details, so the referrer is kept off
    outbound links and the content type is never re-sniffed.
    """
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return resp


# The original card artwork, served so the deck page can show cards 1-12 as
# they were actually printed.
app.mount("/assets", StaticFiles(directory=str(ASSETS)), name="assets")


# ------------------------------------------------------------------ admin
#
# El Taller is an operator surface: it mints content, spends the key, and shows
# unreviewed drafts. It is not for the public. The password lives in .env; the
# token is in-memory, so restarting the server logs everyone out.

# token -> the moment it stops being valid. A session that never expires is a
# password that leaks once and works forever.
_SESSIONS: dict[str, float] = {}
SESSION_TTL_SECONDS = 8 * 3600


def _session_ok(token: str) -> bool:
    """True if the token is live. Expired tokens are dropped on the way past."""
    if not token:
        return False
    now = time.time()
    for dead in [t for t, exp in _SESSIONS.items() if exp <= now]:
        _SESSIONS.pop(dead, None)
    return token in _SESSIONS

# Hiding the login URL is not a security control -- the password is. So the
# door is allowed to be findable, and the lock is made to hold: failed
# attempts are counted per client and throttled.
_ATTEMPTS: dict[str, list[float]] = {}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 900


DEFAULT_ADMIN_PASSWORD = "loteria-admin"


def admin_password() -> str:
    """The operator password.

    A documented default is right for a graded clone and wrong for anything
    reachable from the internet, so it is allowed only in the local case.
    ALLOWED_ORIGINS is set exactly when the app has been pointed at a real
    frontend, which makes it a reliable "this is deployed" signal: in that
    case an unset ADMIN_PASSWORD fails closed rather than quietly shipping a
    password that is printed in the README.
    """
    pw = os.getenv("ADMIN_PASSWORD")
    if pw:
        return pw
    if os.getenv("ALLOWED_ORIGINS", "").strip():
        raise HTTPException(
            503, "ADMIN_PASSWORD must be set before this app is exposed publicly")
    return DEFAULT_ADMIN_PASSWORD


def _throttle(client: str) -> None:
    now = time.time()
    tries = [t for t in _ATTEMPTS.get(client, []) if now - t < WINDOW_SECONDS]
    _ATTEMPTS[client] = tries
    if len(tries) >= MAX_ATTEMPTS:
        wait = int(WINDOW_SECONDS - (now - tries[0])) // 60 + 1
        raise HTTPException(429, f"too many attempts; try again in {wait} minutes")


def _record_failure(client: str) -> None:
    _ATTEMPTS.setdefault(client, []).append(time.time())


class LoginRequest(BaseModel):
    password: str


@app.post("/api/admin/login")
def admin_login(req: LoginRequest, request: Request) -> dict:
    client = request.client.host if request.client else "unknown"
    _throttle(client)
    if not secrets.compare_digest(req.password, admin_password()):
        _record_failure(client)
        raise HTTPException(401, "wrong password")
    _ATTEMPTS.pop(client, None)
    token = secrets.token_urlsafe(24)
    _SESSIONS[token] = time.time() + SESSION_TTL_SECONDS
    return {"token": token, "default_password": not os.getenv("ADMIN_PASSWORD")}


def require_admin(x_admin_token: str = Header(default="")) -> str:
    if not _session_ok(x_admin_token):
        raise HTTPException(401, "admin session required")
    return x_admin_token


@app.get("/api/admin/check")
def admin_check(_: str = Depends(require_admin)) -> dict:
    return {"ok": True}


# ------------------------------------------------------------------ tablas

@app.get("/api/resources")
def get_resources(include_pending: bool = False,
                  x_admin_token: str = Header(default="")) -> dict:
    """The reading library: real reports, polling, fact-checkers and places to act.

    Items the weekly sweep proposed are hidden until a person approves them,
    so the public page never shows an unreviewed link.
    """
    data = json.loads((DATA / "resources.json").read_text(encoding="utf-8"))
    if not (include_pending and _session_ok(x_admin_token)):
        data["items"] = [i for i in data["items"] if not i.get("pending")]
    return data


MEDIA = {
    "pdf": "application/pdf",
    "pptx": ("application/vnd.openxmlformats-officedocument."
             "presentationml.presentation"),
}


@app.get("/api/export/deck")
def export_deck(lang: str = Query("es", pattern="^(es|en)$"),
                fmt: str = Query("pdf", pattern="^(pdf|pptx)$")) -> FileResponse:
    """The deck as slides: one per card with both faces and its text, in one
    language, preceded by the story.

    Pre-built so the download is instant. Regenerate after minting or editing
    cards with `python export_deck.py --lang both`.
    """
    path = OUTPUT / f"loteria-climatica-{lang}.{fmt}"
    if not path.is_file():
        raise HTTPException(404, f"not generated yet - run: python export_deck.py")
    return FileResponse(path, filename=path.name, media_type=MEDIA[fmt])


@app.get("/api/tablas")
def get_tablas(count: int = Query(6, ge=1, le=20), seed: int | None = None) -> dict:
    """Generate playing boards from the approved deck."""
    ids = [c.id for c in archivista.deck() if c.status != "rejected"]
    out = tablas.generate(ids, count=count, seed=seed)
    names = {c.id: c.name.model_dump() for c in archivista.deck()}
    art = {c.id: render.original_front(c) for c in archivista.deck()}
    out["names"] = names
    out["art"] = art
    out["call_order"] = tablas.call_order(ids, out["seed"])["order"]
    return out


# ------------------------------------------------------------------ models

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list, max_length=40)
    channel: str = "web"
    user: str = "web-anon"


class ContraRequest(BaseModel):
    material: str = Field(min_length=1, max_length=20000)
    defend: bool = True
    user: str = "web-anon"


class MintRequest(BaseModel):
    claim: str = Field(min_length=1)
    gap_id: str | None = None
    audience: str = "general mixed audience"


# ------------------------------------------------------------------- deck

@app.get("/api/health")
def health() -> dict:
    deck = archivista.deck()
    return {
        "ok": True,
        "model": MODEL,
        "cards": len(deck),
        "generated": sum(1 for c in deck if c.provenance == "generated"),
        "adapters": adapters.available(),
        # True on a fresh clone, where ADMIN_PASSWORD is unset and the default
        # applies. The gate uses this to show the password to whoever is
        # evaluating the project; it disappears the moment a real one is set.
        "admin_default": not os.getenv("ADMIN_PASSWORD"),
    }


@app.get("/api/deck")
def get_deck(category: str | None = None, provenance: str | None = None) -> dict:
    tools.refresh()
    out = []
    for c in archivista.deck():
        if category and c.category != category:
            continue
        if provenance and c.provenance != provenance:
            continue
        out.append({
            "id": c.id, "number": c.number, "slug": c.slug,
            "name": c.name.model_dump(), "category": c.category,
            "provenance": c.provenance, "status": c.status,
            "frame": c.frame.frame if c.frame else None,
            "art": render.original_front(c),
        })
    cats = sorted({c.category for c in archivista.deck()})
    return {"count": len(out), "categories": cats, "cards": out}


@app.get("/api/cards/{card_id}")
def get_card(card_id: str) -> dict:
    for c in archivista.deck():
        if c.id == card_id:
            d = c.model_dump()
            d["art"] = render.original_front(c)
            return d
    raise HTTPException(404, f"no card {card_id}")


@app.get("/api/cards/{card_id}/svg")
def card_svg(card_id: str, face: str = Query("front"), lang: str = Query("es")) -> Response:
    for c in archivista.deck():
        if c.id == card_id:
            if face == "front" and c.provenance == "original":
                raise HTTPException(409, "original cards use their printed artwork")
            return Response(render.render(c, face, lang), media_type="image/svg+xml")
    raise HTTPException(404, f"no card {card_id}")


# ------------------------------------------------------------------- lanes

@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    return await comadre.ask(
        req.message, history=req.history,
        channel=req.channel, user_ref=pseudonym(req.user),
    )


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list, max_length=40)
    channel: str = "web"
    user: str = "web-anon"


@app.post("/api/ask")
async def ask(req: AskRequest) -> dict:
    """One surface, two agents.

    La Comadre explains it to you; La Contra builds the message you send back.
    They are independent, so they run concurrently and the answer carries both.
    A short question gets only the explanation -- there is nothing to reply to
    yet, and the counter-message pipeline costs eight times as much.
    """
    user_ref = pseudonym(req.user)
    looks_forwarded = (
        len(req.message) > 220
        or any(k in req.message.lower() for k in
               ("reenv", "forward", "pásalo", "pasalo", "comparte", "compartan",
                "urgente", "whatsapp", "*", "🙏"))
    )

    if not looks_forwarded:
        out = await comadre.ask(req.message, history=req.history,
                                channel=req.channel, user_ref=user_ref)
        return {"mode": "question", "explanation": out, "counter": None}

    explanation, counter = await asyncio.gather(
        comadre.ask(req.message, history=req.history,
                    channel=req.channel, user_ref=user_ref),
        contra.counter(req.message, defend=True, user_ref=user_ref,
                       channel=req.channel),
    )
    return {"mode": "forward", "explanation": explanation, "counter": counter}


@app.post("/api/contra")
async def contra_route(req: ContraRequest) -> dict:
    return await contra.counter(
        req.material, defend=req.defend, user_ref=pseudonym(req.user),
    )


@app.post("/api/whatsapp")
async def whatsapp(payload: dict) -> dict:
    """WhatsApp Business webhook -- built and tested against synthetic payloads.

    Going live needs a Twilio or Meta number, whose credentials are outside the
    key names this project is allowed to use, so the route is deliberately
    unwired. The lane below is the same one the website calls: one brain,
    several doors.
    """
    body = (payload.get("Body") or payload.get("text") or "").strip()
    sender = payload.get("From") or payload.get("from") or "wa-unknown"
    if not body:
        raise HTTPException(400, "no message body")
    out = await comadre.ask(body, channel="whatsapp", user_ref=pseudonym(sender))
    return {"reply": out["text"], "cards": out["cards"]}


# ---------------------------------------------------------------- el taller

@app.get("/api/taller/stream")
async def taller_stream(claim: str, gap_id: str | None = None,
                        token: str = Query("")) -> StreamingResponse:
    # EventSource cannot set headers, so the token travels as a query param.
    if not _session_ok(token):
        raise HTTPException(401, "admin session required")
    """Mint a card and stream the mesh working: the live dashboard."""
    queue: asyncio.Queue = asyncio.Queue()

    async def run_mint():
        try:
            card = await taller.mint(claim, gap_id=gap_id, queue=queue)
            archivista.save(card)
            tools.refresh()
            if gap_id:
                ledger.mark_minted(gap_id, card.id)
            await queue.put({"type": "card", "data": card.model_dump()})
        except Exception as exc:
            await queue.put({"type": "error",
                             "data": {"error": f"{type(exc).__name__}: {exc}"}})
        finally:
            await queue.put(None)

    async def stream():
        task = asyncio.create_task(run_mint())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield sse(item)
        finally:
            task.cancel()

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.post("/api/taller/approve/{card_id}")
def approve(card_id: str, by: str = "Juan Pablo Alvarado",
            _: str = Depends(require_admin)) -> dict:
    card = archivista.approve(card_id, by)
    if not card:
        raise HTTPException(404, f"no card {card_id}")
    tools.refresh()
    return {"id": card.id, "status": card.status, "approved_by": card.approved_by}


# ------------------------------------------------------------- gaps + brief

@app.get("/api/gaps")
def get_gaps(_: str = Depends(require_admin)) -> dict:
    found = gaps.detect()
    return {
        "cadence": gaps.cadence(),
        "min_distinct_conversations": gaps.MIN_DISTINCT_CONVERSATIONS,
        "gaps": [g.model_dump() for g in found],
        "mintable": [g.gap_id for g in gaps.mintable()],
    }


@app.get("/api/boletin")
def get_boletin() -> dict:
    path = DATA / "boletin_latest.json"
    if not path.is_file():
        raise HTTPException(404, "no brief generated yet")
    brief = json.loads(path.read_text(encoding="utf-8"))
    brief["source_note"] = junkipedia.status_note()
    return brief


@app.post("/api/boletin/generate")
async def generate_boletin(adapter: str | None = None,
                           _: str = Depends(require_admin)) -> dict:
    brief = await boletin.build_brief(adapter)
    return brief.model_dump()


# -------------------------------------------------------------- the list

class SubscribeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    zip: str = Field(default="", max_length=12)
    phone: str = Field(default="", max_length=32)
    lang: str = "es"
    sms_consent: bool = False
    consent_text: str = Field(min_length=1)


@app.post("/api/subscribe")
def subscribe(req: SubscribeRequest) -> dict:
    """Join the list. Consent wording and timestamp are stored with the row."""
    try:
        out = subscribers.subscribe(
            req.name, req.email, req.zip, req.phone, req.lang,
            req.sms_consent, req.consent_text,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"ok": True, "status": out["status"],
            "unsubscribe": f"/api/unsubscribe?token={out['token']}"}


@app.get("/api/unsubscribe")
def unsubscribe(token: str) -> dict:
    """One click, real delete. No login, no 'are you sure'."""
    return {"ok": subscribers.unsubscribe(token)}


@app.get("/api/admin/subscribers")
def list_subscribers(_: str = Depends(require_admin)) -> dict:
    return {"stats": subscribers.count(), "rows": subscribers.rows()}


@app.get("/api/admin/subscribers.csv")
def export_subscribers(_: str = Depends(require_admin)) -> PlainTextResponse:
    return PlainTextResponse(
        subscribers.to_csv(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=subscribers.csv"},
    )


@app.get("/api/admin/sending")
def sending_status(_: str = Depends(require_admin)) -> dict:
    """Whether any send channel is connected, and what each one still needs."""
    return senders.status()


@app.get("/api/admin/audience")
def get_audience(channel: str = Query("email", pattern="^(email|sms)$"),
                 lang: str | None = None,
                 _: str = Depends(require_admin)) -> dict:
    """The people a send may actually reach on this channel.

    Sending is deliberately not implemented here: an email or SMS blast needs
    a provider account whose key names this project is not allowed to use.
    This endpoint produces the audience so an approved provider can be handed
    exactly the right list -- and nobody who did not consent to that channel.
    """
    people = subscribers.audience(channel, lang)
    return {"channel": channel, "lang": lang, "count": len(people), "people": people}


# ------------------------------------------------------------- tokenomics

@app.get("/api/pricing")
def pricing() -> dict:
    return {"model": MODEL, "prices_per_1m_tokens": PRICES, "source": PRICE_SOURCE}


@app.get("/api/stats")
def stats() -> dict:
    """Measured spend across every run in the audit trail."""
    path = OUTPUT / "audit_trail.json"
    runs = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    by_lane: dict[str, dict] = {}
    by_agent: dict[str, float] = {}
    for run in runs:
        lane = run.get("lane") or "unknown"
        usage = run.get("usage") or {}
        bucket = by_lane.setdefault(lane, {"runs": 0, "usd": 0.0, "calls": 0})
        bucket["runs"] += 1
        bucket["usd"] += usage.get("total_usd", 0.0)
        bucket["calls"] += usage.get("calls", 0)
        for agent, u in (usage.get("agents") or {}).items():
            by_agent[agent] = by_agent.get(agent, 0.0) + u.get("cost_usd", 0.0)

    for bucket in by_lane.values():
        bucket["usd"] = round(bucket["usd"], 6)
        bucket["avg_usd_per_run"] = round(bucket["usd"] / max(1, bucket["runs"]), 6)

    chat = by_lane.get("comadre", {}).get("avg_usd_per_run", 0.0)
    return {
        "runs": len(runs),
        "by_lane": by_lane,
        "by_agent": {k: round(v, 6) for k, v in sorted(by_agent.items())},
        "total_usd": round(sum(b["usd"] for b in by_lane.values()), 6),
        "projection_chat": project_costs(chat) if chat else None,
        "conversations_last_7_days": ledger.count_since(7),
    }
