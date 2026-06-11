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


DEFAULT_INPUT = Path("examples/inputs/001-customer-feedback-thread.md")
DEFAULT_WORKSPACE = Path("examples/workspace")


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Hermes Product Teams capture demo.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args()

    written = run(args.input, args.workspace)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
