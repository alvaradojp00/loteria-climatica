# Deploying Lotería Climática

Follows Lecture 8's pattern — Render for both halves, backend first because
the frontend needs its URL — with the differences this app actually has.

---

## What makes this app different from the lecture example

**It writes to disk while it runs.** Not just logs:

| What | Written by | Losing it means |
|---|---|---|
| `subscribers.db` | every signup | **people's contact details, gone** |
| `ledger.db` | every chat turn | the demand signal the factory runs on |
| `cards.json` | El Taller minting | new cards vanish |
| `resources.json` | the weekly librarian | staged finds vanish |
| `boletin_latest.json` | the brief | the published brief vanishes |
| `audit_trail.json` | every run | the tokenomics evidence for the report |

Render's filesystem is **ephemeral**: it resets on every deploy and restart. So
a plain deploy quietly loses subscriber data, which is the one kind of loss
that is not recoverable and not yours to lose.

**The fix is one line of config, not a rewrite.** `DATA_DIR` and `OUTPUT_DIR`
move all of it onto a mounted disk. `render.yaml` already sets them.

---

## 1. Push to GitHub

```bash
cd "Final Project"
git init && git add -A
git commit -m "Lotería Climática"
gh repo create loteria-climatica --public --source=. --push
```

`.gitignore` already excludes `.env`, the venv, `node_modules` and the 450 MB
of print masters. The repo is about **4 MB**.

Confirm before pushing:

```bash
git ls-files | grep -i "\.env$"     # must print nothing
```

## 2. Backend — Render Web Service

New → Web Service → connect the repo.

| Field | Value |
|---|---|
| Root directory | `backend` |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/api/health` |
| Instance type | **Starter ($7/mo)** |

`--host 0.0.0.0` and `$PORT` are both required — Render assigns the port and
nothing outside the container can reach `127.0.0.1`.

**Take Starter, not Free.** Free instances spin down after ~15 minutes idle and
cold-start in 30–60 seconds. A grader opening a sleeping site sees a hang, and
the rubric gives zero for "the teaching staff can run it" if the app is not up
within ten minutes.

### Add a disk

Settings → Disks → Add: name `loteria-data`, mount `/var/data`, **1 GB**
(~$0.25/mo). Without it the table above is lost on every deploy.

### Environment variables

| Key | Value |
|---|---|
| `PORTKEY_API_KEY` | your course key |
| `ADMIN_PASSWORD` | a real one — otherwise the default is live on the public internet |
| `DATA_DIR` | `/var/data/data` |
| `OUTPUT_DIR` | `/var/data/output` |
| `ALLOWED_ORIGINS` | the frontend URL, once step 3 gives you one |
| `JUNKIPEDIA_API_KEY` | only if the entitlement comes through |

## 3. Frontend — Render Static Site

New → Static Site → same repo.

| Field | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |
| Env var | `VITE_API_URL` = the backend URL from step 2 |

Add a rewrite rule `/*` → `/index.html`, or deep links 404.

`VITE_API_URL` is read **at build time**, not at runtime — changing it means
redeploying the frontend.

Static sites are free.

## 4. Close the loop

Go back to the backend and set `ALLOWED_ORIGINS` to the static site's URL.
Until you do, the browser blocks every API call and the site looks broken
while the backend looks healthy.

## 5. Scheduled work

Uncomment the `jobs:` block in `render.yaml`, or add two Cron Jobs by hand:

| Job | Schedule | Command |
|---|---|---|
| El Boletín | `0 13 * * 1` | `python -m agents.boletin` |
| La Bibliotecaria | `0 14 * * 1` | `python -m agents.librarian` |

Both need the same env vars and the same disk mount.

---

## Running cost

| Item | Monthly |
|---|---|
| Backend, Starter | $7.00 |
| Disk, 1 GB | $0.25 |
| Static site | $0 |
| Cron jobs | pennies |
| Model usage | ~$0.0005 per chat turn, ~$0.008 per card |

About **$7.25/month**, plus whatever the model does.

---

## What NOT to deploy

`export_deck.py` and `make_web_art.py` need Playwright and a Chromium
download (~120 MB). They are build-time tools: run them locally and commit the
output. Keeping them out of the web service keeps the image small and the
deploy fast.

---

## Before it is public

- [ ] `ADMIN_PASSWORD` set on Render — the default is in the README and this repo
- [ ] `ALLOWED_ORIGINS` set to the real frontend URL
- [ ] Disk mounted, so subscriber data survives
- [ ] Open `/api/health` and confirm `admin_default` is `false`
- [ ] Sign up once yourself, redeploy, confirm you are still in the list
- [ ] Decide what you owe the people on that list: where their data lives, who
      can see it, and how they get removed. The unsubscribe route exists; a
      privacy note for the footer does not yet.

---

## Next, if you want it (Lecture 9)

The agents are already a toolbox — `search_cards`, `search_sources`,
`list_tactics`, `get_frame_guidance`. Wrapping them in **FastMCP** would let
Claude, Codex or any MCP client query the deck directly:

```python
from fastmcp import FastMCP
mcp = FastMCP("loteria-climatica")

@mcp.tool
def search_cards(query: str, lang: str = "es") -> str:
    """Search the Lotería Climática deck for cards answering a climate claim."""
    ...
```

The logic already exists in `backend/tools.py`; only the wiring changes, which
is the point Lecture 9 makes. That turns the deck from a website into something
other people's agents can use — a reasonable "next steps" line for the report,
and genuinely useful if any partner organisation ever wanted to build on it.
