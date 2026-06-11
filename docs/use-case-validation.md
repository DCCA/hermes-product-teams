# Use-Case Validation Matrix

## Purpose

This document validates Hermes Product Teams against real PM/founder user cases, not just repository structure. It is the MVP validation backlog for reaching a product ready for real user testing.

The product direction is protected by `docs/prd-direction.md`: Hermes Product Teams is a **Discovery + Living Docs Agent** focused on the **memory/discovery/docs layer**.

## Global acceptance criteria

Every validated use case should:

- preserve source-linked evidence;
- separate facts from assumptions;
- identify open questions;
- create or update product-memory artifacts;
- produce PRD update proposals when requirements/spec changes are implied;
- not silently edit PRD.md;
- avoid drifting into not roadmap management;
- avoid drifting into not user research operations;
- remain useful in a local/private Markdown workspace.

## Validation status summary

| Use case | Current status |
| --- | --- |
| Customer feedback thread | Partially validated with one fixture. |
| User interview notes | Partially validated with one fixture. |
| Support ticket cluster | Partially validated with one fixture. |
| Internal product decision discussion | Partially validated with one fixture. |
| Product brainstorm | Not yet validated. |
| Weekly synthesis from multiple inputs | Not yet validated. |

## Customer feedback thread

Target user: Startup PM or founder collecting feedback from customer-facing channels.

User job: Turn scattered customer/support comments into a discovery note, customer insight, open questions, decision proposal, PRD update proposal, and weekly brief signal.

Input fixture: `examples/inputs/001-customer-feedback-thread.md`

Expected artifacts:
- discovery note;
- customer insight update;
- decision-log proposal;
- open questions;
- PRD update proposal;
- weekly brief entry.

Acceptance criteria:
- Direct customer/support statements appear as source-linked evidence.
- The output separates facts from assumptions.
- The PRD update remains a proposal and does not silently edit PRD.md.
- The output identifies what data is needed before prioritizing the change.
- The output preserves the product direction as a memory/discovery/docs workflow.

Current status: Partially validated by `tests/test_prd_direction.py` and the deterministic capture demo.

Next gap: Add broader content checks specific to this use case and make the capture script less hardcoded.

## User interview notes

Target user: PM, founder, designer, or researcher processing a user interview.

User job: Extract pain points, goals, quotes, opportunity themes, contradictions, assumptions, and follow-up questions from interview notes.

Input fixture: `examples/inputs/002-user-interview-notes.md`

Expected artifacts:
- discovery note;
- customer insight update;
- open questions;
- possible PRD update proposal if a requirement implication is clear;
- weekly brief entry.

Acceptance criteria:
- Direct quotes are preserved as source-linked evidence.
- User pains and goals are separated from PM interpretation.
- Follow-up questions are specific and interviewable.
- No survey/recruiting workflow is introduced because this is not user research operations.
- PRD implications remain proposals.

Current status: Partially validated with a realistic input fixture plus deterministic interview artifact generation covered by `tests/test_prd_direction.py`.

Next gap: Add broader acceptance checks for decision-log and weekly-brief quality, or validate a second interview fixture with a different segment/contradiction pattern.

## Support ticket cluster

Target user: PM or support lead reviewing repeated support issues.

User job: Identify recurring product pain, severity, affected segment, likely root cause, support impact, and product follow-ups from a cluster of tickets.

Input fixture: `examples/inputs/003-support-ticket-cluster.md`

Expected artifacts:
- discovery note;
- customer insight update;
- open questions;
- decision or triage proposal;
- PRD update proposal if repeated support pain implies a product change;
- weekly brief entry.

Acceptance criteria:
- The output groups repeated issues without exaggerating sample size.
- Ticket statements are preserved as source-linked evidence.
- Severity and confidence are labeled.
- The workflow does not create tickets or change external systems.
- The workflow remains product-memory synthesis, not support operations automation.

Current status: Partially validated with a realistic support-cluster fixture plus deterministic artifact generation covered by `tests/test_prd_direction.py`.

Next gap: Add broader acceptance checks for decision/triage quality, or validate a second support cluster with a different severity/confidence pattern.

## Internal product decision discussion

Target user: Product/design/engineering trio deciding between product options.

User job: Preserve the decision, context, options considered, rationale, risks, reversibility, and follow-ups.

Input fixture: `examples/inputs/004-internal-decision-discussion.md`

Expected artifacts:
- decision log entry;
- discovery note if context/evidence is substantial;
- open questions;
- PRD update proposal if the decision changes requirements;
- weekly brief entry.

Acceptance criteria:
- Options considered are captured.
- The decision status is clear: decided, proposed, or pending.
- Rationale and risks are explicit.
- Reversibility is labeled.
- The output does not silently rewrite the PRD.

Current status: Partially validated with a realistic internal-decision fixture plus deterministic artifact generation covered by `tests/test_prd_direction.py`.

Next gap: Add broader acceptance checks for decision quality, or validate a second decision discussion with a different status/reversibility pattern.

## Product brainstorm

Target user: Founder or PM exploring rough product ideas.

User job: Separate ideas, assumptions, hypotheses, non-goals, risks, and next actions from a messy brainstorm.

Input fixture: Missing — proposed path `examples/inputs/005-product-brainstorm.md`

Expected artifacts:
- discovery note;
- open questions;
- opportunity themes;
- possible PRD update proposal only if enough evidence exists;
- weekly brief entry.

Acceptance criteria:
- Ideas are not treated as validated facts.
- Assumptions and hypotheses are labeled.
- Non-goals are preserved when stated.
- The workflow recommends validation steps instead of prematurely prioritizing roadmap items.
- The output stays inside the Product Discovery Memory Agent direction.

Current status: Not yet validated.

Next gap: Add fixture and assumption-vs-fact checks.

## Weekly synthesis from multiple inputs

Target user: PM, founder, or product ops lead preparing a weekly product update.

User job: Combine multiple product inputs into a concise weekly brief with discovery signals, decisions, pending decisions, PRD proposals, open questions, risks, and next actions.

Input fixture: Missing — proposed approach: run the capture workflow across all sample inputs and generate `examples/workspace/Weekly Briefs/weekly-brief-demo.generated.md`.

Expected artifacts:
- weekly product brief;
- source list;
- decision summary;
- open question summary;
- PRD/spec proposal summary;
- recommended next actions.

Acceptance criteria:
- Every major claim links back to source input(s).
- The brief distinguishes decisions made from decisions pending.
- PRD update proposals are summarized, not silently applied.
- The brief is concise enough for a PM/product trio to read quickly.
- The workflow does not become a generic status-reporting or project-management system.

Current status: Not yet validated.

Next gap: Generalize the script to process multiple inputs and synthesize a combined weekly brief.

## Validation commands

Run these before claiming the repo is user-test-ready:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
python3 -m unittest discover -v
python3 -m py_compile scripts/*.py tests/*.py
git diff --check
```

## Readiness rubric

A use case is **Ready for user test** when:

- it has a realistic input fixture;
- it has expected artifacts documented here;
- automated tests or checks validate the key acceptance criteria;
- generated outputs preserve source-linked evidence;
- generated outputs separate facts from assumptions;
- PRD/spec implications are proposals requiring approval;
- a PM/founder can understand the output without explanation.

The MVP is **ready for a real user test** when at least four core use cases are ready and `docs/user-test-guide.md` exists with a 5–10 minute test script.

Current user-test-script status: `docs/user-test-guide.md` exists for the customer feedback demo and should be expanded as additional use cases become ready.
