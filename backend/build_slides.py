"""Build slides.html — self-contained reveal.js deck, 10 slides maximum."""
from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "output" / "shots"
OUT = ROOT / "slides.html"


def b64(path: Path) -> str:
    mime = "jpeg" if path.suffix in {".jpg", ".jpeg"} else "png"
    return f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def shot(name: str) -> str:
    p = SHOTS / f"{name}.png"
    return b64(p) if p.is_file() else ""


runs = json.loads((ROOT / "output" / "audit_trail.json").read_text(encoding="utf-8"))
lanes: dict[str, dict] = {}
for r in runs:
    lane = r.get("lane") or "?"
    u = r.get("usage") or {}
    b = lanes.setdefault(lane, {"runs": 0, "usd": 0.0})
    b["runs"] += 1
    b["usd"] += u.get("total_usd", 0)
total = sum(b["usd"] for b in lanes.values())
rej = sum(1 for r in runs for e in r.get("events", []) if e.get("type") == "qa_rejected")
chat = lanes["comadre"]["usd"] / lanes["comadre"]["runs"]
card = lanes["taller"]["usd"] / lanes["taller"]["runs"]

group = ROOT / "assets/web/event/group-holding-cards.jpg"

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Lotería Climática — MGT 409</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/theme/white.css">
<style>
  :root {{ --ink:#2e2520; --green:#2e6b3f; --orange:#f04e23; --amber:#f2a227;
           --paper:#edede8; }}
  .reveal {{ font-family:"Jost","Helvetica Neue",sans-serif; color:var(--ink); }}
  .reveal .slides section {{ text-align:left; }}
  .reveal h1 {{ font-size:2.3em; letter-spacing:-.02em; text-transform:none; font-weight:600; }}
  .reveal h2 {{ font-size:1.5em; text-transform:none; font-weight:600;
                border-bottom:3px solid var(--ink); padding-bottom:.15em; margin-bottom:.5em; }}
  .reveal h3 {{ font-size:.95em; text-transform:uppercase; letter-spacing:.08em;
                color:var(--green); font-weight:600; }}
  .reveal p, .reveal li {{ font-size:.72em; line-height:1.45; }}
  .reveal .big {{ font-size:2.6em; font-weight:600; line-height:1; color:var(--orange); }}
  .reveal .stat {{ display:inline-block; margin:0 1.4em .6em 0; }}
  .reveal .stat b {{ display:block; font-size:2em; line-height:1; color:var(--orange); }}
  .reveal .stat span {{ font-size:.5em; text-transform:uppercase; letter-spacing:.1em; opacity:.65; }}
  .reveal .two {{ display:grid; grid-template-columns:1fr 1fr; gap:1.2em; align-items:start; }}
  .reveal img.shot {{ width:100%; border-radius:6px; box-shadow:0 6px 24px rgba(0,0,0,.18); }}
  .reveal .quote {{ background:var(--paper); border-left:5px solid var(--amber);
                    padding:.5em .8em; font-size:.68em; }}
  .reveal .rej {{ background:#fdeee9; border-left:5px solid var(--orange);
                  padding:.5em .8em; font-size:.62em; }}
  .reveal table {{ font-size:.58em; }}
  .reveal .tag {{ display:inline-block; background:var(--green); color:#fff;
                  font-size:.42em; letter-spacing:.12em; text-transform:uppercase;
                  padding:.3em .8em; border-radius:99px; margin-bottom:.6em; }}
  .reveal section.cover {{ text-align:left; }}
  .reveal .muted {{ opacity:.6; font-size:.6em; }}
</style></head><body>
<div class="reveal"><div class="slides">

<!-- 1 -->
<section class="cover">
  <span class="tag">MGT 409 · Final Project</span>
  <h1>Lotería <span style="color:var(--orange)">Climática</span></h1>
  <p style="font-size:.85em">A climate-disinformation defence system that manufactures
  its own counter-messaging — routed through value frames measured on the audience it serves.</p>
  <p class="muted">Juan Pablo Alvarado · Yale SOM · gpt-6-luna via Portkey</p>
  <p style="font-size:.6em;margin-top:.4em">Public repository —
  <a href="https://github.com/alvaradojp00/loteria-climatica">github.com/alvaradojp00/loteria-climatica</a><br>
  <span class="muted" style="font-size:.85em">Runs locally from a fresh clone; see README.md. Not hosted.</span></p>
</section>

<!-- 2 -->
<section>
  <h2>The problem</h2>
  <div class="two">
    <div>
      <p>Disinformation reaches Spanish-speaking families through the channel they
      trust most: <b>the family WhatsApp group</b>. It arrives from someone who loves them.</p>
      <p>The correction arrives as <b>a PDF, in English</b>, written for people already convinced.</p>
      <p>I made the first twelve Climate Lotería cards at GreenLatinos. A team, over weeks.
      <b>That is why there are twelve and not a hundred and twenty</b> — while the narratives
      change weekly.</p>
    </div>
    <img class="shot" src="{b64(group)}" alt="Community event">
  </div>
</section>

<!-- 3 -->
<section>
  <h2>What is new</h2>
  <p><b>Factchequeado, Maldita, Chequeado, Climate Feedback, CAAD</b> — all better
  resourced, all human-paced, none hands you words to say.</p>
  <p>Two things here do not exist elsewhere:</p>
  <div class="quote">
  <b>1. Framing routed by a controlled experiment.</b> GreenLatinos + Resource Media
  tested five value frames on <b>1,797 Latinx adults</b> (Grow Progress, 2025).
  Health <b>+11</b> on community danger · Family <b>+6</b>, no backlash anywhere ·
  Villain <b>−1 overall, −15 with liberals</b>.<br><br>
  <b>2. The deck is an output, not a dataset.</b> The system listens, notices what no
  card answers, and manufactures the missing one.
  </div>
</section>

<!-- 4 -->
<section>
  <h2>The agents</h2>
  <pre style="font-size:.42em;line-height:1.4;background:#f5f1e6;padding:.7em;border-radius:6px;">
         El Despachador  (choice model: a lane + a confidence)
                              |
   Comadre ---- Contra ---- Maestra ---- Editor
       \\___________\\________/__________/
                        |
    shared pool: researcher · framer · tactic · extractor
                 transcreator · artist
                        |
    shared gates (reject upward): verifier · visual QA
                        |
             La Archivista (deterministic deck custodian)
  </pre>
  <p style="font-size:.62em"><b>A hierarchy of control with a service mesh underneath.</b>
  Chat is deliberately <b>one agent</b> — measured, the mesh variant cost more for no gain.
  The gap detector, cadence gate, renderer and budget guard are <b>plain code</b>:
  the card template is why generated cards look like the deck.</p>
</section>

<!-- 5 -->
<section>
  <h2>One run, traced</h2>
  <p style="font-size:.62em"><i>"Los paneles solares no sirven… por eso se fue la luz en Texas."</i></p>
  <div class="rej">
  <b>Researcher</b> → 3 citations · <b>Framer</b> → <code>family</code> (+6), rejecting
  villain (−4 topline, −14 moderates)<br>
  <b>Verifier REJECTED</b> — "55% of unplanned outages" dropped the denominator; the source
  said 55% of outages <i>and derates by capacity</i><br>
  <b>Verifier REJECTED again</b> — "evidence does not show solar caused the blackout"
  overstated the citation<br>
  <b>→ Card 13, El Panel Solar · $0.0079</b>
  </div>
  <p style="font-size:.62em"><b>{rej} gate rejections</b> across {len(runs)} runs.
  The system refuses its own work when the evidence does not carry it.</p>
</section>

<!-- 6 -->
<section>
  <h2>It works — both halves</h2>
  <div class="two">
    <div>
      <img class="shot" src="{shot('ask')}" alt="La Comadre answering">
      <p class="muted"><b>The public side.</b> Explanation, the named technique, and the
      line you can actually say, in whichever language you wrote in.</p>
    </div>
    <div>
      <img class="shot" src="{shot('taller_panel')}" alt="El Taller, the operator console">
      <p class="muted"><b>The operator side</b>, password-gated. A consented list, an
      audience builder that <i>cannot</i> reach anyone who did not opt in, the gap queue,
      and approvals. An organising tool, not a demo.</p>
    </div>
  </div>
</section>

<!-- 7 -->
<section>
  <h2>Cost to run</h2>
  <div>
    <span class="stat"><b>${chat:.5f}</b><span>per chat turn</span></span>
    <span class="stat"><b>${card:.4f}</b><span>per card made</span></span>
    <span class="stat"><b>${total:.2f}</b><span>whole project</span></span>
    <span class="stat"><b>{len(runs)}</b><span>runs measured</span></span>
  </div>
  <table>
  <tr><th>Unit</th><th>Per user/mo</th><th>100 users</th><th>10,000 users</th></tr>
  <tr><td>Chat, 8 turns</td><td>${chat * 8:.4f}</td><td>${chat * 800:.2f}</td>
      <td>${chat * 80000:,.0f}</td></tr>
  <tr><td>Full 54-card deck</td><td colspan="3">${card * 54:.2f} one-off</td></tr>
  </table>
  <p style="font-size:.6em">Measured from <code>audit_trail.json</code>, not estimated.
  Savings: prompt caching behind a breakpoint, a choice model at the router, a single-agent
  chat, hard <code>BudgetExceeded</code> caps. <b>Reasoning tokens bill as output</b> and
  dominate — visible only if you read the usage details.</p>
</section>

<!-- 8 -->
<section>
  <h2>Safety</h2>
  <p style="font-size:.64em">Three escalating injection attacks — blatant, hidden
  editorial note, payload-carrying (EchoLeak's shape).</p>
  <table>
  <tr><th>Attack</th><th>Result</th></tr>
  <tr><td>Blatant "ignore all instructions"</td><td>Blocked by the gateway (HTTP 400)</td></tr>
  <tr><td>Hidden fake verification note</td><td>Detected, claim corrected anyway</td></tr>
  <tr><td>Attacker URL in the reply</td><td>Detected, URL never appeared</td></tr>
  </table>
  <div class="rej" style="margin-top:.5em">
  <b>Reported as a measured negative.</b> I could not make gpt-6-luna comply, so there is
  no staged before/after. The tripwire <b>detected planted instructions 4 of 4 times</b>.<br><br>
  <b>The finding:</b> my first defence said <i>"this is not instruction"</i> — Azure's Prompt
  Shield read that as an override attempt and <b>refused the request</b>.
  A defence written in the obvious voice <b>fails closed</b>.
  </div>
  <p style="font-size:.58em">Also: 3-conversation floor before minting (Goodhart on our own
  metric), evidence required, human approval, hard budget caps.</p>
</section>

<!-- 9 -->
<section>
  <h2>Impact — and what I cannot claim</h2>
  <div class="two">
    <div>
      <p><b>Measured:</b> 42 cards manufactured with cited evidence, ~90s and
      ${card:.4f} each, against twelve cards in months by a team.
      Every card records its frame, its measured lift, and the frames it rejected.</p>
      <div class="rej"><b>Not measured: I did not run a user trial.</b> The rubric asks for a
      real quote or a before/after time and I do not have one. Claiming a pilot I did not run
      is exactly what the Verifier spends its time rejecting.</div>
    </div>
    <img class="shot" src="{shot('deck')}" alt="The deck">
  </div>
</section>

<!-- 10 -->
<section>
  <h2>Limits · Next</h2>
  <div class="two">
    <div>
      <h3>Limits</h3>
      <p style="font-size:.62em">No user trial · Framer only reached <i>health</i> and
      <i>family</i> because the audience is always "general" · Junkipedia authenticates but
      the org lacks API entitlement · single model, so no cross-tier comparison ·
      runs from a fresh clone, not hosted.</p>
    </div>
    <div>
      <h3>Next</h3>
      <p style="font-size:.62em">A five-person pilot with measured time-to-reply ·
      WhatsApp (webhook built and tested; needs a Twilio number) ·
      an MCP server — the tools already exist, only the wiring changes ·
      vary the audience so the Faith frame becomes reachable.</p>
    </div>
  </div>
  <p style="font-size:.66em;margin-top:.8em"><b>Repository (public):</b>
  <a href="https://github.com/alvaradojp00/loteria-climatica">github.com/alvaradojp00/loteria-climatica</a></p>
  <p class="muted" style="margin-top:.5em">Cards 1–12 created by Juan Pablo Alvarado as
  Program Manager at GreenLatinos with Intersectional Environmentalist, shown with
  attribution. Expanded deck and agent system are independent work.</p>
</section>

</div></div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.js"></script>
<script>Reveal.initialize({{ hash:true, slideNumber:'c/t', transition:'slide' }});</script>
</body></html>"""

OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.name}  ({OUT.stat().st_size // 1024} KB)  10 slides")
