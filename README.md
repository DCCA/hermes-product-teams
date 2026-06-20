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
│   ├── mvp-plan.md
│   ├── prd-direction.md
│   ├── use-case-validation.md
│   └── user-test-guide.md
├── examples/
│   ├── inputs/
│   └── workspace/
├── hermes/
│   ├── profile/
│   ├── prompts/
│   └── skills/product-team-memory/
├── scripts/
└── tests/
```

## MVP artifacts

The demo workspace uses Markdown files:

- `Product Brief.md`
- `Customer Insights.md`
- `Decision Log.md`
- `Open Questions.md`
- `PRD Update Proposals.md`
- `PRD.md`
- `Weekly Briefs/`
- `Discovery Notes/`

## Current status

Hermes Product Teams now includes:

1. an installable Hermes profile package under `hermes/profile/`;
2. a **real, non-deterministic LLM capture engine** under `scripts/extract_capture.py` that extracts from arbitrary messy input and machine-verifies every quote against the source; and
3. a deterministic demo harness under `scripts/run_capture_demo.py` that renders the bundled sample fixtures (and honestly refuses inputs it cannot faithfully render).

## Install the actual Hermes profile

From the repository root:

```bash
python3 scripts/install_profile.py --workspace examples/workspace
```

For a fresh product workspace, add `--init-workspace` to create the standard artifact folders and starter Markdown files without overwriting any existing artifacts:

```bash
python3 scripts/install_profile.py \
  --workspace /absolute/path/to/product-workspace \
  --init-workspace
```

To install under a team-specific profile name, pass `--profile-name <name>` using a Hermes-compatible lowercase slug such as `acme-product-memory`. The generated `config.yaml` and packaged runners will use that same profile name by default.

This creates a runnable Hermes profile at:

```text
~/.hermes/profiles/product-teams/
├── config.yaml
├── SOUL.md
├── distribution.yaml
├── workflows/
├── skills/
└── scripts/
    ├── check_profile_install.py
    ├── run_agent_capture.py
    └── run_weekly_brief.py
```

Verify the installed package and workspace scaffold without making a model call:

```bash
python3 ~/.hermes/profiles/product-teams/scripts/check_profile_install.py
```

The checker confirms the installed profile files exist, the configured workspace has the standard Product Teams artifacts, and the capture/weekly-brief runners render real `hermes chat --profile ... --skills product-team-memory` commands. If the workspace scaffold is missing, rerun the installer with `--init-workspace`.

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

You don't need to save messy inputs (Slack threads, ad-hoc PM notes) to a file first — capture pasted text directly, or pipe it via stdin:

```bash
python3 scripts/run_agent_capture.py \
  --text "Slack thread: two customers say weekly CSV exports keep timing out" \
  --workspace examples/workspace \
  --dry-run

pbpaste | python3 scripts/run_agent_capture.py --workspace examples/workspace --dry-run
```

`--input` and `--text` are mutually exclusive; stdin is only read when neither flag is given and input is piped (not a TTY). For pasted/stdin input the content is embedded in the prompt between `BEGIN/END PASTED INPUT` markers, and the agent is instructed to record the source as user-pasted text with today's date if the text doesn't name a source.

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

## Real LLM capture engine

`scripts/extract_capture.py` is the real engine (roadmap item #1). Unlike the
deterministic demo, it reads any messy input, asks a real model to extract
structure, and **verifies every Evidence quote verbatim against the source before
writing anything** — so its output passes the trust linter by construction, and it
refuses to write artifacts when no quote can be verified (no empty or fabricated
evidence).

```bash
# Provider auto-detects: Anthropic Messages API via ANTHROPIC_API_KEY, else the `claude` CLI.
python3 scripts/extract_capture.py \
  --input examples/inputs/adversarial/101-noisy-slack-thread.md \
  --workspace /tmp/live-workspace

# Pasted text or stdin work too:
python3 scripts/extract_capture.py --text "Slack thread: exports keep timing out" --workspace /tmp/live-workspace
pbpaste | python3 scripts/extract_capture.py --workspace /tmp/live-workspace

# Inspect the exact prompt without calling the model:
python3 scripts/extract_capture.py --input <file> --print-prompt
```

### Splitting noisy multi-topic inputs (UC-206)

A single messy thread often mixes several unrelated signals. With `--split` the
engine segments the input into **distinct topics** and writes one source-traced
discovery note per topic, instead of blurring them into a single note (the exact
failure the deterministic demo showed). Each topic's evidence is verified verbatim
independently; a topic whose evidence can't be verified is **reported, not silently
dropped**, so no signal disappears unnoticed.

```bash
python3 scripts/extract_capture.py \
  --input examples/inputs/adversarial/101-noisy-slack-thread.md \
  --workspace /tmp/live-workspace --split
# → e.g. four notes: CSV export reliability, xlsx format, SSO-before-renewal, pricing-comms confusion
```

Then verify the generated artifacts:

```bash
python3 scripts/check_workspace.py --workspace /tmp/live-workspace --inputs examples/inputs
```

Because the engine output is non-deterministic, it is **not** committed to
`examples/workspace/` (which stays the stable deterministic demo). Unit tests cover
prompt building, response parsing, quote verification, and rendering offline; an
end-to-end test against a live provider runs only when `EXTRACT_CAPTURE_LIVE=1`.

## Deterministic demo and validation

Run:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
python3 -m unittest discover -v
```

The deterministic demo renders the bundled sample fixtures only; it refuses inputs
it does not recognize (pointing you at the real engine above) rather than
fabricating a narrative. It transforms `examples/inputs/001-customer-feedback-thread.md` into:

- a generated discovery note;
- customer insight updates;
- a proposed decision-log entry;
- open questions;
- a PRD update proposal;
- a weekly product brief.

### PRD touchpoint report

To see which PRD sections each generated discovery note touches — and which notes have no PRD touchpoint at all (an early staleness/coverage signal) — run:

```bash
python3 scripts/report_prd_touchpoints.py
```

The report lists, per discovery note, the PRD sections sharing salient terms (with the shared terms shown so a PM can judge relevance), prints `No PRD touchpoint found` for uncovered notes, and ends with a coverage summary. Use `--min-overlap` to tune sensitivity and `--output <path>` to also write the report to a file.

For manual validation, use `docs/user-test-guide.md` to run a 5–10 minute user test of the customer feedback demo before expanding to additional use cases.

## Eval harness

`scripts/run_eval_harness.py` installs the Hermes profile into a temporary runtime, clones a clean copy of the example product workspace, runs capture against the eval cases in `examples/evals/cases.json`, generates a weekly brief, and then runs the workspace trust checker. This is the closest repo-native check that the package is still runnable as a Hermes Product Teams agent rather than only a set of docs.

Run a cheap smoke case:

```bash
python3 scripts/run_eval_harness.py \
  --cases examples/evals/smoke-case.json \
  --output reports/smoke-eval-report.md
```

Run the broader eval set:

```bash
python3 scripts/run_eval_harness.py \
  --output reports/latest-eval-report.md
```

For experiments, pass `--prompt-suffix` to append a temporary instruction to every capture and brief prompt without editing the packaged workflow files. When a case fails, the Markdown report includes the command stdout/stderr tail so install/config/profile errors are visible in the saved report.
