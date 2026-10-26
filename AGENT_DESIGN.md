# Agent architecture — Lotería Climática

## 0. Two governing decisions

**The deck is an output, not an input.** We do not carry over a pre-authored 54-card file. We seed from the **12 real cards** — their art, their myths, their truths, extracted from the print files and the GreenLatinos page — and every card after #12 is **manufactured by the agents, on the record, from measured demand.** This is strictly better for the project: the deck becomes the proof that the system works rather than the content the system decorates. A grader can watch card #13 come into existence.

**Lean where the job is one role, mesh where it genuinely isn't.** Lecture 10 says one agent is enough when the job fits a single role and context. The rubric rewards *thoughtful* design, not maximal design. So the chat path is one agent and the manufacturing path is a mesh, and the report explains the difference with numbers.

---

## 1. The hierarchy

Three tiers and a shared services layer. The thing that makes it smart is the third column: **specialists are a pool, not copies.** Four bosses call the same Researcher, the same Verifier, the same Framer. One standard, one place to fix a bug, one prompt to improve.

```
TIER 0                      EL DESPACHADOR  (router)
                      cheap classifier → picks a lane, with confidence
                                    │
        ┌───────────────┬───────────┴────────┬──────────────────┐
TIER 1  │               │                    │                  │
     COMADRE      CONTRA BOSS            MAESTRA          EDITOR (Boletín)
    (converse)   (counter a forward)   (make a card)    (biweekly brief)
        │               │                    │                  │
        └───────────────┴─────────┬──────────┴──────────────────┘
                                  │  all four draw from:
TIER 2                  ╔═════════▼══════════════════════════════╗
                        ║        SHARED SPECIALIST POOL          ║
                        ║  Researcher    — evidence + citations  ║
                        ║  Framer        — Grow Progress routing ║
                        ║  Tactic analyst— names the manipulation║
                        ║  Extractor     — vision → structured   ║
                        ║  Transcreator  — EN↔ES, register-true  ║
                        ║  Artist        — motif SVG only        ║
                        ╚═════════╤══════════════════════════════╝
                                  │
TIER 3                  ╔═════════▼══════════════════════════════╗
                        ║     SHARED GATES (can reject upward)   ║
                        ║  Verifier   — every number traceable   ║
                        ║  Visual QA  — style conformance        ║
                        ╚════════════════════════════════════════╝

              ARCHIVISTA (deterministic service, not an agent)
        owns the deck: read, match, dedupe, version, publish-on-approval
```

### Why this is the smart version

- **The router is a choice model, not an essay model.** Lecture 11's last cost-cutting technique: *for decisions, use models that return a pick and probabilities instead of long text.* El Despachador returns `{lane, confidence}` and nothing else. It's the cheapest call in the system and it runs on every request. If confidence is low it defaults to Comadre, which is the safe lane.
- **Shared specialists are the real architecture.** Four pipelines each with their own private researcher would be four prompts drifting apart. One Researcher, called by all four, means the Boletín and El Taller cite evidence to the same standard. This is also the honest answer to "is this a hierarchy or a mesh?" — it is a hierarchy of control with a **shared service mesh underneath**, which is exactly how real org charts work and is worth saying in those words.
- **Gates reject upward across pipeline boundaries.** The Verifier can fail a Contra draft *and* a Taller card *and* a Boletín topline. One guardrail, three enforcement points.
- **The Archivista is not an agent.** Deck reads, dedupe and versioning are deterministic. Keeping it out of the model layer is why the deck can't be corrupted by a bad generation.

### Delegation contract

Every boss→specialist call is one async tool with a uniform envelope, the Lecture 10 pattern:

```python
async def ask_specialist(role: str, task: str, context: dict) -> SpecialistReport
# SpecialistReport: {role, status, findings, citations, confidence, usage}
```

Bosses synthesize **only** from `SpecialistReport`s. A boss that states a fact not present in a report is a bug the Verifier catches.

---

## 2. Pipeline E — **Génesis** (runs once, first)

This is new, and it replaces "copy the deck over."

**Job:** turn the 12 original cards into structured, bilingual, verified data — using our own agents.

```
for each of the 12 cards, EN and ES:
   Extractor (vision)  ─ reads the card FRONT  → number, name, motif description, palette
                       ─ reads the card BACK   → myth text, truth headline, body paragraph
   Archivista          ─ cross-checks against the GreenLatinos page text
   Transcreator        ─ reconciles EN/ES pairs, flags any mismatch for review
   Verifier            ─ every extracted number must appear in the source image
   → cards.json  (seed deck, 12 cards, marked provenance: "original")
```

**Why this earns points rather than costing time:**
- It is **Lecture 5's exact pattern** — define the output fields first, then extract structured data from an image — and vision is otherwise unrepresented in this project.
- It produces the **style corpus** the Artist and Visual QA need: the real palettes, stroke weights, horizon seams and type treatment, measured from the originals instead of described by me.
- It makes provenance explicit in the data: `provenance: "original" | "generated"`, with `created_by`, `frame`, `evidence[]`, `approved_by` on every generated card. The deck itself becomes the audit trail.
- Twelve cards × 2 languages × 2 faces is a bounded, cheap, parallelizable run that will finish in minutes.

**Deliverable of Génesis:** `data/cards.json` with 12 verified cards, and `data/style_profile.json` with the measured visual system.

**Note on deck size:** we do not promise 54. The site ships the 12 originals plus however many the system genuinely manufactures and you approve before Monday. A deck of 12 + 6 generated, each with its evidence and frame recorded, is worth far more than 54 asserted ones.

---

## 3. The four lanes

### Lane A — La Comadre (conversation) · **1 agent**

Single agent with tools. No boss, no specialists: one role, one context.

| | |
|---|---|
| Model | gpt-6-luna |
| Tools | `search_cards`, `search_sources`, `list_tactics`, `suggest_reading`, `web_search` |
| Memory | conversation history + `user_ref` |
| Stopping | `request_limit=6` |
| Guardrails | never invent a statistic/date/quote/URL; never link a homepage; refuse identification |
| Writes | one ledger row per turn |

**Also a measured experiment.** We build the boss+specialists variant too, run both over the same 20 questions, and report cost per conversation and quality side by side. "We measured it and chose the cheaper architecture" is a stronger section than asserting multi-agent is better.

### Lane B — La Contra (paste a forward) · boss + 4 pooled specialists + 1 gate

Boss → **Extractor** (vision; also the injection tripwire — flags instruction-shaped text and the boss quarantines rather than complies) → **Tactic analyst** and **Researcher** concurrently → drafter in Comadre's voice, frame-routed → **Verifier** gate, one rework, then safe fallback.

### Lane C — El Taller de Cartas (manufacturing) · boss + 5 pooled specialists + 2 gates

**Maestra** → **Researcher** (no evidence, no card) → **Framer** → Writer → **Transcreator** → **Artist** (motif SVG only) → **Verifier** and **Visual QA**, each able to reject, max 2 rework passes, then `needs_human`. Nothing publishes without your approval.

The **Framer** is the agent that makes this project defensible: it selects the value frame from the Grow Progress measured lift and records the chosen lift *and the rejected alternatives* in card metadata — declining the Villain frame for a general audience because the experiment measured −1 overall and −15 with liberals.

### Lane D — El Boletín (scheduled brief) · editor + pooled specialists

Deterministic ingest (`fixture` | `open` | `junkipedia`) → deterministic clustering → **Editor** writes three toplines, each with its tactic and a frame-routed prebunk line → **Verifier**. Gaps found here join the same queue as gaps from the chat ledger. Two demand signals, one factory.

---

## 4. What is deliberately NOT an agent

Restraint is the design signal; give it a paragraph in the report.

- **Gap detector** — `frequency × unanswered_rate × harm_weight × recency` is arithmetic.
- **Cadence gate** — a threshold on a count.
- **Clustering** — embeddings.
- **The card renderer** — a template. *This is why generated cards look consistent rather than AI-made: the look is not a model output.* Only the motif is generated.
- **The Archivista** — deck CRUD, dedupe, versioning.
- **Budget enforcement** — a counter that raises.

---

## 5. Shared core

`agents/config.py` holds the Portkey client, model and budget. One tool library, one deps object:

```python
@dataclass
class Deps:
    queue: asyncio.Queue   # event bus → SSE → UI
    channel: str           # "web" | "whatsapp" | "paste" | "scheduler"
    user_ref: str          # stable, pseudonymous
    lang: str | None       # detected, never assumed
    budget: BudgetTracker  # raises BudgetExceeded
    run_id: str
```

`emit(event_type, **data)`. Event types the UI knows: `routed`, `agent_started`, `agent_done`, `tool_called`, `evidence_found`, `frame_selected`, `qa_rejected`, `rework`, `spend`, `final`, `error`.

New tools beyond the five: `get_frame_guidance(topic, audience?)` (returns measured lift incl. negatives), `ledger_write` / `ledger_query`, `render_card(spec)`.

---

## 6. Harness (name these five — Lecture 4)

| Part | Implementation |
|---|---|
| **Tools** | shared library; name + docstring are the instruction manual |
| **Memory** | short: history, tool observations. long: `cards.json`, `sources.json`, `style_profile.json`, the SQLite ledger, `prompts/*.md` |
| **Stopping rules** | `request_limit` per agent, max 2 rework passes, `needs_human` terminal state |
| **Guardrails** | untrusted-content boundary on all external text; no-fabrication enforced by the Verifier; frame allow-list from measured data; min-distinct-conversations before minting; human approval before publish |
| **Audit trail** | `output/audit_trail.json`, appended per run — thoughts, tool calls, rejections, tokens, cost |

---

## 7. Cost controls (Lecture 11)

- **Prompt caching** — stable instructions + the deck + tactic taxonomy + style profile first, then `prompt_cache_breakpoint`; per-run evidence after it.
- **Choice model at the router** — a pick and a confidence, not prose, on the highest-frequency call.
- **Per-agent spend meters** — the shared pool makes this interesting: you can show Researcher cost attributed across all four lanes.
- **Hard budget** — `BudgetExceeded` per run and per day.
- **Concurrency where it's free** — Lane B's analysts; Lane C's Artist alongside the Writer.
- **Real cache fields only** — `cached_tokens`, `cache_write_tokens` from the Responses API.

**On intelligence allocation:** the course key is gpt-6-luna only, so model-tier routing cannot be demonstrated on it. Express allocation through **context and tool budgets** instead (the Maestra gets a tiny prompt and no search tools; Writer and Transcreator get the cached style corpus and the most steps), say so plainly, and run **one** comparison card on your own `OPENAI_API_KEY` against a stronger model for the delta. A few cents turns a constraint into a measured finding.

---

## 8. File layout

```
final-project/
  .env.example   README.md
  backend/
    main.py  config.py  models.py  pricing.py  events.py
    ledger.py  gaps.py  render.py  archivista.py
    adapters/     fixture.py  open_sources.py  junkipedia.py
    agents/       despachador.py  comadre.py  contra.py  taller.py
                  boletin.py  genesis.py  pool.py  gates.py
    prompts/      despachador.md  comadre.md  extractor.md  tactic.md
                  researcher.md  framer.md  writer.md  transcreator.md
                  artist.md  verifier.md  visual_qa.md  editor.md
    data/         cards.json  sources.json  frames.json  style_profile.json
  frontend/
  output/         audit_trail.json
```

---

## 9. Build order

1. **Spine** — `models.py`, `pricing.py`, `events.py`, `config.py`, `frames.json` (Grow Progress lifts).
2. **Génesis** — Extractor over the 12 cards → `cards.json` + `style_profile.json`. Nothing downstream is real until this is.
3. **`render.py` + card template** — prove a generated card sits convincingly beside card 01 **before** building the agents that feed it. This is the project's biggest risk; retire it Saturday.
4. **Lane A** + ledger writes. Something works end-to-end early.
5. **Lane C** with both gates. The showcase.
6. `gaps.py` + cadence gate.
7. **Lane B**, then **Lane D** on fixture + open.
8. Frontend: deck, chat, La Contra, El Taller live stream, Boletín, Resources.
9. The chat A/B cost experiment, the injection demo, the pilot.
