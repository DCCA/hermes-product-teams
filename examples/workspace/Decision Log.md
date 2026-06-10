# Decision Log

Use this file for durable product decisions.

## Template

Decision:
Owner:
Context:
Options considered:
Rationale:
Evidence:
Risks:
Reversibility:
Follow-ups:
Source:

<!-- generated:decision-log:start -->
## 2026-06-10 — Proposed decision: prioritize activation/status panel before advanced analytics

Decision: Pending — evaluate whether MVP should prioritize an activation/status panel before advanced analytics.
Owner: Product lead / PM
Context: Users are connecting a source but not completing activation; feedback points to unclear setup state and missing next best action.
Options considered:
- Build activation/status panel first.
- Continue with advanced analytics first.
- Add lightweight checklist copy only.
Rationale: Activation blockers near onboarding can prevent users from reaching value; advanced analytics may not matter if users fail setup.
Evidence: See `examples/inputs/001-customer-feedback-thread.md` and generated discovery note.
Risks: Could over-index on a small sample without quantitative activation data.
Reversibility: High — can build a lightweight status panel and validate quickly.
Follow-ups:
- Quantify activation drop-off.
- Review support tickets.
- Define smallest status-panel requirement.
Source: Simulated Slack thread from customer-facing team
<!-- generated:decision-log:end -->
