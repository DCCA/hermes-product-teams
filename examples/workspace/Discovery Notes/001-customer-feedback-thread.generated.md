# Sample Input 001 — Customer feedback thread

Type: Customer Feedback / Roadmap Signal
Area: Product Discovery / Activation
Summary: Multiple customer/support signals suggest users are getting stuck after connecting a first data source because setup state and next steps are unclear.
Source: Simulated Slack thread from customer-facing team
Date: 2026-06-10

## Facts

- Customers find the onboarding checklist helpful.
- At least one customer does not know which step is blocking setup when setup fails.
- At least one customer asked for a clear next best action after connecting the first data source.
- Support saw three related tickets in one week where users connected a source but did not complete activation.

## Evidence

- “Customer A says the onboarding checklist is helpful, but they don't know which step is blocking them when setup fails.”
- “Customer B asked if we can show a clear "next best action" after connecting their first data source.”
- “Support noticed three tickets this week where users connected a source but never completed activation.”

## Assumptions

- The activation issue may be caused more by unclear setup state than by missing advanced features.
- A setup status panel could reduce support tickets and improve activation completion.

## Customer/user signals

- Segment: new or activating users connecting their first data source.
- Pain: unclear status and unclear next step after partial setup.
- Possible desired outcome: show what is complete, what is blocked, and what to do next.

## Decisions

- No final decision yet.
- Proposed decision to evaluate: prioritize activation/status panel before advanced analytics.

## Open questions

- How many users connect a source but fail activation?
- Which exact setup step fails most often?
- What is the current activation completion rate?
- Would a status panel alone solve the problem, or is a guided workflow needed?

## PRD/spec update suggestions

- Add an activation status panel requirement.
- Add a next-best-action recommendation after first source connection.
- Add success metric: reduce connected-but-not-activated users and related support tickets.

## Next actions

1. Quantify the activation drop-off after first source connection.
2. Review the three support tickets for common failure modes.
3. Sketch the smallest activation status panel.
4. Decide whether this outranks advanced analytics in the MVP.

## Priority

High — activation blocker near onboarding.

## Tags

#customer-feedback #activation #onboarding #prd-proposal #decision-needed
