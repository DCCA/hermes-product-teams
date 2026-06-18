---
name: product-team-memory
description: Use when capturing product-team inputs and maintaining discovery notes, customer insights, decisions, PRD update proposals, and weekly product briefs with source-linked evidence.
version: 0.1.0
author: Hermes Product Teams
license: MIT
metadata:
  hermes:
    tags: [product-management, discovery, prd, decisions, product-ops]
    related_skills: []
---

# Product Team Memory

## Overview

This skill turns messy product-team inputs into maintained product artifacts. It is optimized for product discovery, living docs, decision continuity, and weekly product communication.

It should behave as a careful product-ops assistant: source-linked, explicit about assumptions, and conservative about editing source-of-truth docs.

## When to Use

Use this when the input contains:

- customer/user feedback;
- discovery notes or interview transcripts;
- product ideas or opportunity notes;
- roadmap/product strategy discussion;
- PRD/spec changes;
- product decisions or tradeoffs;
- stakeholder update material.

Do not use it for:

- final roadmap prioritization without human approval;
- financial/account data;
- sending messages to customers or stakeholders;
- changing external tools unless explicitly approved.

## Default Output Contract

For each captured input, produce:

```markdown
# [Title]

Type:
Area:
Summary:
Facts:
Assumptions:
Evidence:
Customer/user signals:
Decisions:
Open questions:
PRD/spec update suggestions:
Next actions:
Priority:
Tags:
Source:
```

## Artifact Rules

Maintain these workspace artifacts:

- `Product Brief.md` — durable product context, audience, and problem framing.
- `Discovery Notes/` — one note per meaningful input or session.
- `Customer Insights.md` — durable themes, quotes, segments, evidence.
- `Decision Log.md` — decisions, rationale, alternatives, reversibility.
- `Open Questions.md` — unresolved discovery/product questions.
- `PRD Update Proposals.md` — proposed PRD/spec edits requiring human approval.
- `PRD.md` — current product requirements snapshot; do not silently edit without approval.
- `Weekly Briefs/` — synthesized product-team updates.

## Safety and Permission Rules

1. Write only inside the configured product workspace.
2. Never silently overwrite source-of-truth docs.
3. For PRD/spec changes, produce a "proposed update" section or diff-style summary first.
4. Preserve sources and evidence for every important claim.
5. Separate facts from assumptions and recommendations.
6. If confidence is low, label it clearly.
7. Never invent customer evidence.

## Classification Taxonomy

This list is the canonical input-classification taxonomy. Workflows (for example
`hermes/profile/workflows/capture-input.md`) and scripts (`scripts/run_capture_demo.py`,
`scripts/run_agent_capture.py`) must use these exact class names — they match the
`Type:` lines rendered in generated discovery notes.

- `Customer Feedback / Roadmap Signal`
- `User Interview`
- `Support Ticket Cluster`
- `Internal Product Decision Discussion`
- `Product Brainstorm`
- `Discovery Note`
- `PRD Update`
- `Stakeholder Update`
- `Research Finding`
- `Open Question`
- `Archive`

Inputs that do not clearly match a class above are treated as generic
`Product-Team Input` until a human classifies them.

## Decision Log Format

```markdown
## YYYY-MM-DD — [Decision]

Decision:
Owner:
Context:
Options considered:
Rationale:
Evidence:
Risks:
Reversibility:
Follow-ups:
Source:
```

## Weekly Brief Format

```markdown
# Weekly Product Brief — YYYY-MM-DD

## Executive summary

## Discovery signals

## Decisions made

## PRD/spec changes proposed

## Open questions and risks

## Roadmap/issue implications

## Recommended next actions

## Sources reviewed
```

## Common Pitfalls

1. **Turning assumptions into facts.** Always label assumptions.
2. **Over-editing docs.** Propose important changes before applying them.
3. **Losing source evidence.** Keep source references close to insights.
4. **Trying to replace roadmap tools.** This skill is the memory/docs layer, not the roadmap authority.
5. **Writing vague insights.** Prefer specific customer/user signals with evidence.

## Verification Checklist

- [ ] Each important insight has a source or is labeled as an assumption.
- [ ] Decisions include rationale and alternatives.
- [ ] PRD changes are proposed, not silently applied, unless approved.
- [ ] Next actions are concrete and owner-friendly.
- [ ] Output separates facts, assumptions, recommendations, and actions.
