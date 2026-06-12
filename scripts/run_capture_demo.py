#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureInput:
    slug: str
    kind: str
    title: str
    source: str
    date: str
    quotes: list[str]
    raw_text: str
    pm_note: str = ""
    potential_decision: str = ""
    interviewee_role: str = ""
    segment: str = ""
    current_workflow: list[str] | None = None
    pain_points: list[str] | None = None
    goals: list[str] | None = None
    assumptions_to_validate: list[str] | None = None
    follow_up_questions: list[str] | None = None
    prd_implications: list[str] | None = None
    severity: str = ""
    confidence: str = ""
    affected_segment: str = ""
    ticket_summaries: list[str] | None = None
    repeated_issue_pattern: list[str] | None = None
    likely_root_causes: list[str] | None = None
    support_impact: list[str] | None = None
    product_follow_ups: list[str] | None = None
    decision_status: str = ""
    participants: str = ""
    context_points: list[str] | None = None
    options_considered: list[str] | None = None
    rationale_points: list[str] | None = None
    risks: list[str] | None = None
    reversibility: list[str] | None = None
    decision_follow_ups: list[str] | None = None
    requirement_implications: list[str] | None = None
    brainstorm_participants: str = ""
    raw_idea_cluster: list[str] | None = None
    brainstorm_assumptions: list[str] | None = None
    brainstorm_hypotheses: list[str] | None = None
    brainstorm_non_goals: list[str] | None = None
    brainstorm_risks: list[str] | None = None
    brainstorm_next_actions: list[str] | None = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "examples" / "inputs" / "001-customer-feedback-thread.md"
DEFAULT_WORKSPACE = ROOT / "examples" / "workspace"


def read_capture(path: Path) -> CaptureInput:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    source_match = re.search(r"^Source:\s*(.+)$", text, flags=re.MULTILINE)
    date_match = re.search(r"^Date:\s*(.+)$", text, flags=re.MULTILINE)
    slug = path.stem

    if is_interview_capture(path, text):
        return CaptureInput(
            slug=slug,
            kind="user_interview",
            title=title_match.group(1).strip() if title_match else slug,
            source=source_match.group(1).strip() if source_match else str(path),
            date=date_match.group(1).strip() if date_match else "Unknown date",
            quotes=extract_quotes(text),
            raw_text=text,
            interviewee_role=extract_metadata_value(text, "Role"),
            segment=extract_metadata_value(text, "Segment"),
            current_workflow=extract_bullet_section(text, "Current workflow"),
            pain_points=extract_bullet_section(text, "Pain points"),
            goals=extract_bullet_section(text, "Goals"),
            assumptions_to_validate=extract_bullet_section(text, "Assumptions to validate"),
            follow_up_questions=extract_bullet_section(text, "Follow-up questions"),
            prd_implications=extract_bullet_section(text, "PRD implications"),
        )

    if is_support_ticket_capture(path, text):
        return CaptureInput(
            slug=slug,
            kind="support_ticket_cluster",
            title=title_match.group(1).strip() if title_match else slug,
            source=source_match.group(1).strip() if source_match else str(path),
            date=date_match.group(1).strip() if date_match else "Unknown date",
            quotes=extract_quotes(text),
            raw_text=text,
            severity=extract_metadata_value(text, "Severity"),
            confidence=extract_metadata_value(text, "Confidence"),
            affected_segment=extract_metadata_value(text, "Affected segment"),
            ticket_summaries=extract_bullet_section(text, "Ticket summaries"),
            repeated_issue_pattern=extract_bullet_section(text, "Repeated issue pattern"),
            likely_root_causes=extract_bullet_section(text, "Likely root causes"),
            support_impact=extract_bullet_section(text, "Support impact"),
            product_follow_ups=extract_bullet_section(text, "Product follow-ups"),
        )

    if is_internal_decision_capture(path, text):
        return CaptureInput(
            slug=slug,
            kind="internal_decision_discussion",
            title=title_match.group(1).strip() if title_match else slug,
            source=source_match.group(1).strip() if source_match else str(path),
            date=date_match.group(1).strip() if date_match else "Unknown date",
            quotes=extract_quotes(text),
            raw_text=text,
            decision_status=extract_metadata_value(text, "Decision status"),
            participants=extract_metadata_value(text, "Participants"),
            context_points=extract_bullet_section(text, "Context"),
            options_considered=extract_bullet_section(text, "Options considered"),
            rationale_points=extract_bullet_section(text, "Rationale"),
            risks=extract_bullet_section(text, "Risks"),
            reversibility=extract_bullet_section(text, "Reversibility"),
            decision_follow_ups=extract_bullet_section(text, "Follow-ups"),
            requirement_implications=extract_bullet_section(text, "Requirement implications"),
        )

    if is_product_brainstorm_capture(path, text):
        return CaptureInput(
            slug=slug,
            kind="product_brainstorm",
            title=title_match.group(1).strip() if title_match else slug,
            source=source_match.group(1).strip() if source_match else str(path),
            date=date_match.group(1).strip() if date_match else "Unknown date",
            quotes=extract_quotes(text),
            raw_text=text,
            brainstorm_participants=extract_metadata_value(text, "Participants"),
            raw_idea_cluster=extract_bullet_section(text, "Raw idea cluster"),
            brainstorm_assumptions=extract_bullet_section(text, "Assumptions"),
            brainstorm_hypotheses=extract_bullet_section(text, "Hypotheses"),
            brainstorm_non_goals=extract_bullet_section(text, "Non-goals"),
            brainstorm_risks=extract_bullet_section(text, "Risks"),
            brainstorm_next_actions=extract_bullet_section(text, "Next actions"),
        )

    return CaptureInput(
        slug=slug,
        kind="customer_feedback",
        title=title_match.group(1).strip() if title_match else slug,
        source=source_match.group(1).strip() if source_match else str(path),
        date=date_match.group(1).strip() if date_match else "Unknown date",
        quotes=extract_quotes(text),
        raw_text=text,
        pm_note=section_after_heading(text, "PM note"),
        potential_decision=section_after_heading(text, "Potential decision needed"),
    )


def is_interview_capture(path: Path, text: str) -> bool:
    lowered_name = path.name.lower()
    lowered = text.lower()
    markers = [
        "interviewee:",
        "interviewer:",
        "direct quotes",
        "assumptions to validate",
        "follow-up questions",
    ]
    return "interview" in lowered_name or sum(marker in lowered for marker in markers) >= 3


def is_support_ticket_capture(path: Path, text: str) -> bool:
    lowered_name = path.name.lower()
    lowered = text.lower()
    markers = [
        "ticket summaries",
        "repeated issue pattern",
        "support impact",
        "severity:",
        "confidence:",
    ]
    return "support-ticket" in lowered_name or sum(marker in lowered for marker in markers) >= 4


def is_internal_decision_capture(path: Path, text: str) -> bool:
    lowered_name = path.name.lower()
    lowered = text.lower()
    markers = [
        "decision status:",
        "options considered",
        "reversibility",
        "requirement implications",
        "participants:",
    ]
    return "decision-discussion" in lowered_name or sum(marker in lowered for marker in markers) >= 4


def is_product_brainstorm_capture(path: Path, text: str) -> bool:
    lowered_name = path.name.lower()
    lowered = text.lower()
    markers = [
        "raw idea cluster",
        "assumptions",
        "hypotheses",
        "non-goals",
        "participants:",
    ]
    return "product-brainstorm" in lowered_name or sum(marker in lowered for marker in markers) >= 4


def extract_metadata_value(text: str, field: str) -> str:
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_quotes(text: str) -> list[str]:
    block_quotes = [
        re.sub(r"^>\s?", "", line).strip()
        for line in text.splitlines()
        if line.strip().startswith(">") and re.sub(r"^>\s?", "", line).strip()
    ]
    if block_quotes:
        return block_quotes
    return [item.strip('"') for item in extract_bullet_section(text, "Direct quotes")]


def extract_bullet_section(text: str, heading: str) -> list[str]:
    body = extract_markdown_section(text, heading)
    if not body:
        return []
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def extract_markdown_section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group("body").strip() if match else ""


def section_after_heading(text: str, heading: str) -> str:
    pattern = rf"^\s*{re.escape(heading)}:\s*$\n(?P<body>.*?)(?=\n\s*[A-Z][^\n]+:\s*$|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def replace_generated_block(path: Path, marker: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem}\n\n"
    start = f"<!-- generated:{marker}:start -->"
    end = f"<!-- generated:{marker}:end -->"
    block = f"{start}\n{content.rstrip()}\n{end}\n"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.DOTALL)
    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        updated = existing.rstrip() + "\n\n" + block
    path.write_text(updated, encoding="utf-8")


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def first_item(items: list[str] | None, fallback: str) -> str:
    return items[0] if items else fallback


def render_discovery_note(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        evidence = "\n".join(f"- “{quote}”" for quote in capture.quotes)
        return f"""# {capture.title}

Type: User Interview
Area: Product Discovery / Customer Evidence
Summary: Interview notes reinforce the need for source-linked discovery memory, explicit PRD proposal workflows, and weekly briefs that surface open questions rather than silently editing source-of-truth docs.
Source: {capture.source}
Date: {capture.date}
Interviewee role: {capture.interviewee_role}
Segment: {capture.segment}

## Facts

{bullets(capture.current_workflow or [])}

## Evidence

{evidence}

## Pain points

{bullets(capture.pain_points or [])}

## Goals

{bullets(capture.goals or [])}

## Assumptions to validate

{bullets(capture.assumptions_to_validate or [])}

## Follow-up questions

{bullets(capture.follow_up_questions or [])}

## PRD/spec update suggestions

{bullets(capture.prd_implications or [])}

## Next actions

1. Validate which source has the highest-value product evidence today.
2. Define the approval path for proposed PRD/spec edits.
3. Test whether source-linked weekly briefs help product, design, and engineering leads.

## Priority

High — foundational trust and product-memory workflow signal.

## Tags

#user-interview #discovery #source-linked-evidence #prd-proposal #weekly-brief
"""

    if capture.kind == "support_ticket_cluster":
        evidence = "\n".join(f"- “{quote}”" for quote in capture.quotes)
        return f"""# {capture.title}

Type: Support Ticket Cluster
Area: Product Discovery / Support Evidence
Summary: Repeated export complaints suggest a reliability problem in CSV export flows, with direct support cost and trust risk for weekly reporting workflows.
Source: {capture.source}
Date: {capture.date}
Affected segment: {capture.affected_segment}
Severity: {capture.severity}
Confidence: {capture.confidence}

## Facts

{bullets(capture.ticket_summaries or [])}

## Evidence

{evidence}

## Repeated issue pattern

{bullets(capture.repeated_issue_pattern or [])}

## Likely root causes

{bullets(capture.likely_root_causes or [])}

## Support impact

{bullets(capture.support_impact or [])}

## Product follow-ups

{bullets(capture.product_follow_ups or [])}

## Open questions

- What percentage of CSV exports time out for weekly reports?
- Which report sizes or account tiers correlate with export failure?
- Are scheduled exports failing for the same reason as manual exports?

## PRD/spec update suggestions

- Add explicit export status states and retry guidance.
- Instrument export timeout rate by report size and tier.
- Treat export reliability as a prerequisite before expanding export formats.

## Next actions

1. Pull export timeout metrics by tier and report size.
2. Review job logs for the three ticketed export failures.
3. Decide whether export reliability should outrank net-new export polish.

## Priority

High — repeated customer pain in a visible recurring workflow.

## Tags

#support-ticket-cluster #export-reliability #severity-high #confidence-medium #prd-proposal
"""

    if capture.kind == "internal_decision_discussion":
        evidence = "\n".join(f"- “{quote}”" for quote in capture.quotes)
        return f"""# {capture.title}

Type: Internal Product Decision Discussion
Area: Product Discovery / Decision Memory
Summary: Product, design, and engineering are converging on a proposal-review handoff that keeps discovery-driven requirement changes visible before implementation starts.
Source: {capture.source}
Date: {capture.date}
Decision status: {capture.decision_status}
Participants: {capture.participants}

## Context

{bullets(capture.context_points or [])}

## Evidence

{evidence}

## Options considered

{bullets(capture.options_considered or [])}

## Rationale

{bullets(capture.rationale_points or [])}

## Risks

{bullets(capture.risks or [])}

## Reversibility

{bullets(capture.reversibility or [])}

## Requirement implications

{bullets(capture.requirement_implications or [])}

## Follow-ups

{bullets(capture.decision_follow_ups or [])}

## Priority

Medium-high — affects discovery-to-implementation trust and coordination.

## Tags

#internal-decision #prd-proposal #decision-memory #reversibility #product-trio
"""

    if capture.kind == "product_brainstorm":
        evidence = "\n".join(f"- “{quote}”" for quote in capture.quotes)
        return f"""# {capture.title}

Type: Product Brainstorm
Area: Product Discovery / Idea Framing
Summary: The brainstorm suggests a source-linked weekly customer recap could be a strong wedge, but the ideas are still hypotheses and should remain clearly separated from roadmap commitments.
Source: {capture.source}
Date: {capture.date}
Participants: {capture.brainstorm_participants}

## Raw ideas

{bullets(capture.raw_idea_cluster or [])}

## Evidence

{evidence}

## Assumptions

{bullets(capture.brainstorm_assumptions or [])}

## Hypotheses

{bullets(capture.brainstorm_hypotheses or [])}

## Non-goals

{bullets(capture.brainstorm_non_goals or [])}

## Risks

{bullets(capture.brainstorm_risks or [])}

## Next actions

{bullets(capture.brainstorm_next_actions or [])}

## Priority

Medium — promising direction, but still low-evidence exploration.

## Tags

#product-brainstorm #hypothesis #non-goals #weekly-recap #prd-proposal
"""

    evidence = "\n".join(f"- “{quote}”" for quote in capture.quotes)
    return f"""# {capture.title}

Type: Customer Feedback / Roadmap Signal
Area: Product Discovery / Activation
Summary: Multiple customer/support signals suggest users are getting stuck after connecting a first data source because setup state and next steps are unclear.
Source: {capture.source}
Date: {capture.date}

## Facts

- Customers find the onboarding checklist helpful.
- At least one customer does not know which step is blocking setup when setup fails.
- At least one customer asked for a clear next best action after connecting the first data source.
- Support saw three related tickets in one week where users connected a source but did not complete activation.

## Evidence

{evidence}

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
"""


def render_customer_insights(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        return f"""## {capture.date} — Source-linked product memory from customer-facing teams

Theme: Discovery trust / Product memory
Signal strength: Medium — one realistic interview with specific workflow pain and trust constraints.

Insight:
PMs trust AI-generated discovery notes when direct quotes and source links are visible. Teams want source-linked evidence close to product decisions without silently changing source-of-truth docs.

Evidence:
{chr(10).join(f'- “{quote}”' for quote in capture.quotes)}

Implication:
The MVP should emphasize source-linked evidence, PRD update proposals instead of silent edits, and weekly briefs that surface discovery signals and open questions.

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "support_ticket_cluster":
        return f"""## {capture.date} — Export reliability pain from repeated support tickets

Theme: Support-driven product reliability
Signal strength: {capture.confidence} — three related tickets in one week and direct evidence of repeated customer pain.

Insight:
Customers and support are seeing the same export timeout issue across manual and scheduled export flows, which makes weekly reporting feel unreliable.

Evidence:
{chr(10).join(f'- “{quote}”' for quote in capture.quotes)}

Implication:
Export reliability and visible recovery guidance should be triaged before adding more export formats or reporting polish.

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "internal_decision_discussion":
        return f"""## {capture.date} — Decision-memory handoff before implementation

Theme: Discovery-to-implementation trust
Signal strength: Medium — clear internal alignment pressure from product, design, and engineering.

Insight:
The product trio wants a visible proposal-review checkpoint so discovery-driven requirement changes become implementation-ready without silently mutating `PRD.md`.

Evidence:
{chr(10).join(f'- “{quote}”' for quote in capture.quotes)}

Implication:
The MVP should treat proposal review as the trust-preserving handoff from discovery memory into execution planning.

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "product_brainstorm":
        return f"""## {capture.date} — Structured customer recap as a possible wedge

Theme: Founder-facing synthesis / idea framing
Signal strength: Low-medium — promising wedge ideas, but still early brainstorm territory.

Insight:
A structured customer recap could be a compelling first workflow if it stays source-linked, labels hypotheses clearly, and avoids drifting into roadmap automation.

Evidence:
{chr(10).join(f'- “{quote}”' for quote in capture.quotes)}

Implication:
The MVP can explore a recap-first wedge, but it should keep confidence labeling and non-goals explicit so brainstorm ideas do not look validated.

Source: `examples/inputs/{capture.slug}.md`
"""

    return f"""## {capture.date} — Activation clarity after first source connection

Theme: Onboarding / Activation
Signal strength: Medium — 3 support tickets plus direct customer feedback in sample input.

Insight:
Users can connect an initial data source but still fail to complete activation because they do not understand current setup state, blocking step, or next best action.

Evidence:
{chr(10).join(f'- “{quote}”' for quote in capture.quotes)}

Implication:
Prioritize setup-state visibility before advanced analytics if activation drop-off is confirmed.

Source: `examples/inputs/{capture.slug}.md`
"""


def render_decision_log(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        return f"""## {capture.date} — Proposed decision: keep PRD changes as source-linked proposals

Decision: Pending — validate whether proposed PRD/spec edits with sources should be the default trust model.
Owner: Product lead / PM
Context: Interview feedback says teams want remembered customer evidence and proposed edits with sources, but do not trust silent AI updates to source-of-truth docs.
Options considered:
- Default to PRD update proposals with evidence.
- Allow silent PRD edits.
- Keep notes only, without structured proposal artifacts.
Rationale: Proposal-first behavior preserves trust while still turning messy inputs into usable product memory.
Evidence: See `examples/inputs/{capture.slug}.md` and generated discovery note.
Risks: Could add review overhead if proposal formatting is weak.
Reversibility: High — proposal workflows can evolve without changing source-of-truth docs.
Follow-ups:
- Define approver for proposed PRD/spec edits.
- Validate which source feed should be captured first.
- Test usefulness of weekly briefs across product/design/engineering.
Source: {capture.source}
"""

    if capture.kind == "support_ticket_cluster":
        return f"""## {capture.date} — Proposed decision: triage export performance before adding more export formats

Decision: Pending — evaluate whether export reliability should outrank net-new reporting polish in the near-term backlog.
Owner: Product lead / PM with support input
Context: Multiple support tickets describe repeated CSV export timeouts, unclear retry guidance, and manual report fulfillment for weekly reporting workflows.
Options considered:
- Triage export performance and status guidance first.
- Add more export/reporting polish first.
- Document a support workaround and defer product changes.
Rationale: Repeated reliability failures in a visible recurring workflow can erode trust faster than missing export-format breadth.
Evidence: See `examples/inputs/{capture.slug}.md` and generated discovery note.
Risks: Sample size is still limited and may over-represent one segment.
Reversibility: High — instrumentation and export-status guidance are incremental changes.
Follow-ups:
- Measure export timeout rate by report size and tier.
- Review job logs for the failing export runs.
- Confirm whether scheduled and manual exports share the same bottleneck.
Source: {capture.source}
"""

    if capture.kind == "internal_decision_discussion":
        return f"""## {capture.date} — Proposal-review handoff before implementation

Decision: {capture.decision_status} — standardize on PRD proposal review before implementation starts.
Owner: Product lead / design lead / engineering lead
Context: The team wants discovery insights to influence implementation planning without silently editing `PRD.md`, while giving engineering a clearer requirement handoff.
Options considered:
{bullets(capture.options_considered or [])}
Rationale:
{bullets(capture.rationale_points or [])}
Evidence: See `examples/inputs/{capture.slug}.md` and generated discovery note.
Risks:
{bullets(capture.risks or [])}
Reversibility: {first_item(capture.reversibility, 'High — the decision can be revisited with little structural cost.')}
Follow-ups:
{bullets(capture.decision_follow_ups or [])}
Source: {capture.source}
"""

    if capture.kind == "product_brainstorm":
        return f"""## {capture.date} — Proposed decision: prototype a source-linked weekly recap before broader product-memory expansion

Decision: Pending — validate whether AI-generated customer recap should be the first brainstorm theme to prototype.
Owner: Founder / PM
Context: The brainstorm suggests a weekly recap could be a sticky wedge if it preserves quotes, labels hypotheses clearly, and avoids roadmap-tool drift.
Options considered:
- Start with a structured customer recap as the first artifact.
- Jump straight to a full discovery repository.
- Add action automation before synthesis trust is proven.
Rationale: A recap-first wedge may create immediate founder value while keeping the scope inside discovery memory rather than execution tooling.
Evidence: See `examples/inputs/{capture.slug}.md` and generated discovery note.
Risks: The recap could feel generic or overconfident if evidence is thin.
Reversibility: High — a recap workflow can expand later if repeated use proves real value.
Follow-ups:
{bullets(capture.brainstorm_next_actions or [])}
Source: {capture.source}
"""

    return f"""## {capture.date} — Proposed decision: prioritize activation/status panel before advanced analytics

Decision: Pending — evaluate whether MVP should prioritize an activation/status panel before advanced analytics.
Owner: Product lead / PM
Context: Users are connecting a source but not completing activation; feedback points to unclear setup state and missing next best action.
Options considered:
- Build activation/status panel first.
- Continue with advanced analytics first.
- Add lightweight checklist copy only.
Rationale: Activation blockers near onboarding can prevent users from reaching value; advanced analytics may not matter if users fail setup.
Evidence: See `examples/inputs/{capture.slug}.md` and generated discovery note.
Risks: Could over-index on a small sample without quantitative activation data.
Reversibility: High — can build a lightweight status panel and validate quickly.
Follow-ups:
- Quantify activation drop-off.
- Review support tickets.
- Define smallest status-panel requirement.
Source: {capture.source}
"""


def render_open_questions(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        return f"""## {capture.date} — Discovery trust and PRD proposal workflow

{bullets(capture.follow_up_questions or [])}

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "support_ticket_cluster":
        product_follow_ups = bullets(capture.product_follow_ups or [])
        return f"""## {capture.date} — Export reliability and support load

- What percentage of CSV exports time out for weekly reports?
- Which account tiers or report sizes see the highest export failure rate?
- Are scheduled exports failing for the same reason as manual exports?
- What recovery guidance should users see before they contact support?
- Should export reliability outrank additional export-format work this cycle?

## Product follow-ups from source

{product_follow_ups}

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "internal_decision_discussion":
        return f"""## {capture.date} — Decision-review handoff

- What evidence threshold should trigger a PRD proposal review before implementation?
- Who should approve proposal-only requirement changes?
- Which changes can skip the extra review step without creating trust risk?
- How should weekly briefs summarize pending decision reviews?

Source: `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "product_brainstorm":
        return f"""## {capture.date} — Brainstorm validation questions

- What evidence would prove founders will reuse a generated customer recap each week?
- What confidence labeling is needed so ideas do not look like roadmap commitments?
- Which non-goals must stay visible in every brainstorm-derived artifact?
- When is there enough evidence to attach a PRD proposal to a brainstorm theme?

## Next actions from source

{bullets(capture.brainstorm_next_actions or [])}

Source: `examples/inputs/{capture.slug}.md`
"""

    return f"""## {capture.date} — Activation setup clarity

- What percentage of users connect a source but never complete activation?
- Which setup step blocks users most often?
- Are the three support tickets from the same segment or plan?
- Would a static status panel be enough, or do users need guided remediation?
- Should activation/status panel outrank advanced analytics for the MVP?

Source: `examples/inputs/{capture.slug}.md`
"""


def render_prd_proposal(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        return f"""# PRD Update Proposals

<!-- generated:{capture.slug}:start -->
## {capture.date} — Source-linked evidence and approval-path proposal

Status: Proposed, not applied to `PRD.md`.
Source: `examples/inputs/{capture.slug}.md`

### Problem update

Product teams want AI help turning messy evidence into discovery memory, but they do not trust silent updates to source-of-truth docs.

### Proposed requirement

The product should preserve source-linked evidence and direct quotes in discovery artifacts, then present PRD/spec changes as proposals that require human approval.

### Proposed workflow requirement

- Keep source-linked evidence close to each proposed change.
- Show direct quotes when summarizing product signals.
- Route important requirement changes through a visible approval step.
- Include weekly briefs that surface discovery signals, pending decisions, and open questions.

### Non-goal

Do not silently rewrite `PRD.md`; retain source-linked evidence and proposal-first behavior.
<!-- generated:{capture.slug}:end -->
"""

    if capture.kind == "support_ticket_cluster":
        return f"""# PRD Update Proposals

<!-- generated:{capture.slug}:start -->
## {capture.date} — Export reliability and recovery-guidance proposal

Status: Proposed, not applied to `PRD.md`.
Source: `examples/inputs/{capture.slug}.md`

### Problem update

Repeated support tickets show that CSV exports for weekly reports can time out without clear status or retry guidance, forcing support into manual report delivery.

### Proposed requirement

The product should expose export-job state, failure status, and retry guidance for weekly reporting exports before expanding export-format breadth.

### Proposed workflow requirement

- Instrument export timeout rate by report size and account tier.
- Show queued, running, failed, and retryable export states.
- Provide explicit recovery guidance when an export stalls or times out.
- Label severity/confidence in synthesized support-cluster artifacts.

### Non-goal

Do not create support tickets or automate support operations; keep this as product-memory synthesis and proposal-only PRD updates.
<!-- generated:{capture.slug}:end -->
"""

    if capture.kind == "internal_decision_discussion":
        return f"""# PRD Update Proposals

<!-- generated:{capture.slug}:start -->
## {capture.date} — Proposal-review gate for discovery-driven requirement changes

Status: Proposed, not applied to `PRD.md`.
Source: `examples/inputs/{capture.slug}.md`

### Problem update

Discovery-driven requirement changes can influence implementation planning before the product trio has a shared, visible approval checkpoint.

### Proposed requirement

Important discovery-driven requirement changes should go through a visible PRD proposal review before implementation starts.

### Proposed workflow requirement

{bullets(capture.requirement_implications or [])}

### Non-goal

Do not silently rewrite `PRD.md` or let implementation proceed against AI-generated requirement changes without visible review.
<!-- generated:{capture.slug}:end -->
"""

    if capture.kind == "product_brainstorm":
        return f"""# PRD Update Proposals

<!-- generated:{capture.slug}:start -->
## {capture.date} — No PRD proposal generated yet

Source: `examples/inputs/{capture.slug}.md`
Evidence threshold: not yet met for a concrete requirement proposal.

### Why no proposal yet

- The brainstorm is still primarily a set of ideas, assumptions, and hypotheses.
- The strongest wedge candidate still needs proof of repeated user value.
- Non-goals and trust boundaries are clearer than requirement-level evidence right now.

### What would unlock a proposal

- Evidence that founders repeatedly revisit a source-linked recap artifact.
- Clear proof that recap outputs improve weekly product understanding.
- Stronger signal that a recap-first workflow should become a committed product requirement.

### Current guardrail

Do not turn brainstorm ideas into validated requirements or rewrite `PRD.md` before the evidence threshold is met.
<!-- generated:{capture.slug}:end -->
"""

    return f"""# PRD Update Proposals

<!-- generated:{capture.slug}:start -->
## {capture.date} — Activation/status panel proposal

Status: Proposed, not applied to `PRD.md`.
Source: `examples/inputs/{capture.slug}.md`

### Problem update

Users can connect a first data source but fail to complete activation because setup status, blockers, and next best action are unclear.

### Proposed requirement

The product should show an activation status panel after first data-source connection that includes:

- completed setup steps;
- current blocking step, if any;
- recommended next best action;
- clear recovery guidance when setup fails.

### Proposed success metrics

- Reduce connected-but-not-activated users.
- Reduce support tickets about failed or unclear setup.
- Increase activation completion rate after first source connection.

### Non-goal

Do not build advanced analytics before users reliably complete setup, unless activation data disproves this bottleneck.
<!-- generated:{capture.slug}:end -->
"""


def render_weekly_brief(capture: CaptureInput) -> str:
    if capture.kind == "user_interview":
        return f"""# Weekly Product Brief — {capture.date}

## Executive summary

This week’s strongest discovery signal is about trust: teams want customer evidence remembered with sources, PRD implications proposed rather than silently applied, and weekly briefs that make open product questions visible.

## Discovery signals

- Customer evidence is scattered across support, Slack, calls, and PM notes.
- Teams want source-linked discovery notes with direct quotes.
- Weekly updates currently summarize shipped work better than discovery signals.

## Decisions made

- None finalized.

## Decisions pending

- Who should approve proposed PRD/spec edits?
- Which input source should be validated first for highest-value feedback capture?

## PRD/spec changes proposed

- Preserve source-linked evidence in discovery artifacts.
- Keep PRD/spec changes proposal-first with human approval.
- Treat weekly briefs as a core product-memory output.

## Open questions and risks

- Sample size is still small.
- Trust could break if source links or quotes are weak.
- The team may resist extra review overhead if proposal artifacts are noisy.

## Roadmap/issue implications

- Support-ticket clustering looks like a strong next validated input type.
- Approval-path UX for PRD updates should be treated as a core trust feature.

## Recommended next actions

1. Validate the highest-value input source to capture first.
2. Define approvers for PRD/spec proposals.
3. Test weekly brief usefulness with product, design, and engineering leads.

## Sources reviewed

- `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "support_ticket_cluster":
        return f"""# Weekly Product Brief — {capture.date}

## Executive summary

This week’s strongest support-derived discovery signal is that export reliability is becoming a visible trust issue for recurring weekly reports.

## Discovery signals

- Three related tickets in one week point to repeated CSV export timeouts.
- Customers do not get clear retry guidance or status when exports stall.
- Support is manually fulfilling reports that should be self-serve.

## Decisions made

- None finalized.

## Decisions pending

- Whether to triage export performance before adding more export formats.

## PRD/spec changes proposed

- Add explicit export status and retry guidance.
- Instrument timeout rate by report size and account tier.
- Label Severity/confidence in synthesized support-cluster outputs.

## Open questions and risks

- Severity/confidence: {capture.severity} / {capture.confidence}.
- Sample size is still limited to one cluster.
- The root cause may differ between scheduled and manual exports.

## Roadmap/issue implications

- Export reliability may outrank report-format expansion.
- Instrumentation work should precede broad workflow automation.

## Recommended next actions

1. Measure export timeout rate by report size and tier.
2. Inspect logs for the ticketed export failures.
3. Decide whether export reliability should outrank net-new export polish.

## Sources reviewed

- `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "internal_decision_discussion":
        return f"""# Weekly Product Brief — {capture.date}

## Executive summary

This week’s strongest internal signal is that discovery-driven requirement changes need a clearer proposal-review handoff before implementation starts.

## Discovery signals

- Product, design, and engineering want a visible trust boundary before building against evolving discovery notes.
- The team sees risk in silent PRD changes while implementation is already moving.
- A lightweight review checkpoint could reduce ambiguous requirement shifts.

## Decisions made

- None finalized.

## Decisions pending

- Whether to standardize PRD proposal review before implementation starts.
- Who should approve proposal-only requirement changes.

## PRD/spec changes proposed

{bullets(capture.requirement_implications or [])}

## Open questions and risks

- Decisions pending around approval ownership and evidence threshold.
- An extra review step could slow trivial changes.
- Proposal templates could become noisy if they are not concise.

## Roadmap/issue implications

- Discovery-to-implementation trust should be treated as a first-class workflow feature.
- Weekly briefs should summarize pending proposal reviews and decisions made.

## Recommended next actions

1. Define the minimum evidence threshold for opening a PRD proposal.
2. Decide who approves proposal-only requirement changes.
3. Pilot the review flow for the next two discovery-driven changes.

## Sources reviewed

- `examples/inputs/{capture.slug}.md`
"""

    if capture.kind == "product_brainstorm":
        return f"""# Weekly Product Brief — {capture.date}

## Executive summary

This week’s founder-facing idea signal is that a source-linked customer recap could be a compelling wedge, but the ideas are still hypotheses and need evidence before becoming product commitments.

## Discovery signals

- Founders want one place to review the week’s customer signal without losing quotes.
- Trust increases when evidence is visible and hypotheses are clearly labeled.
- The brainstorm explicitly rejects roadmap-tool drift.

## Decisions made

- None finalized.

## Decisions pending

- Whether a structured customer recap should be the first brainstorm theme to prototype.
- What evidence threshold should trigger a PRD proposal from a brainstorm artifact.

## Potential product implications

- A source-linked weekly customer recap may be a promising first-class artifact.
- Brainstorm-derived outputs should label assumptions, hypotheses, and non-goals explicitly.
- Any PRD implications should remain below the proposal threshold until stronger evidence exists.

## Open questions and risks

- These ideas are still hypotheses, not validated commitments.
- The recap may feel generic if source evidence is too thin.
- Too many generated artifacts could create review fatigue.

## Roadmap/issue implications

- A recap-first wedge may be more testable than a broad discovery platform.
- Confidence labeling should be treated as a trust feature, not polish.

## Recommended next actions

1. Test whether founders revisit a weekly customer recap artifact.
2. Validate the evidence threshold for attaching PRD proposals.
3. Compare recap-only output versus recap plus open questions.

## Sources reviewed

- `examples/inputs/{capture.slug}.md`
"""

    return f"""# Weekly Product Brief — {capture.date}

## Executive summary

The strongest signal this week is an activation clarity issue: users can connect a data source but may not know what is blocking setup or what to do next.

## Discovery signals

- Customers asked for clearer setup status and next best action.
- Support saw three related tickets in one week around source connection without completed activation.

## Decisions made

- None finalized.

## Decisions pending

- Whether the MVP should prioritize an activation/status panel before advanced analytics.

## PRD/spec changes proposed

- Add activation status panel requirement.
- Add next-best-action guidance after first data-source connection.
- Add activation completion and support-ticket reduction as success metrics.

## Open questions and risks

- Quantitative drop-off is not yet known.
- Sample size is small and should be validated.
- Building too much guided setup could delay other MVP scope.

## Recommended next actions

1. Pull activation funnel data for first-source connection to activation completion.
2. Review the three support tickets.
3. Sketch a low-scope status panel.
4. Make a build/defer decision for the activation panel.

## Sources reviewed

- `examples/inputs/{capture.slug}.md`
"""


def run(input_path: Path, workspace: Path) -> list[Path]:
    capture = read_capture(input_path)
    written: list[Path] = []

    discovery_path = workspace / "Discovery Notes" / f"{capture.slug}.generated.md"
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(render_discovery_note(capture), encoding="utf-8")
    written.append(discovery_path)

    targets = [
        (workspace / "Customer Insights.md", "customer-insights", render_customer_insights(capture)),
        (workspace / "Decision Log.md", "decision-log", render_decision_log(capture)),
        (workspace / "Open Questions.md", "open-questions", render_open_questions(capture)),
    ]
    for path, marker, content in targets:
        replace_generated_block(path, marker, content)
        written.append(path)

    prd_proposals = workspace / "PRD Update Proposals.md"
    prd_proposals.write_text(render_prd_proposal(capture), encoding="utf-8")
    written.append(prd_proposals)

    weekly_path = workspace / "Weekly Briefs" / f"weekly-brief-{capture.date}.generated.md"
    weekly_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_path.write_text(render_weekly_brief(capture), encoding="utf-8")
    written.append(weekly_path)

    return written


def source_id(capture: CaptureInput) -> str:
    return capture.slug.split("-", 1)[0]


def format_source_ids(captures: list[CaptureInput]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for capture in captures:
        item = source_id(capture)
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ", ".join(ordered)


def write_discovery_note(capture: CaptureInput, workspace: Path) -> Path:
    discovery_path = workspace / "Discovery Notes" / f"{capture.slug}.generated.md"
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(render_discovery_note(capture), encoding="utf-8")
    return discovery_path


def render_multi_input_weekly_brief(captures: list[CaptureInput]) -> str:
    source_lines = "\n".join(f"- `examples/inputs/{capture.slug}.md`" for capture in captures)

    discovery_captures: list[CaptureInput] = []
    discovery_bullets: list[str] = []
    decision_captures: list[CaptureInput] = []
    decision_bullets: list[str] = []
    pending_captures: list[CaptureInput] = []
    pending_bullets: list[str] = []
    proposal_captures: list[CaptureInput] = []
    proposal_bullets: list[str] = []
    risk_captures: list[CaptureInput] = []
    risk_bullets: list[str] = []
    next_action_captures: list[CaptureInput] = []
    next_action_bullets: list[str] = []

    for capture in captures:
        if capture.kind == "customer_feedback":
            discovery_captures.append(capture)
            discovery_bullets.append(
                "Customers still want a weekly AI summary, but only if it stays grounded in source-linked evidence and next actions."
            )
            pending_captures.append(capture)
            pending_bullets.append(
                "Whether activation/status clarity should be prioritized for the next product change."
            )
            proposal_captures.append(capture)
            proposal_bullets.append(
                "Add clearer workflow support for recurring weekly summaries and pending proposal review."
            )
            next_action_captures.append(capture)
            next_action_bullets.append(
                "Validate which input source delivers the most reusable product signal each week."
            )
        elif capture.kind == "user_interview":
            discovery_captures.append(capture)
            discovery_bullets.append(
                "Interview feedback says trust increases when source links are visible and PRD implications remain proposals."
            )
            pending_captures.append(capture)
            pending_bullets.append(
                "Which source should be validated first as the highest-value product-memory input path."
            )
            proposal_captures.append(capture)
            proposal_bullets.append(
                "Preserve source-linked evidence and direct quotes across discovery outputs."
            )
            risk_captures.append(capture)
            risk_bullets.append(
                "Can the system keep source-linked evidence concise enough for weekly review without becoming noisy?"
            )
        elif capture.kind == "support_ticket_cluster":
            discovery_captures.append(capture)
            discovery_bullets.append(
                "Support signals show export reliability is a concrete trust issue for recurring weekly workflows."
            )
            pending_captures.append(capture)
            pending_bullets.append(
                "Whether export reliability should be prioritized before broader workflow automation."
            )
            proposal_captures.append(capture)
            proposal_bullets.append(
                "Investigate export reliability before expanding into broader workflow automation."
            )
            risk_captures.append(capture)
            risk_bullets.append(
                "Support severity is still based on a limited cluster and needs broader confirmation."
            )
            next_action_captures.append(capture)
            next_action_bullets.append(
                "Measure whether export reliability is causing more immediate weekly pain."
            )
        elif capture.kind == "internal_decision_discussion":
            discovery_captures.append(capture)
            discovery_bullets.append(
                "Internal decision discussion reinforces the need for proposal review before implementation starts."
            )
            decision_captures.append(capture)
            decision_bullets.append(
                "One important team-level conclusion did emerge: discovery-driven requirement changes should flow through proposal review before implementation whenever evidence is still evolving."
            )
            pending_captures.append(capture)
            pending_bullets.append(
                "Who should approve proposed PRD/spec edits before source-of-truth docs change."
            )
            proposal_captures.append(capture)
            proposal_bullets.append(
                "Keep PRD/spec changes proposal-first with human approval."
            )
            next_action_captures.append(capture)
            next_action_bullets.append(
                "Define the approval path and evidence threshold for PRD/spec proposals."
            )
        elif capture.kind == "product_brainstorm":
            discovery_captures.append(capture)
            discovery_bullets.append(
                "The brainstorm suggests a structured customer recap could be a promising wedge, but the idea is still below the evidence threshold."
            )
            pending_captures.append(capture)
            pending_bullets.append(
                "Whether a structured customer recap should be the first brainstorm theme to prototype."
            )
            proposal_captures.append(capture)
            proposal_bullets.append(
                "Treat recap-style outputs as possible product implications, not validated requirements, until stronger evidence exists."
            )
            risk_captures.append(capture)
            risk_bullets.append(
                "Brainstorm ideas remain hypotheses and should not be treated as committed product direction."
            )
            next_action_captures.append(capture)
            next_action_bullets.append(
                "Test whether a structured customer recap actually saves founder/PM review time."
            )

    decision_summary = ["No final product decisions were made this week.", *decision_bullets]
    numbered_next_actions = "\n".join(
        f"{index}. {item}" for index, item in enumerate(next_action_bullets, start=1)
    )
    executive_summary = (
        f"This synthesis combines {len(captures)} product input"
        f"{'s' if len(captures) != 1 else ''} into one weekly view. "
        "The strongest cross-cutting signal is that product teams want source-linked evidence, "
        "clearer trust boundaries for requirement changes, and tighter weekly communication before more automation is added."
    )

    return f"""# Weekly Product Brief — Multi-input Demo

## Executive summary

{executive_summary}

## Discovery signals

Sources: {format_source_ids(discovery_captures)}

{bullets(discovery_bullets)}

## Decisions made

Sources: {format_source_ids(decision_captures) if decision_captures else format_source_ids(captures)}

{bullets(decision_summary)}

## Decisions pending

Sources: {format_source_ids(pending_captures)}

{bullets(pending_bullets)}

## PRD/spec update proposals

Sources: {format_source_ids(proposal_captures)}

{bullets(proposal_bullets)}

## Open questions and risks

Sources: {format_source_ids(risk_captures)}

{bullets(risk_bullets)}

## Recommended next actions

Sources: {format_source_ids(next_action_captures)}

{numbered_next_actions}

## Sources reviewed

{source_lines}
"""


def run_many(input_paths: list[Path], workspace: Path) -> list[Path]:
    written: list[Path] = []
    captures: list[CaptureInput] = []
    for input_path in input_paths:
        capture = read_capture(input_path)
        captures.append(capture)
        discovery_path = write_discovery_note(capture, workspace)
        written.append(discovery_path)

    weekly_demo_path = workspace / "Weekly Briefs" / "weekly-brief-demo.generated.md"
    weekly_demo_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_demo_path.write_text(render_multi_input_weekly_brief(captures), encoding="utf-8")
    written.append(weekly_demo_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Hermes Product Teams capture demo.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--inputs", type=Path, nargs="+")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args()

    if args.inputs:
        written = run_many(args.inputs, args.workspace)
    else:
        written = run(args.input, args.workspace)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
