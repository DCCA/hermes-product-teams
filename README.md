# Hermes Product Teams

A Hermes-based MVP for product teams: a permission-aware product memory agent that turns messy discovery inputs into maintained product artifacts — discovery notes, customer insights, decision logs, PRD update proposals, and weekly product briefs.

## MVP thesis

Product teams do not need another generic AI PM chatbot. They need a trustworthy memory layer that keeps discovery, decisions, and docs current across messy team/customer inputs.

## First wedge

**Discovery + Living Docs Agent**

Given rough inputs such as meeting notes, customer feedback, Slack-style threads, research snippets, or product ideas, the agent should:

1. classify the input;
2. extract product-relevant facts, assumptions, questions, evidence, and decisions;
3. write a structured discovery note;
4. update or propose changes to shared artifacts;
5. prepare a weekly product brief.

## Default permission model

- Read only approved inputs and workspace files.
- Write only inside the configured product workspace.
- Propose diffs for important source-of-truth docs before editing.
- Never send external messages, create issues, change roadmaps, or modify calendars without explicit approval.
- Keep source links/evidence with generated insights.

## Repository structure

```text
.
├── docs/
│   ├── concept.md
│   ├── market-validation.md
│   └── mvp-plan.md
├── examples/
│   ├── inputs/
│   └── workspace/
├── hermes/
│   ├── profile/
│   ├── prompts/
│   └── skills/product-team-memory/
└── scripts/
```

## MVP artifacts

The demo workspace uses Markdown files:

- `Product Brief.md`
- `Customer Insights.md`
- `Decision Log.md`
- `Open Questions.md`
- `PRD.md`
- `Weekly Briefs/`
- `Discovery Notes/`

## Current status

Hermes Product Teams now includes both:

1. an installable Hermes profile package under `hermes/profile/`; and
2. a deterministic demo harness under `scripts/run_capture_demo.py`.

## Install the actual Hermes profile

From the repository root:

```bash
python3 scripts/install_profile.py --workspace examples/workspace
```

This creates a runnable Hermes profile at:

```text
~/.hermes/profiles/product-teams/
├── config.yaml
├── SOUL.md
├── distribution.yaml
├── workflows/
├── skills/
└── scripts/
    ├── run_agent_capture.py
    └── run_weekly_brief.py
```

You can run the packaged scripts directly from the installed profile:

```bash
python3 ~/.hermes/profiles/product-teams/scripts/run_agent_capture.py \
  --input /absolute/path/to/customer-feedback.md \
  --dry-run

python3 ~/.hermes/profiles/product-teams/scripts/run_weekly_brief.py \
  --dry-run
```

After install, both scripts default to the workspace configured in `~/.hermes/profiles/product-teams/config.yaml`, so `--workspace` is optional unless you want to override it.

Or run from the repo checkout while developing:

```bash
python3 scripts/run_agent_capture.py \
  --input examples/inputs/001-customer-feedback-thread.md \
  --workspace examples/workspace \
  --dry-run
```

Run it through Hermes:

```bash
python3 scripts/run_agent_capture.py \
  --input examples/inputs/001-customer-feedback-thread.md \
  --workspace examples/workspace
```

Under the hood this invokes:

```bash
hermes chat --profile product-teams --skills product-team-memory -q "..."
```

Generate the weekly brief the same way:

```bash
python3 scripts/run_weekly_brief.py \
  --workspace examples/workspace \
  --dry-run

python3 scripts/run_weekly_brief.py \
  --workspace examples/workspace
```

## Deterministic demo and validation

Run:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
python3 -m unittest discover -v
```

The deterministic demo transforms `examples/inputs/001-customer-feedback-thread.md` into:

- a generated discovery note;
- customer insight updates;
- a proposed decision-log entry;
- open questions;
- a PRD update proposal;
- a weekly product brief.

For manual validation, use `docs/user-test-guide.md` to run a 5–10 minute user test of the customer feedback demo before expanding to additional use cases.
