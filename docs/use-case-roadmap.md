# Use-Case Expansion Roadmap

Date: 2026-06-13
Status: Proposed. A breadth plan for the input types and workflows Hermes Product Teams should tackle next.

## How this doc fits

- `docs/prd-direction.md` — the guardrails this roadmap must respect (the memory/discovery/docs wedge).
- `docs/use-case-validation.md` — the **six use cases already specified** (customer feedback, user interview, support ticket cluster, internal decision, product brainstorm, weekly synthesis). This doc adds the *next* ones.
- `docs/roadmap.md` — the 4–6 week **engine/trust** plan (quote verification landed; real LLM extraction engine pending). That work is a hard dependency for everything here.
- `docs/mvp-plan.md` — Phase 4 (integrations) is where Tier D below lives.

## The sequencing principle that governs everything below

**New use cases cannot be validated on the deterministic demo.** Stress-testing (`docs/roadmap.md`) showed the templated engine fabricates evidence and produces empty `## Evidence` sections on any non-fixture input. So a new use case is **"done" only when the LLM extraction path produces output that passes `scripts/check_workspace.py` quote verification on a *realistic, messy* fixture** — not a curated one shaped to fit the parser.

Concretely, every use case in this roadmap inherits this definition of done:

1. A realistic (deliberately messy) input fixture exists.
2. The agent path (`run_agent_capture.py` → Hermes) produces the expected artifacts.
3. `check_workspace.py` passes: every Evidence quote traces verbatim to the source; no empty Evidence; `PRD.md` untouched; facts separated from assumptions.
4. A human reviewer agrees the artifacts captured the input's *actual* signals (signal recall), not a plausible-sounding fabrication.

This is why Tier A cannot ship before `docs/roadmap.md` item #1 (make the LLM path the real engine). The breadth roadmap rides on top of the depth roadmap.

## The guardrail filter

Every candidate below was run through the five `docs/prd-direction.md` alignment checks. Candidates that fail any check are either constrained until they pass or moved to "Out of scope." Three recurring constraints:

- **No revenue weighting.** Capturing signal from revenue-facing conversations is in-wedge; computing revenue-weighted priority or pulling CRM amounts is not (needs integrations + becomes prioritization authority).
- **No external mutation.** Capturing the product-memory implication of an incident/ticket/review is in-wedge; creating or editing tickets, posting replies, or touching external systems is not.
- **No monitoring automation.** Capturing human-pasted competitor/market notes as Research Findings is in-wedge; scraping or scheduled competitive monitoring is a different product.

## Tier A — New input types (breadth, near-term)

Same capture → artifact pattern as today's six, applied to new source shapes. These are the fastest wins once the engine is real, and each just needs a fixture + acceptance criteria. Build order is by evidence strength from the market research.

| ID | Use case | Target user | Key artifacts | Guardrail | Priority |
| --- | --- | --- | --- | --- | --- |
| UC-201 | Sales / CS call signal | Founder, PM at startup with revenue-facing calls | Discovery note, customer insight, open questions, possible PRD proposal | Qualitative signal only — **no revenue weighting** | High |
| UC-202 | Churn / cancellation / exit-survey feedback | PM, founder, growth | Discovery note, customer insight (churn theme), decision/triage proposal | Capture reasons + evidence; not a retention-ops tool | High |
| UC-203 | Public review / community / NPS verbatim cluster | PM, founder | Discovery note, customer insight, open questions | Human-pasted; not review-monitoring automation | Medium |
| UC-204 | Competitor / market signal note | PM, founder | Discovery note classified as Research Finding, open questions | **No scraping/monitoring**; human-pasted, sourced | Medium |
| UC-205 | Incident / bug retro → product implication | PM, eng-lead in a trio | Discovery note, decision proposal, possible PRD proposal | Product-memory implication only — **never touches tickets** | Medium |
| UC-206 | Noisy multi-topic thread → split into threads | PM drowning in Slack | Multiple discovery notes (one per distinct signal) + open questions | Already have fixture `adversarial/101`; formalize | High |

### Detailed specs for the first build wave (UC-201, UC-202, UC-206)

**UC-201 — Sales / CS call signal**
- Fixture to author: `examples/inputs/201-sales-call-feedback.md` (a messy sales/CS call note: prospect objections, feature asks tied to deals, mixed buying-signal and product-signal).
- Acceptance criteria: feature asks are captured as customer signals with the source; deal context is preserved as evidence **without** being turned into revenue-weighted priority; PRD implications remain proposals; the note distinguishes "prospect wants X" (assumption about need) from "prospect said X" (fact/quote).
- Guardrail check: passes all five; constrained on revenue weighting.
- Status: **fixture authored + engine-validated** — `examples/inputs/201-sales-call-feedback.md`. Live capture verified 7 verbatim quotes, trust linter passes; output keeps feature asks as source-linked signals, separates the AE's read (assumptions) from prospect quotes, and prioritizes on deadline/blockers rather than deal value. Remaining to fully close: human-confirmed signal-recall sign-off.

**UC-202 — Churn / exit-survey feedback**
- Fixture: `examples/inputs/202-churn-exit-feedback.md` (cancellation reasons, exit-survey verbatims, a CSM's interpretation mixed in).
- Acceptance criteria: stated churn reasons captured verbatim as evidence; PM interpretation separated from customer statements; a durable "why customers leave" insight theme accumulates across captures (leverages the per-capture accumulation already shipped); does not exaggerate from small N.
- Status: **fixture authored + engine-validated** — `examples/inputs/202-churn-exit-feedback.md`. Live capture verified 8 verbatim quotes, trust linter passes; customer verbatims land as evidence, the CSM's interpretation is quarantined as assumptions, and the output flags the small sample (n=6, really 4 activated) rather than over-reading it. Remaining to fully close: human-confirmed signal-recall sign-off.

**UC-206 — Noisy multi-topic thread splitting**
- Fixture: existing `examples/inputs/adversarial/101-noisy-slack-thread.md` (export reliability + format + SSO + pricing comms in one thread).
- Acceptance criteria: the engine produces **distinct** discovery notes/signals per topic rather than one blurred note; each signal traces to the specific lines that support it; no topic silently dropped (this is the exact failure the deterministic engine showed). This use case is the clearest demonstration of the engine upgrade and should be a flagship acceptance test.
- Status: **engine support shipped** — `scripts/extract_capture.py --split` segments a noisy input into one verbatim-verified note per topic, reporting (never silently dropping) topics whose evidence can't be verified; the trust linter is split-aware. Verified live on `adversarial/101` (four distinct topics recovered). Remaining to fully close: human-confirmed signal-recall sign-off on a realistic messy fixture.

## Tier B — Longitudinal / cross-artifact workflows (depth, the moat)

These exploit *accumulated memory across captures* — the differentiator no incumbent ships (research: contradiction detection is unshipped white space; teams re-litigate decisions; repositories become graveyards). They are higher-value and higher-effort, and depend on Tier A producing real accumulated content.

| ID | Workflow | What it does | Evidence basis | Priority |
| --- | --- | --- | --- | --- |
| UC-210 | Contradiction surfacing | Flag new evidence conflicting with PRD claims, and conflicting statements across notes | `roadmap.md` item #4; nobody ships this | High |
| UC-211 | Decision re-litigation guard | "We're discussing X again — here's the prior decision, rationale, and date" | Research: teams re-litigate every planning cycle | High |
| UC-212 | Open-question lifecycle | Track a question from raised → evidence accrues → answered/closed; flag stale-open | Research: repository "graveyard" / staleness | Medium |
| UC-213 | PRD coverage / drift audit | Which PRD sections lack recent evidence; which strong signals have no PRD home | Extends `report_prd_touchpoints.py` | Medium |
| UC-214 | Theme consolidation | Merge duplicate insights across weeks into durable themes with evidence counts | Atomic-research "nuggets" practice | Medium |
| UC-215 | Evidence-strength escalation | Promote a signal toward a PRD proposal only after N independent sources | Brainstorm use case's "evidence threshold" | Low |

The acceptance test for UC-210/UC-211 already exists: the contradictory-interview fixture (`adversarial/102`: "an hour, maybe 90 min" vs "4 hours"; wants automation but distrusts it) and any decision re-raised across two captures.

## Tier C — Output / communication use cases

Synthesis *from* accumulated memory into audience-shaped outputs. Research showed per-audience customization is the core weekly-update pain.

| ID | Use case | What it produces | Guardrail |
| --- | --- | --- | --- |
| UC-220 | Audience-tailored update (exec / eng / investor) | Same memory, three framings with source links | Communication of memory, **not** a status-tracking/PM tool |
| UC-221 | Monthly / quarterly roll-up | Longitudinal synthesis over many weekly briefs | Summarizes existing artifacts only |
| UC-222 | New-teammate onboarding brief | "Why did we build it this way" — decisions + rationale + evidence | Directly answers the re-litigation/amnesia pain |
| UC-223 | "What changed in our understanding this week" digest | Diff of insights/decisions/open-questions vs last week | Requires per-week snapshots |

## Tier D — Integration-fed capture (gated, Phase 4)

Out of near-term scope; listed for completeness and to set the permission bar. Each requires the explicit-approval permission model and must preserve the local/private-first default.

- UC-230 Slack / Telegram gateway capture
- UC-231 Meeting-notes import (e.g. Granola/Otter transcript → capture; Granola exposes API/MCP per research)
- UC-232 Notion / Google Docs output sync (propose-first into external docs)
- UC-233 Linear / Jira *read-only* issue summary intake (never write)

Gate: no Tier D ships until the local Markdown workflow is validated with real users (`roadmap.md` weeks 5–6) and a written permission model covers external reads/writes.

## Build sequencing (recommended)

1. **Prerequisite** — `roadmap.md` item #1 (real LLM extraction engine) + quote verification (done). Nothing in Tier A is trustworthy until extraction is real.
2. **Wave 1 (breadth proof):** UC-206 (thread splitting — flagship engine test), UC-201, UC-202. Highest-evidence pains, reuse the capture pattern.
3. **Wave 2 (moat):** UC-210 (contradiction surfacing) + UC-211 (re-litigation guard). The features no competitor has.
4. **Wave 3 (breadth fill):** UC-203, UC-204, UC-205; UC-212/UC-213 longitudinal.
5. **Wave 4 (communication):** UC-220, UC-222 (strongest of Tier C by research).
6. **Later / gated:** remaining Tier B depth, Tier C, then Tier D integrations.

## Per-use-case validation bar (rubric extension)

Extends the `docs/use-case-validation.md` readiness rubric. A new use case is **Ready for user test** when, in addition to the existing rubric, it:

- ships a **realistic/messy** fixture (not parser-shaped), ideally adversarial-grade;
- passes `check_workspace.py` quote verification (every Evidence quote traces to source);
- demonstrates **signal recall** on the messy fixture (a reviewer confirms the artifacts captured the input's real signals, with no fabricated ones);
- respects its guardrail constraint (revenue / mutation / monitoring) with a test or check where automatable.

## Explicitly out of scope (and why)

- **Roadmap prioritization / scoring authority** — would make us a roadmap tool (fails alignment check 4).
- **Revenue-weighted prioritization** — needs CRM integration and becomes prioritization authority (`prd-direction.md` non-goal).
- **User-research operations** (recruiting, scheduling, survey/panel management) — fails check 4; this is the memory/docs layer, not research ops.
- **Ticket/incident operations** (creating, triaging, closing tickets) — external mutation; we capture the implication, the team acts in their tools.
- **Competitive monitoring automation** (scraping, scheduled crawls) — a different product; we accept human-pasted notes only.
- **Sending stakeholder messages / posting updates to external channels** — external mutation requiring explicit approval; default is propose-and-hand-back.
