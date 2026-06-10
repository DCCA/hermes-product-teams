#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureInput:
    slug: str
    title: str
    source: str
    date: str
    quotes: list[str]
    pm_note: str
    potential_decision: str
    raw_text: str


DEFAULT_INPUT = Path("examples/inputs/001-customer-feedback-thread.md")
DEFAULT_WORKSPACE = Path("examples/workspace")


def read_capture(path: Path) -> CaptureInput:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    source_match = re.search(r"^Source:\s*(.+)$", text, flags=re.MULTILINE)
    date_match = re.search(r"^Date:\s*(.+)$", text, flags=re.MULTILINE)

    quotes = [
        re.sub(r"^>\s?", "", line).strip()
        for line in text.splitlines()
        if line.strip().startswith(">") and re.sub(r"^>\s?", "", line).strip()
    ]

    pm_note = section_after_heading(text, "PM note")
    potential_decision = section_after_heading(text, "Potential decision needed")

    slug = path.stem
    return CaptureInput(
        slug=slug,
        title=title_match.group(1).strip() if title_match else slug,
        source=source_match.group(1).strip() if source_match else str(path),
        date=date_match.group(1).strip() if date_match else "Unknown date",
        quotes=quotes,
        pm_note=pm_note,
        potential_decision=potential_decision,
        raw_text=text,
    )


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


def render_discovery_note(capture: CaptureInput) -> str:
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
    return f"""## {capture.date} — Activation setup clarity

- What percentage of users connect a source but never complete activation?
- Which setup step blocks users most often?
- Are the three support tickets from the same segment or plan?
- Would a static status panel be enough, or do users need guided remediation?
- Should activation/status panel outrank advanced analytics for the MVP?

Source: `examples/inputs/{capture.slug}.md`
"""


def render_prd_proposal(capture: CaptureInput) -> str:
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
