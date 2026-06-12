# MVP Plan

## Goal

Build a usable demo of Hermes Product Teams as a local/private product-memory workspace.

## Phase 1 — Static workspace and capture workflow

Status: initial demo implemented.

- Define Markdown artifacts. ✅
- Define input classification taxonomy. ✅
- Write the product-team-memory skill. ✅
- Create sample messy product inputs. ✅
- Run the deterministic capture workflow and inspect generated outputs. ✅

Current demo command:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
```

## Phase 2 — Repeatable CLI/script demo

Status: implemented.

- Add a script that applies the workflow to a sample input folder. ✅ (`scripts/run_capture_demo.py --inputs ...`)
- Produce deterministic output files for demos. ✅
- Add basic checks for required sections and source references. ✅ (`scripts/check_scaffold.py`, `tests/`)

## Phase 3 — Hermes profile pack

Status: implemented except gateway setup docs.

- Add example profile config guidance. ✅ (`hermes/profile/`, `scripts/install_profile.py`)
- Add prompts for weekly brief, PRD delta proposal, and decision capture. ✅ (`hermes/profile/workflows/`)
- Add setup docs for using Telegram/Slack-style capture. ⏳

## Phase 4 — Integrations exploration

Candidate integrations, not MVP requirements:

- Slack/Discord/Telegram gateway capture;
- Notion/Google Docs output;
- Linear/Jira issue summaries;
- GitHub discussions/issues;
- Dovetail/Productboard imports;
- CRM/customer-success feedback sources.

## Definition of done for MVP demo

Given 5–10 messy inputs, the repo demo should produce:

- structured discovery notes;
- customer insights with evidence;
- a decision log;
- open questions;
- a PRD update proposal;
- a weekly product brief.

A PM should be able to read the output and say: "This saves me real documentation and synthesis time."
