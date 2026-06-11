# Use Case Validation

This checklist keeps the MVP focused on the Product Discovery Memory Agent direction in `docs/prd-direction.md` while making the demo user-testable.

## Acceptance criteria for every sample use case

Each realistic sample input should demonstrate that Hermes Product Teams can:

1. classify the input as a product discovery, customer insight, decision, brainstorm, support, or synthesis signal;
2. extract facts separately from assumptions and recommendations;
3. preserve source-linked evidence in generated artifacts;
4. record decisions as pending/proposed unless already explicit in the source;
5. generate PRD/spec update proposals instead of silently editing `examples/workspace/PRD.md`;
6. leave human-reviewable open questions and next actions;
7. remain inside the memory/discovery/docs layer, avoiding roadmap management, ticketing, research-ops, and generic PM-suite behavior.

## Required MVP sample inputs

| Use case | Required sample | User-test acceptance criteria | Current status |
| --- | --- | --- | --- |
| Customer feedback thread | A Slack/email-style thread with multiple customer quotes and a product implication. | Generated discovery note includes direct quotes as evidence, facts, assumptions, open questions, and a PRD update proposal. | Present: `examples/inputs/001-customer-feedback-thread.md`. |
| User interview notes | Interview notes with participant context, observed pain, direct quotes, and unanswered follow-ups. | Output separates observed facts from interviewer's interpretation and creates source-linked insights without treating one interview as broad proof. | Gap. |
| Support ticket cluster | A cluster of support tickets around one activation/setup/product issue. | Output identifies repeated symptoms, preserves ticket/source references, proposes questions and a possible PRD/spec change without creating tickets. | Gap. |
| Internal product decision discussion | A messy team discussion with options, tradeoffs, risks, and an unresolved or explicit decision. | Output creates a decision record with status, rationale, evidence, reversibility, risks, and follow-ups. | Gap. |
| Product brainstorm | A rough idea dump with opportunities, constraints, and speculative ideas. | Output labels assumptions clearly, avoids converting ideas into commitments, and proposes validation questions. | Gap. |
| Weekly synthesis from multiple inputs | A multi-source weekly rollup from at least two input types. | Weekly brief cites reviewed sources, summarizes signals, decisions, open questions, and proposed next actions. | Partial: current demo produces a weekly brief from one input. |

## Validation commands

Run these before claiming the repo is user-test-ready:

```bash
python3 scripts/run_capture_demo.py
python3 scripts/check_scaffold.py
python3 -m unittest discover -v
python3 -m py_compile scripts/*.py tests/*.py
git diff --check
```

## Next validation gap

Add the remaining required sample inputs and extend the repeatable demo command so one run can process the sample input folder into source-linked product-memory artifacts.
