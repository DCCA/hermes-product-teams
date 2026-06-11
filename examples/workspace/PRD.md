# PRD

## Overview

Hermes Product Teams is a **Product Discovery Memory Agent** for product teams. It is a product team memory layer that turns messy customer/team inputs into source-linked discovery notes, customer insights, decision records, PRD update proposals, open questions, and weekly product briefs.

The MVP should prove that a PM can use Hermes to keep product context current without adopting a new heavyweight product-management suite.

## Problem

Product teams lose context across customer calls, support tickets, chat threads, product docs, issue trackers, and weekly updates. This creates repeated work and unclear rationale:

- customer evidence becomes disconnected from roadmap or PRD changes;
- decisions are hard to reconstruct later;
- PRDs/specs fall behind the latest discovery;
- weekly updates require manual synthesis;
- teams cannot easily separate facts, assumptions, and recommendations.

## Target users

- Startup PMs and founders who collect product feedback from many lightweight channels.
- Product/design/engineering trios that need shared discovery memory.
- Product ops or growth teams that want a local/private AI-assisted product documentation workflow.

## Goals

- Capture messy product inputs into structured discovery notes.
- Maintain customer insights with source-linked evidence.
- Record decisions and pending decision proposals with rationale.
- Generate PRD update proposals rather than silently changing the PRD.
- Produce weekly product briefs for product teams.
- Keep the workflow useful in a local/private Markdown workspace before integrations.

## Non-goals

- Do **not replace Productboard**, Jira Product Discovery, Linear, Jira, Dovetail, Maze, Sprig, Notion, or Confluence.
- Do **not silently modify source-of-truth docs**.
- Do not own final roadmap prioritization in the MVP.
- Do not run surveys, recruit users, or manage research panels.
- Do not claim revenue-weighted prioritization or product analytics without integrations.
- Do not create tickets, send stakeholder messages, or change external systems without explicit approval.

## Requirements

### R1 — Capture messy product input

Given a rough customer/team/product input, the system should classify it and extract facts, assumptions, evidence, decisions, open questions, PRD implications, and next actions.

### R2 — Preserve source-linked evidence

Every important insight, decision proposal, or PRD update proposal should reference the source input and include direct evidence where available.

### R3 — Maintain product-memory artifacts

The workspace should maintain:

- discovery notes;
- customer insights;
- decision log entries;
- open questions;
- PRD update proposals;
- weekly product briefs.

### R4 — Propose PRD/spec changes safely

The system should produce **PRD update proposals** and not silently apply important changes to `PRD.md` without approval.

### R5 — Generate weekly product communication

The system should summarize discovery signals, decisions, pending decisions, PRD/spec proposals, open questions, risks, and recommended next actions.

## Success metrics

For the MVP demo:

- A sample messy input produces all required artifact types.
- Generated artifacts include source-linked evidence.
- PRD changes are proposed, not silently applied.
- A PM can understand what changed, why it matters, and what to do next.
- The demo runs with a repeatable command and lightweight checks.

For a future user-facing version:

- Reduce time spent writing discovery summaries and weekly updates.
- Increase traceability from decisions to evidence.
- Reduce stale or contradictory PRD/spec content.

## Open questions

- Should the next implementation be deterministic, LLM-assisted, or hybrid?
- Which input shape should be generalized next: customer feedback thread, meeting notes, support tickets, or product brainstorms?
- Should the first real integration be Telegram/Slack capture, GitHub/Linear issue context, or Notion/Docs export?
- What is the smallest approval/diff workflow that feels trustworthy?

## Decisions

- Start with **Discovery + Living Docs Agent** as the product direction.
- Focus on the **memory/discovery/docs layer**, not full product management.
- Use Markdown workspace artifacts for the MVP.
- Keep important PRD/spec edits as proposed changes requiring human approval.
