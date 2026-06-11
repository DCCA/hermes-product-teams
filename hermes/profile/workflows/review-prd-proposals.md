# Workflow: Review PRD Update Proposals

Use this workflow when the user asks whether proposed PRD/spec changes should be accepted.

## Steps

1. Read `PRD Update Proposals.md` and the relevant source inputs.
2. Compare the proposal against `PRD.md`.
3. Identify the evidence, assumptions, risks, and affected requirements.
4. Check whether the proposal fits the Discovery + Living Docs Agent direction.
5. Recommend one of:
   - accept as written;
   - accept with edits;
   - defer pending more evidence;
   - reject as outside MVP scope.
6. If the user explicitly approves, provide a clear patch/diff for `PRD.md`.

## Guardrails

- Human approval is required before important docs change.
- Never silently edit source-of-truth docs.
- Keep evidence close to every proposed requirement change.
- Do not turn a weak signal into a roadmap commitment.
