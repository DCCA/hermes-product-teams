# Workflow: Capture Product-Team Input

Use this workflow when the user gives Hermes Product Teams customer feedback, interview notes, support snippets, product thoughts, meeting notes, or decision discussions.

## Inputs

- Source input path or pasted text.
- Product workspace path.
- Optional user instruction about whether to write files or only propose updates.

## Steps

1. Read the input and identify its source.
2. Classify the input using the canonical taxonomy from the `product-team-memory` skill (`SKILL.md` "Classification Taxonomy"): Customer Feedback / Roadmap Signal, User Interview, Support Ticket Cluster, Internal Product Decision Discussion, Product Brainstorm, Discovery Note, PRD Update, Stakeholder Update, Research Finding, Open Question, or Archive. Use Product-Team Input as the fallback when nothing matches.
3. Extract facts from assumptions.
4. Preserve direct quotes and source-linked evidence.
5. Create a discovery note using the profile output contract.
6. Propose updates to:
   - `Customer Insights.md`
   - `Decision Log.md`
   - `Open Questions.md`
   - `PRD Update Proposals.md`
7. Do not silently edit `PRD.md`; create a PRD update proposal instead.
8. List next actions and open questions.

## User Interview extraction requirements

When the input is a user interview, also:

- Preserve interview context, interviewee role, and segment.
- Separate direct quotes from synthesized insights.
- Extract the current workflow, pain points, goals, assumptions to validate, follow-up questions, and PRD implications.
- Keep customer-evidence themes and open questions ahead of premature roadmap commitments.
- Treat PRD/spec implications as proposals with sources, not silent source-of-truth edits.

For the discovery note, explicitly include these sections when supported by the input:

- `Interviewee role:`
- `Segment:`
- `Goals:`
- `Assumptions to validate:`
- `Follow-up questions:`

## Required output

Return a concise summary of what was captured, what artifacts were written or proposed, and what needs human approval.
