# User Test Guide

## Purpose

Use this guide to run a 5–10 minute manual user test of Hermes Product Teams as a **Discovery + Living Docs Agent**. The test checks whether a PM, founder, or product trio can turn messy product input into useful product-memory artifacts without losing source-linked evidence or silently changing important docs.

This is a local/private Markdown workspace test. It should not require SaaS integrations, roadmap tooling, recruiting workflows, or external message delivery.

## Setup

1. Start from the repository root.
2. Run the deterministic demo:
   ```bash
   python3 scripts/run_capture_demo.py
   ```
3. Open these generated artifacts:
   - `examples/workspace/Discovery Notes/001-customer-feedback-thread.generated.md`
   - `examples/workspace/Customer Insights.md`
   - `examples/workspace/Decision Log.md`
   - `examples/workspace/Open Questions.md`
   - `examples/workspace/PRD Update Proposals.md`
   - `examples/workspace/Weekly Briefs/weekly-brief-2026-06-10.generated.md`
4. Keep the source input open for comparison:
   - `examples/inputs/001-customer-feedback-thread.md`

## 5–10 minute test script

### Minute 0–1: Frame the product

Tell the tester:

> This MVP is a Discovery + Living Docs Agent. It helps product teams convert messy feedback and product conversations into discovery notes, customer insights, decision memory, PRD update proposals, open questions, and weekly briefs. It should preserve source-linked evidence and require human approval before important docs change.

Confirm the tester understands that the workflow must **do not merge, deploy, create issues, send messages, or change external systems** during this test.

### Minute 1–3: Inspect the source and discovery note

Ask the tester to compare `examples/inputs/001-customer-feedback-thread.md` with the generated discovery note.

Prompts:

- Which source statements are preserved as evidence?
- Can you distinguish facts from assumptions?
- Are customer pains and requested outcomes easy to find?
- What would you distrust or want traced back to the source?

### Minute 3–5: Inspect living product-memory artifacts

Ask the tester to review the generated customer insights, decision-log proposal, open questions, and PRD update proposal.

Prompts:

- Does each important claim retain source-linked evidence?
- Does the PRD update proposal stay proposed rather than silently editing `PRD.md`?
- Is human approval clearly required before changing source-of-truth product docs?
- Are open questions specific enough to guide the next discovery step?

### Minute 5–7: Inspect the weekly brief

Ask the tester to open the weekly brief.

Prompts:

- Could a PM or product trio read this quickly and understand what changed?
- Are decisions, pending decisions, open questions, and next actions separated?
- Does the brief remain a product-memory synthesis rather than roadmap management or user research operations?

### Minute 7–10: Capture readiness feedback

Ask the tester:

- What artifact would you use as-is in your product workflow?
- What artifact would you rewrite before sharing?
- What missing source evidence would block trust?
- What is the smallest change that would make this useful in a real product-team workspace?

## Success criteria

The test is successful enough for the next user-test iteration when:

- the tester can explain the Discovery + Living Docs Agent wedge in their own words;
- generated artifacts preserve source-linked evidence from the input fixture;
- facts from assumptions are visibly separated;
- PRD/spec implications appear as a PRD update proposal, not a silent edit to `PRD.md`;
- human approval is required before important docs change;
- open questions are specific and actionable;
- the weekly brief is concise enough for a PM/founder/product trio to scan quickly;
- the tester does not mistake the product for a roadmap manager, survey/recruiting tool, support-ticket system, or project-management system.

## Observer checklist

Record pass/fail/notes for each item:

- The tester found the original source input.
- The tester found at least one source-linked evidence item in a generated artifact.
- The tester identified at least one assumption or open question.
- The tester understood that the PRD update proposal requires human approval.
- The tester understood that the workflow should not silently modify source-of-truth docs.
- The tester understood the test must do not merge, deploy, create issues, send messages, or change external systems.
- The tester could describe which artifact was most useful and why.
- The tester identified the most important missing trust/readiness gap.

## Notes template

```markdown
# User test notes — YYYY-MM-DD

Tester role:
Product context:
Fixture used:

## Observed behavior
- 

## Trust blockers
- 

## Most useful artifact
- 

## Confusing or overreaching artifact
- 

## Evidence gaps
- 

## Next recommended product change
- 
```
