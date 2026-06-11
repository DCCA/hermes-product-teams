# Workflow: Capture Product-Team Input

Use this workflow when the user gives Hermes Product Teams customer feedback, interview notes, support snippets, product thoughts, meeting notes, or decision discussions.

## Inputs

- Source input path or pasted text.
- Product workspace path.
- Optional user instruction about whether to write files or only propose updates.

## Steps

1. Read the input and identify its source.
2. Classify the input as one of: Customer Feedback, User Interview, Support Ticket Cluster, Product Brainstorm, Decision Discussion, PRD Update Proposal, Weekly Brief Material, or Archive.
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

## Required output

Return a concise summary of what was captured, what artifacts were written or proposed, and what needs human approval.
