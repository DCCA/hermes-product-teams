# Support Ticket Cluster

Source: Simulated support inbox cluster from customer-facing team
Date: 2026-06-11

Affected segment: Operations managers exporting weekly customer reports
Severity: High
Confidence: Medium

## Ticket summaries

- Ticket 1842: A customer on the Growth plan tried to export a CSV report three times and each export timed out after roughly 90 seconds.
- Ticket 1848: Support had to manually send a report because the scheduled CSV export stalled and showed no recovery guidance.
- Ticket 1851: Another customer said they stop trusting weekly exports when the report spinner runs for several minutes without finishing.

## Direct quotes

- "I waited a couple of minutes and the CSV export never finished."
- "If the export fails, I need to know whether to retry or ask support for the file."
- "We can't promise the Monday report will be ready if exports keep timing out."

## Repeated issue pattern

- Three related export complaints arrived in the same week.
- The same export timeout issue appears across manual and scheduled export flows.
- Customers lack clear retry guidance or status when exports stall.

## Likely root causes

- Export jobs may be timing out for larger weekly reports.
- The UI does not distinguish queued, running, failed, or retryable export states.
- Scheduled exports may share the same timeout bottleneck as manual exports.

## Support impact

- Support is manually fulfilling reports that should be self-serve.
- Trust in weekly exports is dropping for customer-facing operations teams.
- Repeated export failures create churn risk for a visible recurring workflow.

## Product follow-ups

- Quantify timeout rate for CSV exports by report size and account tier.
- Add export status and retry guidance before expanding export format options.
- Decide whether export reliability should outrank net-new reporting polish in the near-term backlog.
