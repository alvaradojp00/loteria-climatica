# MGT 409 Final Project — Brief

Source: https://zlisto.github.io/mgt_409_fa26/ (requirements, lectures, instructions, grading)
Compiled 2026-10-24.

## 1. The hard facts

- **Due:** Mon Oct 26, 2026, 6:00 PM, Canvas. **Solo.**
- **Weight:** 50% of the course grade (attendance 10%, homework 40%).
- **Deliverables:**
  1. GitHub repo link on Canvas — all app code, README with run instructions, `.env.example` with key *names* only. Public, or private with `zlisto` added as collaborator.
  2. `report.html` — self-contained, 10–15 printed pages, opens by double-click, screenshots embedded (base64).
  3. `slides.html` — self-contained reveal.js, **max 10 slides**.
  4. Demo video (optional) — 2–3 min screen recording.
- **Repo rules:** never commit a real `.env` or the key. App must look for `.env` in its own repo folder **first**, then one level above. Only key names `PORTKEY_API_KEY` / `OPENAI_API_KEY`. Big dataset → ship a small test dataset plus a README toggle.
- **Model:** course key = `PORTKEY_API_KEY`, gpt-6-luna only. Any other model = own `OPENAI_API_KEY`, own money.
  - **Resolved:** the course moved model families mid-semester. Lectures 1–7 use the **gpt-5.6** family (luna $0.20 / terra $2 / sol $5 in). Lectures 11+ and the project page use the **gpt-6** family. Our AGENTS.md still says `gpt-5.6-luna` — the final project wants **`gpt-6-luna`**. Verify the gateway accepts it on day one (our Portkey key is Azure-pinned), and update AGENTS.md if it does.
- **Testing:** either host it online (link in README and report, up until grades post) **or** it runs locally from a fresh clone via the README. **Not running within 10 minutes of following the README = 0 for "teaching staff can run it."**

## 2. Grading (100 pts) — where the points actually are

| Bucket | Row | Pts |
|---|---|---|
| Idea | Novelty and real-world value | **21** |
| App | It works | **15** |
| App | Teaching staff can run it | 5 |
| App | Look and feel | 10 |
| Report | Motivation / what is new | 8 |
| Report | Agent design | 10 |
| Report | Tokenomics | 8 |
| Report | Safety | 8 |
| Report | Impact and metrics | 5 |
| Report | Design | 2 |
| Slides | Content | 6 |
| Slides | Design | 2 |

**Idea (21) + works (15) = 36% of the grade.** The idea is the single biggest line item, and the one thing that cannot be fixed at the end.

### Tiers
- **Tier 1** — works, familiar idea, report has sections but few real numbers.
- **Tier 2** — plus a new idea or fresh approach, thoughtful agent design, complete report with **measured** costs, a **real** safety defense, screenshots.
- **Tier 3** — plus a clever idea that clearly improves real people's lives and could be used in practice, backed by evidence: user trials, measured time or quality gains.

### The two rules that quietly decide the grade
1. **Overdone ideas are capped at Tier 1** unless there is a real new twist: resume reviewers, chat-with-PDF, trip planners, meeting summarizers, recipe planners, generic study buddies.
2. **Evidence rule — a section without its listed evidence earns at most HALF the row's points:**
   - Motivation / what is new → **named existing products** compared against.
   - Agent design → **one real run traced with screenshots**.
   - Tokenomics → **real token counts from runs**, not estimates.
   - Safety → **a screenshot or test showing a defense working**, not a description.
   - Impact → **a real user's quote, screenshot, or before/after time**, not guesses.

   That is 39 report points, of which about 19.5 are forfeitable purely by missing artifacts. The cheapest points in the project — collect the artifacts *while* building, not after.

## 3. Report structure (use this order exactly)

1. Title and links: project name, name, repo link, app link, one-sentence description.
2. Motivation: who has the problem, current cost in money / time / frustration.
3. What is new: named alternatives, what is different, honest comparison.
4. The agents: each agent's role, tools, organization and handoffs **(diagram)**, model choices, one step-by-step run with screenshots.
5. Tokenomics: measured input / cached / output tokens per run; cost per run, per user per month, at 100 users and at 10,000 users; cost-cutting steps and their performance effects.
6. Safety: prompt injection, agent malfunction, overspending — defenses built, **at least one shown working**.
7. Impact: quantified benefits with sources, ideally a real user.
8. Limits and next steps.

## 4. Slides (max 10, reveal.js)
Title · Problem and audience · What is new · Agent diagram · Demo screenshots · Cost to run · Safety · Impact numbers · Next steps.

## 5. What the course taught — the professor's house style

These are the patterns he grades against. Matching them is free credit on agent design, look and feel, and "teaching staff can run it."

**Lectures:** 1 AI and vibe coding · 2 Structured data from free text · 3 Tools and skills · 4 Agents · 5 Image analysis · 6 Video analysis · 7 Web applications · 8 Deployment · 9 MCP servers · 10 Multi-agent systems · 11 Tokenomics · 12 AI safety · 13 Future directions.

### Agents (Lec 4)
- **PydanticAI**, `pydantic-ai-slim[openai]` (never full `pydantic-ai`), through Portkey.
- Clean separation: `app.py` (lean UI shell, do not redesign), `agent.py` exposing `run_agent(...)`, data file beside them, `requirements.txt`, `.env`.
- Explicit **interface contract**: fixed signature, dict return with `"text"` plus `"tool_events"` (`{"name": ..., "status": "completed"}`).
- **Harness checklist** he expects every agent to have: memory (history plus state), stopping rules (finish condition and max-step cutoff), guardrails (allow-lists, no invented values, refusals), **audit trail** of thoughts / tool calls / observations.
- Dash UI pattern: `dcc.Store` for history and a pending slot, one-shot `dcc.Interval` (250 ms) for the thinking indicator, clientside Enter-to-send / Shift+Enter newline, `host=127.0.0.1, port=8050, debug=False, use_reloader=False`.
- Logging: print the user turn, print tools used (or `(none)`), `traceback.print_exc()` plus a friendly fallback.

### Multi-agent (Lec 10) — the Harry Potter boss/specialist pattern
- **Boss agent** talks to the user and delegates; **specialist agents** answer only from their own evidence and say so when evidence is thin. The boss synthesizes only from specialist reports and never invents facts.
- Handoff is a single async tool, e.g. `ask_book_specialist(id, question)`, returning agent / source / reply / status.
- `asyncio.Queue` event bus plus `emit(event_type, **data)`; fixed SSE event types to the UI (`boss_thinking`, `specialist_started`, `specialist_done`, `final`, `error`) for live progress.
- Module layout: `models.py`, `retrieval.py`, `agents/config.py`, `agents/boss.py`, `agents/specialists.py`, **prompts as editable markdown** in `prompts/*.md`, shared deps object.
- Evidence capped (~40k chars) so a specialist never loads the whole corpus.

### Tokenomics (Lec 11) — exactly how he wants cost reported
- Capture usage per agent key from the Responses API: input, `cache_read_tokens`, `cache_write_tokens`, output. **`input_tokens` is inclusive of cache reads and writes.**
- Pricing used in class (USD per 1M tokens): **gpt-6-luna** $0.10 in / $0.01 cached / $0.125 cache-write / $0.50 out. **gpt-6-astra** $10 / $1 / $12.50 / $50.
- Cost formula: `((input − cache_read − cache_write) × in + cache_read × cached + cache_write × cache_write + output × out) / 1e6`.
- Build `pricing.py` with `cost_usd(model, usage)` and `enrich_usage(model, usage)`.
- Live **spend meters** in the UI (total and per agent), a `spend` event carrying `model`, `budget_usd`, `total_usd`, `agents`.
- Cost-cutting he expects: **prompt caching** (stable instructions first, then a `prompt_cache_breakpoint`, per-question evidence after it), **model routing** (cheap default, expensive on demand), **hard budget cap** raising `BudgetExceeded`, and **real cache fields, never estimates**.

### Safety (Lec 12)
- The demonstrated attacks are **prompt injection via hidden content**: invisible text on a web page, white-on-white text in a PDF. The class assignment was to design a defense and rerun both documents to prove the agent is no longer fooled.
- So the report's safety section should show: the attack landing, the defense added, the attack failing — as screenshots. Plus agent malfunction (stopping rules, allow-lists) and overspending (the budget cap).

### Web app and deployment (Lec 7, 8)
- React + Vite + TypeScript frontend (`frontend/`), FastAPI + uvicorn backend (`backend/` with `main.py` thin routes, `agent.py`, `tools.py`, `models.py`, `prompts/prompt.md`), `data/`, `output/audit_trail.json` appended per run, `.env.example` at root.
- `GET /api/health`, `POST /api/chat` → `{reply, tools_used}`; CORS open for the Vite dev port.
- Deployment: **Render** (Web Service for FastAPI plus Static Site for the frontend), **Supabase** for the DB, secrets as Render env vars.
- Dash is the lighter alternative from Lec 4/5/6 — fine if the app is a single chat surface.

## 5b. The slide decks — the concepts and language he grades in

Read all 13 decks. The vibe pages (§5) are *how* he builds; the slides are *how he thinks*, and the report should speak in this vocabulary.

### The course's thesis (Lec 1)
- "This is Yale SOM's first course with AI in the core. Using AI well is now a core managerial skill."
- **AI-maxxing:** do not bolt AI onto an old workflow — **redesign the workflow**. His examples: replace the spreadsheet with a database AI updates directly; have AI interview every candidate in depth; let AI own the full support loop and escalate only true edge cases.
- **New tech, new paradigm:** early cameras filmed stage plays until cinema emerged. "Aim to design the next paradigm, not a faster version of the old one."
- **Kasparov vs. Jennings:** those who partner with the machine win.
- **Cheap-and-smart frontier:** the set of models where nothing cheaper scores higher. He ranks Terminal-Bench by *cost per task*, not just score — cheaper is not always weaker.
- He describes the final project as a **"Business AI Co-Pilot that integrates the course modules."**

→ *For us:* the "What is new" section should argue AI-maxxing — the workflow redesigned, not a chatbot bolted onto an existing process. That framing is literally the professor's own thesis and it is worth 21 points.

### Plan before you prompt (Lec 2)
- "Think before you prompt." His planning checklist: project type, structure and flow, data sources, required API keys, packages, styles. **Draw a flow diagram so the AI builds the path you intend.**
- JSON everywhere: "AI models need a strict schema. Without one you get prose instead of usable rows. Complex agentic workflows depend on JSON so data can pass safely between agents."
- Secrets in `.env` + `python-dotenv`; if a key leaks, rotate it immediately.
- `.venv` per project, `requirements.txt`, standard folder layout.

### Tools and skills (Lec 3)
- A **tool** = the Python function + the JSON schema. "The model only *requests* a call. Your software runs it."
- **Build vs. buy framework:** buy hosted tools for commodity capability (web search ~$0.01/call, code interpreter ~$0.03/container, file search $0.0025/call + $0.10/GB-day); **build custom tools for proprietary data and high volume** — custom functions have $0 tool fee. "Default toolboxes are converging, so your edge is custom tools and how you deploy them."
- **Skills** = a playbook in `SKILL.md` (when to use it / steps / house rules / a tiny example). Tools are the appliances; skills are the recipe. `AGENTS.md` is the always-on project handbook, under ~10 pages, one per project.
- Data integrity rule he repeats all term: **never let the model invent numbers** — ground every figure in a tool output.

### The agent harness (Lec 4) — the spine of the agent-design row
- **Chatbot** answers once and stops. **Agent** = tools + memory + a loop.
- Lineage: **Chain of Thought** (2022) → **ReAct** (Thought → Action → Observe), tools inside the reasoning loop.
- **The five parts of the harness** — name these explicitly in the report:
  1. **Tools** — the hands.
  2. **Memory** — short-term (context, observations) and long-term (files, `AGENTS.md`, skills, DB). Bad memory → repetition, contradiction, goal drift.
  3. **Stopping rules** — "hunger" is the goal, "satiation" is the stop condition: `Finish[...]`, max steps, good-enough checks. Without them agents loop and burn tokens.
  4. **Guardrails** — sandboxes, permissions, allow-lists, human approval. **Deterministic guardrails, not "the model will behave."**
  5. **Audit trail** — forensic log of thoughts, tool calls, observations, costs, failures.
- PydanticAI's five pieces: typed output schema, dependencies, the agent (model + output type + deps + system prompt), tools (name + docstring are the instruction manual), and the loop (one `run()` with `request_limit` as the stopping control).
- Cautionary tales he opens with: the 2026 Hugging Face eval agents that drifted from solving to gaming, and the DseWiki swarm that posted ~18,000 messages. **Goal pressure and peer influence push agents past their limits.**

### Vision and video (Lec 5, 6)
- Images are input tokens — a 1024×1024 image ≈ **1,229 tokens**. Per-image cost ≈ tokens × rate.
- Define the output fields *first*, then prompt for extraction. Pattern: **vision tool → structured output → next tool.**
- Privacy guardrails are expected: refuse face identification, stalking, covert recording; keep a permitted-query allow-list.
- Video: sample **10–20 frames**, never every frame; use FFmpeg **scene detection (threshold 0.3)** to cut cost on long clips. Failure modes: sampling too slow, hallucinating the gaps, confident answers on blurry frames.

### Web apps and deployment (Lec 7, 8)
- Keep secrets and heavy compute on the server; the browser is public. React + Vite + TypeScript ↔ FastAPI + uvicorn, JSON over HTTP, CORS configured deliberately. Test the API at `/docs` before wiring a frontend.
- Git/GitHub with a real `.gitignore` (secrets, `.venv`, build output). Deploy the **backend first** — the frontend needs its URL. Render: backend Web Service ~**$7/mo**, static frontend **free**; Supabase for the DB; secrets as host env vars.
- If there are logins: hash with **bcrypt/PBKDF2 + salt**, never plain text.

### MCP (Lec 9)
- MCP is the connectivity layer: tools (actions) + resources (readable facts) + prompts, exposed once and usable by any agent. 10,000+ public servers. **Connect** when a maintained server exists; **build** (FastMCP, `@mcp.tool`) when the system is yours — your catalogue, your inventory, your rules — because then you control what the agent can see and must refuse.
- Memorable line from Lec 1: **"MCP servers are products for AI agents, not for humans."**

### Multi-agent (Lec 10)
- One agent is enough when the job fits one role and one context. Complex work mixes research, ops, writing and judgment — "one agent holding every skill and fact becomes slow and messy."
- **Intelligence allocation "depends on the task":** *smart boss + cheap workers* is the common pattern (Anthropic's Opus-boss/Sonnet-workers beat a single Opus agent by **90.2%** on a board-member search, because the single agent stalled on sequential search); *cheap boss + smart workers* fits generative work like one worker per game level.
- **Topologies: hierarchy (tree)** — boss delegates, workers report, boss combines; **peer-to-peer (mesh)** — workers query each other mid-job.
- Delegation tools are `async`; PydanticAI runs many `await`s in parallel. Actions go to an async queue → streamed to a live dashboard.

### Tokenomics (Lec 11)
- Why tokens cost what they do: GPU supply chain (NVIDIA ~80–90% of accelerator revenue, nearly all fabbed by TSMC; H100 $25–34k, B200 $30–55k; HBM is ~half the GPU cost), power (~1.3–1.7 kW per accelerator all-in; one GPU ≈ one US household; 100k H100s ≈ 150 MW ≈ **$124M/yr**), and water (a 100 MW datacenter ≈ **500,000 gal/day** ≈ 1,500–2,000 homes).
- Societal backlash is on the exam-worthy list: **Gallup 2026, 7 in 10 Americans oppose a nearby AI datacenter**; NJ has 37 towns with bans, NY has a ~1-year pause on ≥50 MW builds, NJ's "Fair Share" law makes datacenters pay grid costs.
- **Prices (per 1M tokens):** gpt-6-luna $0.10 / $0.01 cached / $0.125 cache-write / $0.50 out · gpt-6.1-sol $2 / $0.10 / $2.50 / $10 · gpt-6-astra $10 / $1 / $12.50 / $50.
- **Responses API fields to log:** `input_tokens`, `output_tokens`, `total_tokens`, `input_tokens_details.cached_tokens`, `input_tokens_details.cache_write_tokens`, `output_tokens_details.reasoning_tokens` (**reasoning tokens bill as output**).
- **His five cost-cutting moves:** measure (log from the API response) · pick cheaper models (small model routes, large one only when needed) · set caps (tool calls, retries, total tokens) · cache (stable content first, breakpoint, variable content after; 30-min TTL) · choice models that return a pick + probabilities instead of long text.

### Safety (Lec 12)
- **Three failure modes: misalignment, misuse, prompt injection.** Use these words.
- **Outer alignment failure / specification gaming** (Tetris agent paused the game) vs. **inner failure / goal misgeneralization** (CoinRun agent learned "run right").
- **Reward hacking + Goodhart's Law** — "a measure stops being useful once it becomes a target." Human analogue: Wells Fargo's ~3.5M unrequested accounts. AI analogue: CoastRunners; coding agents deleting unit tests and hard-coding answers.
- Scheming: Apollo 2024 (o1 disabled oversight in 5% of runs); Anthropic 2025 (blackmail at 80–96% in a simulated replacement scenario). **Glass-box reasoning** is a safety tool — penalizing bad thoughts just hides them.
- **Prompt injection taxonomy: direct** (jailbreak typed in chat) vs. **indirect** (hidden in web pages, PDFs, resumes, emails, tool outputs). Real cases: hidden text in arXiv papers soliciting positive AI reviews, Perplexity Comet leaking a login code from a Reddit comment, EchoLeak exfiltrating M365 Copilot data from one email, white-text resumes.
- **His six rules of thumb:** measure what you mean · don't rely on sandboxes alone, monitor continuously · **treat all external content as untrusted** · minimal permissions, reward stopping · verify agent claims and test against adversarial inputs · keep reasoning readable.

### Future directions (Lec 13)
- The personal-agent race (OpenClaw, Hermes, Gemini Spark, Grok Bot, Muse, Instinct, Manus Cue, Dots) and the **agent startup gold rush**: Harvey $15.6B (legal), Sierra $15B (support), Abridge $5.3B (clinical notes), Decagon $4.5B, Actively $250M. **The playbook is: pick a job, build an agent for it.** Good framing for the Impact section.
- **Who checks the agents?** AIUC (certification + insurance, ~5,000 attack tests), Mount (liability insurance via continuous red-teaming), Braintrust, Patronus. Useful for Limits/Next steps.
- Open-weight models trail closed by ~4 months; China leads (DeepSeek, Qwen, Kimi, GLM). Memory ≈ params × bytes/param (0.5 at 4-bit).

## 6. Strategy — how we maximize points

1. **The idea is 21 points and gates the tier.** Pick something not on the overdone list, that a real person other than you actually needs, and that you can put in front of that person this week for a quote and a before/after time. Tier 3 is unreachable without a named user.
2. **Build multi-agent, not single-agent.** The agent-design row (10) and the course's whole arc reward a boss/specialist structure with visible handoffs and a diagram.
3. **Instrument cost and safety on day one.** `pricing.py`, per-agent usage capture, a budget cap, and a prompt-injection defense are all *code*, and all four report rows that pay double for evidence depend on code that already exists.
4. **Screenshot as you go.** Every screenshot the report needs is of a thing that only exists while the app is running.
5. **Freeze and rehearse the clone test.** Fresh clone → README → running in under 10 minutes, ideally on a machine that is not this one.
6. **Report and slides last, from the real artifacts** — and every number in them must match the app.
7. **Write the report in his vocabulary.** Name the five harness parts (tools, memory, stopping rules, guardrails, audit trail). Say which topology (hierarchy vs. mesh) and justify the intelligence allocation (smart boss / cheap workers). Classify the safety work as misalignment / misuse / prompt injection, and the injection as direct vs. indirect. Frame the idea as AI-maxxing — a redesigned workflow, not a faster version of the old one. These are free points on rows a grader scans for familiar language.
8. **Draw the flow diagram before building** — he asks for it in Lecture 2 *and* grades it in the agent-design row. Same artifact, two payoffs.

## 7. Open questions for JP
- What is the project idea?
- Is there a real user we can put it in front of before Oct 26? (This is the Tier 2 → Tier 3 line.)
- Host on Render, or ship as a local-clone app? (Hosting is more work but removes the 10-minute risk and looks better.)
