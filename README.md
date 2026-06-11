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

Initial scaffold plus first deterministic capture demo. Run:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
python3 -m unittest tests.test_prd_direction -v
```

The demo transforms `examples/inputs/001-customer-feedback-thread.md` into:

- a generated discovery note;
- customer insight updates;
- a proposed decision-log entry;
- open questions;
- a PRD update proposal;
- a weekly product brief.
