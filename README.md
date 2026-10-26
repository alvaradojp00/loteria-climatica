# Lotería Climática

A climate-disinformation defense system built around a bilingual lotería deck.
People ask it about the claims reaching their family; what the deck cannot
answer becomes a measured gap; a mesh of agents manufactures the missing card,
routed through **value frames that were measured on this exact audience** by a
randomised message test.

Juan Pablo Alvarado · MGT 409, AI Foundations for Managers · Yale SOM

---

## What it does

| Surface | What it is |
|---|---|
| **La Lotería** | The deck. 12 original campaign cards plus 42 manufactured by the system, each with myth, evidence-backed truth, action, and its own provenance. |
| **Pregúntale** | One surface, two agents. La Comadre explains what the evidence says; La Contra builds the reply you can send. Paste a forward and both run; ask a question and only La Comadre does. |
| **El Boletín** | A fortnightly brief: what is circulating, the tactic behind it, and a prebunk line you can say before it reaches you. |
| **Jugar** | Six printable boards (one page each), the printable deck, and the deck as slides in either language. |
| **Recursos** | A filterable library of real reports, polling and fact-checkers — every link to a specific page. |
| **La Historia** | The project's story, with photographs from the campaign. |
| **El Taller** | *Operator only, password-gated at `#taller`.* The factory, live: six agents and two rejection gates, with per-agent spend meters. |

Every conversation writes a pseudonymous row to a demand ledger. A deterministic
gap detector scores topics the deck cannot answer, and a cadence gate decides
whether the factory runs weekly or monthly.

---

## Run it

Requires **Python 3.12+** and **Node 18+**. Two terminals.

### 1. Key

Copy `.env.example` to `.env` in this folder and fill in `PORTKEY_API_KEY`.
**Every other key in that file is optional and unused by default** — the app
runs fully on the course key alone.
The app looks in this folder first, then one level up, then the course root —
so an existing course `.env` already works.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt     # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux
.venv/Scripts/python.exe -m uvicorn main:app --port 8010
```

API docs at http://127.0.0.1:8010/docs · health at `/api/health`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

> Port 8010 rather than 8000 to avoid colliding with other course projects.
> To change it, set `VITE_API_URL` for the frontend and pass `--port` to uvicorn.

---

## Hosting

See **[DEPLOY.md](DEPLOY.md)** — Render blueprint in `render.yaml`, about
$7.25/month. The one thing that needs care: this app writes to disk while it
runs (subscribers, the ledger, newly minted cards), and Render's filesystem is
ephemeral, so a persistent disk is required or the subscriber list is lost on
every deploy. `DATA_DIR` and `OUTPUT_DIR` handle it.

## Data

The deck ships built, so the app works immediately. To rebuild any of it:

```bash
cd backend
python -m agents.genesis                 # re-extract the 12 originals from the print art
python make_web_art.py                   # web-sized card images (44 MB -> 2.4 MB)
python -m agents.batch                   # mint the generated cards (skips existing)
python -m agents.boletin --adapter fixture
python -m experiments.injection_demo     # the safety before/after
python gaps.py                           # gap scores and the cadence gate
python export_deck.py --lang both        # slide deck: PPTX + PDF, es and en
python -m agents.rework --copy 19 --reframe   # rework a held card
```

`export_deck.py` rasterises every card face through headless Chromium (the same
SVG the site renders) and writes four files to `output/`:
`loteria-climatica-{es,en}.{pptx,pdf}`. The PDF is generated directly rather
than converted from the PPTX, so no Office install is needed.

`backend/data/cards.json` is the deck. `backend/data/frames.json` holds the
measured persuasion data. `output/audit_trail.json` accumulates every run.

### Small vs full dataset

`El Boletín` reads whichever ingest adapter is available:

- **`fixture`** — a committed two-week sample. No network, no credentials. This
  is what runs out of the box and what the teaching staff will see.
- **`open`** — live Spanish-language fact-check and news feeds. No credentials.
- **`junkipedia`** — the real monitoring platform. Built and tested; dormant
  because the account lacks the API entitlement (see `adapters/junkipedia.py`).

Force one with `python -m agents.boletin --adapter open`.

---

## Model and cost

Everything runs on **gpt-6-luna** through Portkey. Measured, not estimated:

| Lane | Cost per run |
|---|---|
| La Comadre (one conversation turn) | ~$0.0005 |
| La Contra (one counter-message) | ~$0.004 |
| El Taller (one finished card) | ~$0.008 |

`GET /api/stats` reports measured spend per lane and per agent across every run
in the audit trail. `GET /api/pricing` returns the price table and its source.

---

## Architecture

A cheap router over four lane bosses, drawing on **one shared specialist pool**
and **two shared gates** — a hierarchy of control with a service mesh beneath it.

```
            El Despachador (choice model: a lane and a confidence)
                                 |
     Comadre ---- Contra ---- Maestra ---- Editor
         \           \           /            /
          \_______ shared pool ______________/
            researcher · framer · tactic analyst
            extractor · transcreator · artist
                         |
                 shared gates (reject upward)
                 verifier  ·  visual QA
                         |
            La Archivista (deterministic deck custodian)
```

Deliberately **not** agents: the gap detector, the cadence gate, clustering,
the card renderer, the Archivista, budget enforcement. The card template is why
generated cards look like the deck — only the central motif is model output.

Prompts live in `backend/prompts/*.md` and can be edited without touching code.

---

## Operator access

El Taller is not public. Two ways in:

- **Operador** — a small link at the foot of every public page.
- `http://localhost:5173/#taller` directly.

**The password on a fresh clone is `loteria-admin`.** `ADMIN_PASSWORD` is read
from `.env`, which is gitignored, so a clone has no value set and falls back to
that default — the gate prints it on screen when the default is in use, and the
notice disappears by itself once a real password is set.

Hiding the URL is not a security control, so the door is allowed to be
findable and the lock is made to hold instead: failed logins are throttled to
**5 attempts per client per 15 minutes**, and the gate reports which of the two
problems you have — a wrong password, or a lockout.

That default is local-only by construction. `ALLOWED_ORIGINS` is set exactly
when the app has been pointed at a real frontend, so once it is present an
unset `ADMIN_PASSWORD` **fails closed with a 503** and the default stops being
accepted at all. A fresh clone on your laptop sets no origins, so it keeps
working; a deploy cannot inherit the password printed above. Sessions expire
after **8 hours**.

It asks for a password, which is `ADMIN_PASSWORD` in `.env` (default
`loteria-admin` when unset — change it). The session token is held in the
browser and in server memory, so restarting the backend signs everyone out.

Once signed in, an **El Taller** tab appears in the navigation (orange, with a
dot) so you can move between the public pages and the operator area without
retyping the address. It is only rendered while a valid session exists, and
**Salir** signs out and removes it.

Behind it:

- **The list** — subscriber counts, a CSV export, and an audience builder that
  returns only the people who consented to that channel.
- **The gap queue** with live scores and the weekly/monthly cadence gate.
- **The factory** — mint a card and watch the agents work, with spend meters.
- **Approvals** for cards and for anything the weekly librarian sweep proposed.

Everything here is gated server-side, not merely hidden in the interface.

### Sending

Email and SMS are built as dormant plug-ins, the same way the Junkipedia
adapter is: `backend/senders.py` knows what each channel needs and reports its
own status, but no provider call is wired. With the keys unset, the workflow is
manual — download the CSV for a channel and send from your own tool.

To connect one later, set its keys in `.env` and write the provider call in
`senders.py`. Nothing else changes: the audience builder already decides who
may be contacted, and excludes anyone who did not opt in to that channel.

| Channel | Needs | Also required before sending |
|---|---|---|
| Email | `EMAIL_API_KEY`, `EMAIL_FROM` | A domain with SPF and DKIM; an unsubscribe link in every send; a postal address in the footer |
| SMS | `SMS_ACCOUNT_SID`, `SMS_AUTH_TOKEN`, `SMS_FROM` | A number and A2P 10DLC brand/campaign registration; "Reply STOP" honoured automatically |

## Safety

Three threats, handled and documented in the report:

1. **Indirect prompt injection** — everything pasted or fetched is wrapped in an
   untrusted-material boundary and treated as evidence. `experiments/injection_demo.py`
   runs three escalating attacks and records what happened.
   *Note: the boundary is phrased affirmatively on purpose — a negation-phrased
   version ("this is not instruction") trips Azure's Prompt Shield and fails closed.*
2. **Deck poisoning** — a card cannot be minted from fewer than 3 distinct
   conversations, evidence is required, and nothing publishes without human approval.
3. **Overspending** — a hard per-run `BudgetExceeded` cap that agents cannot
   talk past.

---

## Attribution

Cards 1–12 were created by **Juan Pablo Alvarado as Program Manager at
GreenLatinos**, in partnership with Intersectional Environmentalist, and are
shown here with attribution and their original artwork. The agent system, the
expanded deck, the generated cards and this application are independent work.

Generated cards deliberately carry no GreenLatinos wordmark.

Not affiliated with or endorsed by GreenLatinos, CAAD, Friends of the Earth,
Climate Power or Resource Media.

---

## Repo layout

```
backend/
  main.py          thin routes      config.py   gateway, budget
  models.py        typed handoffs   pricing.py  measured token cost
  events.py        async queue -> SSE
  tools.py         the shared tool library
  ledger.py  gaps.py  archivista.py  render.py   (all deterministic)
  adapters/        fixture · open_sources · junkipedia
  agents/          despachador comadre contra taller boletin genesis pool gates
  prompts/         one markdown file per agent
  data/            cards.json frames.json sources.json tactics.json
frontend/          React + Vite + TypeScript
assets/            original card art, print masters, web-sized copies
output/            audit_trail.json, briefs, rendered cards
```
