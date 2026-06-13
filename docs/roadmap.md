# Roadmap — Next 4–6 Weeks

Date: 2026-06-12
Status: Proposed, evidence-based. Supersedes nothing; complements `docs/mvp-plan.md` (phase view) with a prioritized, dated plan.

## North star

Put the product in front of 3–5 real PMs with their own messy inputs, and have **every quote in every generated artifact machine-verifiable against its source**.

## Why this plan (evidence summary)

### From stress-testing this repo (2026-06-12)

Four realistic messy inputs (noisy multi-topic Slack paste, contradictory interview, mixed decision/brainstorm meeting notes, unedited voice-memo transcript — committed under `examples/inputs/adversarial/`) were run through the pipeline:

- The deterministic engine **fabricated evidence** for every unrecognized input (canned activation-panel narrative regardless of content); zero artifacts mentioned the inputs' actual signals (SSO, xlsx, PowerBI, permissions). This violates SKILL.md rule 7 ("Never invent customer evidence").
- Field extraction only works on fixture-exact headings; the interview fixture produced empty Role/Segment/Pain points/Goals sections and lost the interviewee's contradictions.
- `check_workspace.py` **passed the fabricated workspace** — it validates structure (sections, `Source:` lines), not content.
- Classification fell back to generic on 3 of 4 inputs.

Honest state (at time of stress-test): right architecture and trust rules; no working extraction engine for real inputs; no content-level trust enforcement. Both gaps are now closed — see Plan items #1 (real engine) and #2 (quote verification) below.

### From market/practice research (five-stream web research, 2026-06-12)

1. **Synthesis is the bottleneck.** Manual interview analysis ≈ 2–3 hours per interview hour (Teresa Torres, producttalk.org); 68% of researchers say analysis/synthesis is where AI will matter most (State of User Research).
2. **Evidence repositories become graveyards.** NN/g survey of 400+ ResearchOps professionals: only ~9% of repositories thriving; failure causes are maintenance friction and retrieval (nngroup.com/articles/why-repositories-fail).
3. **Confident gap-filling is the characteristic AI failure.** Torres measured ~30% of ChatGPT "direct quotes" as wrong or fabricated; Lenny's Newsletter documents "Frankenstein quotes" and fabricated participant IDs (lennysnewsletter.com "How to do AI analysis you can actually trust").
4. **Citations raise trust even when fake — and trust collapses on verification** (arXiv:2501.01303; arXiv:2504.06435). Decorative citations are an adoption trap; machine-verified links are the defensible version.
5. **One-shot cross-corpus summarization is the condemned anti-pattern**; the endorsed method is per-interview synthesis first, then cross-unit synthesis with traceability (Torres) — which is this product's architecture (per-input discovery notes → accumulated artifacts → weekly brief).
6. **Competitive white space:** no incumbent auto-maintains a living PRD, decision log, or scheduled weekly brief; Productboard's AI insight-linking is reviewed as error-prone busywork (G2); pricing floors (~$3.5k/yr Productboard for 5 makers, ~$5k/yr Zeda, $20/seat Notion AI, ~$147/mo Aha!) exclude small teams; contradiction detection is shipped by essentially nobody.
7. **Distribution proof:** an installable PM prompt-skills repo gained ~5,000 GitHub stars in 4 months, while repos implementing persistent-state/living-PRD pipelines have ~6 stars — the niche is architecturally validated, commercially unclaimed, and the channel is installable skills.
8. **Decision logs** are universally recommended and routinely abandoned within weeks; the cited fix is sub-60-second logging friction plus an operating model.
9. **Cross-week memory/continuity** is endorsed by the practice canon (Torres's snapshots-as-index; her public use of persistent Claude memory for discovery) but has **no independent quantitative demand evidence** — a hypothesis to test in user tests, not a settled bet.

## Plan

### Weeks 1–2 — Stop the fabrication, make trust checkable

1. **Make the LLM path the real engine; make the demo honest.** ✅ Landed. `scripts/extract_capture.py` is a real, non-deterministic LLM engine (provider `auto`: Anthropic Messages API via `ANTHROPIC_API_KEY`, else the `claude` CLI). It reads arbitrary messy input, asks the model for structured extraction, and **verifies every Evidence quote verbatim against the source before writing** — using the same normalization as `check_workspace.py`, so accepted quotes pass the linter by construction. It refuses to write artifacts when no quote verifies (no empty/fabricated Evidence). Validated against the adversarial fixtures: on `adversarial/101` it correctly classifies (Support Ticket Cluster, not the canned activation narrative) and recovers the real signals (CSV, SSO, xlsx, Starter-tier pricing, trial churn) the deterministic engine missed — 7 quotes verified. `scripts/run_capture_demo.py` is now honest: it **refuses inputs it does not recognize** rather than fabricating a narrative, and points users to the real engine. The LLM call is the only non-deterministic boundary; prompt building, parsing, verification, and rendering are unit-tested offline, with a `EXTRACT_CAPTURE_LIVE=1`-gated end-to-end test.
2. **Quote verification in `check_workspace.py`.** ✅ Landed. Every quoted Evidence bullet must appear verbatim (after quote/whitespace/case normalization) in its source input; empty Evidence sections fail. Matching is verbatim, not fuzzy — a fuzzy match would accept "Frankenstein quotes" stitched from real fragments, the exact failure this guards against. Confirmed to flag the deterministic engine's fabrication on all four adversarial fixtures. Converts the top adoption barrier into the differentiator: *every quote machine-verified*.
3. **Adversarial fixture suite committed** (`examples/inputs/adversarial/`) as the standing quality bar. These are deliberately NOT wired into the deterministic demo; they exist to evaluate the agent path and future extraction work.

### Weeks 3–4 — The two white-space features

4. **Contradiction surfacing v1.** Extend the PRD touchpoint report to flag (a) new evidence conflicting with PRD claims, (b) conflicting statements across notes. Acceptance test: the contradictory-interview fixture ("an hour, maybe 90 min" vs "4 hours"; wants automation but doesn't trust it).
5. **Sub-60-second decision capture.** One command/paste → proposal-first decision-log entry, attacking the documented abandonment cause (friction).
6. **Weekly brief with verifiable links.** Every claim in the brief links to a discovery note and quote, matching the per-unit → cross-unit method.

### Weeks 5–6 — Real user test + positioning

7. **User-test sprint with 3–5 PMs on their real inputs** (the `--text`/stdin capture path; `docs/user-test-guide.md` extended beyond the canned demo). Measure: % of quotes verified, signal recall (did artifacts capture *their* topics?), and week-2 return — the memory-continuity hypothesis test.
8. **Positioning and distribution.** "Local/private product memory agent — every quote verifiable." Ship as installable skills; rewrite `docs/use-case-validation.md` statuses to reflect honest (agent-path) validation rather than deterministic-demo validation.

## Decision gates

- If quote-verification precision cannot be made high → narrow the wedge to **interview synthesis only** (strongest pain, clearest method fit).
- If testers value the weekly brief over accumulated memory → lead with **brief-first** positioning.

## Adversarial fixtures

The "Known current failure" column records how the **deterministic demo** fails each
fixture — the motivation for the real engine (item #1). The real engine
(`scripts/extract_capture.py`) is evaluated against these same fixtures; the demo now
refuses them outright instead of fabricating.

| Fixture | Stresses | Known current failure (deterministic demo) |
| --- | --- | --- |
| `adversarial/101-noisy-slack-thread.md` | Multi-topic noise, no `>` quotes, buried signals (export reliability + format, SSO, pricing comms) | Fabricated activation narrative; empty Evidence |
| `adversarial/102-contradictory-interview.md` | Internal contradictions, unstructured headings, unverified claims | Empty extraction sections; contradictions lost |
| `adversarial/103-mixed-meeting-notes.md` | Decision + brainstorm + action items in one input | Misclassified; decided-vs-pending distinction lost |
| `adversarial/104-founder-voice-memo.md` | Unpunctuated transcript, mixed product/marketing topics | Misclassified; repeated "permissions" signal lost |
