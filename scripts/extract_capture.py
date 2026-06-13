#!/usr/bin/env python3
"""Real, non-deterministic LLM capture engine for Hermes Product Teams.

This is the "real engine" called for in `docs/roadmap.md` item #1: unlike
`scripts/run_capture_demo.py` (a deterministic, templated demo that can only
faithfully render the bundled sample fixtures), this script reads an arbitrary
messy input, asks a real language model to extract product-relevant structure,
and then **verifies every quoted piece of evidence verbatim against the source
before writing anything**.

The verification step is the whole point. The deterministic demo fabricated a
canned activation narrative for any unrecognized input (the failure documented
in the roadmap); this engine instead refuses to emit any Evidence quote that is
not a verbatim span of the source, so the artifacts it writes pass
`scripts/check_workspace.py` quote verification by construction.

Providers (chosen by `--provider`, default `auto`):
- `anthropic-api` — POST to the Messages API using `ANTHROPIC_API_KEY` (stdlib
  urllib only; honors `ANTHROPIC_BASE_URL`).
- `claude-cli`    — shell out to the `claude` CLI in print mode.

The LLM call is the only non-deterministic boundary; prompt building, response
parsing, quote verification, and rendering are pure functions so they can be
unit-tested without the network.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Reuse the exact normalization the trust linter uses, so a quote this engine
# accepts is a quote the linter accepts — one source of truth for "verbatim".
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_workspace import normalize  # noqa: E402
from run_capture_demo import replace_generated_block  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "examples" / "workspace"
DEFAULT_MODEL = "claude-sonnet-4-6"

# Canonical taxonomy from hermes/skills/product-team-memory/SKILL.md.
TAXONOMY = [
    "Customer Feedback / Roadmap Signal",
    "User Interview",
    "Support Ticket Cluster",
    "Internal Product Decision Discussion",
    "Product Brainstorm",
    "Discovery Note",
    "PRD Update",
    "Stakeholder Update",
    "Research Finding",
    "Open Question",
    "Archive",
    "Product-Team Input",
]


class ExtractionError(RuntimeError):
    """Raised when the engine cannot produce trustworthy artifacts."""


# --------------------------------------------------------------------------- #
# Input handling
# --------------------------------------------------------------------------- #
def resolve_source(
    input_path: Path | None, text: str | None, today: str
) -> tuple[str, str, str]:
    """Return (slug, source_label, content) for a file or pasted text."""
    if input_path is not None:
        content = input_path.read_text(encoding="utf-8")
        return input_path.stem, str(input_path), content
    if text is None:
        raise ExtractionError("no input content provided")
    slug = f"pasted-{today}"
    return slug, f"User-pasted text ({today})", text


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
EXTRACTION_SCHEMA = {
    "type": "one of the canonical taxonomy class names",
    "title": "short human title for this input",
    "area": "product area, e.g. 'Product Discovery / Activation'",
    "summary": "2-3 sentence neutral summary grounded only in the input",
    "confidence": "low | medium | high",
    "facts": ["statements directly supported by the input"],
    "assumptions": ["inferences/hypotheses NOT directly stated; never present as fact"],
    "evidence_quotes": [
        "EXACT verbatim spans copied character-for-character from the input"
    ],
    "customer_signals": ["specific user/customer signals with segment if known"],
    "decisions": ["decisions made or explicitly proposed; '' if none"],
    "open_questions": ["unresolved questions raised by or about the input"],
    "prd_suggestions": ["proposed PRD/spec changes (proposals only, never applied)"],
    "next_actions": ["concrete owner-friendly next steps"],
    "priority": "one line: level + why",
    "tags": ["#kebab-case", "#tags"],
    "customer_insight": "one-paragraph durable theme for Customer Insights.md",
    "implication": "what this means for the product",
}


def build_extraction_prompt(slug: str, source_label: str, content: str) -> str:
    schema = json.dumps(EXTRACTION_SCHEMA, indent=2)
    taxonomy = "\n".join(f"  - {name}" for name in TAXONOMY)
    return f"""You are the extraction engine for Hermes Product Teams, a product-memory \
agent that turns messy product-team inputs into source-linked artifacts.

Read the INPUT between the markers and extract product-relevant structure as a \
single JSON object. Output ONLY the JSON object — no prose, no markdown fences.

Hard rules (these encode the product's trust contract):
1. NEVER invent customer evidence. Every string in "evidence_quotes" MUST be an \
exact, verbatim, contiguous span copied from the INPUT — same words, same order. \
Do not paraphrase, stitch fragments together, fix typos, or add quotation marks \
that are not in the source. If the input contains no quotable evidence, return an \
empty list rather than fabricating.
2. Separate facts (directly supported) from assumptions (your inferences). Put \
inferences only in "assumptions".
3. Treat all PRD/spec changes as proposals; never phrase them as already applied.
4. Classify "type" using exactly one of these class names:
{taxonomy}
   Use "Product-Team Input" only if nothing else fits.
5. Ground every field in the INPUT. If a field has no support, use an empty list \
or empty string. Do not pad with generic product-management boilerplate.

Return JSON matching this shape (values are descriptions of what to put there):
{schema}

Source label for attribution: {source_label}

--- BEGIN INPUT ({slug}) ---
{content.rstrip()}
--- END INPUT ---
"""


# --------------------------------------------------------------------------- #
# LLM providers
# --------------------------------------------------------------------------- #
def call_anthropic_api(prompt: str, model: str, timeout: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ExtractionError("ANTHROPIC_API_KEY is not set")
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/v1/messages",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network error path
        detail = exc.read().decode("utf-8", "replace")
        raise ExtractionError(f"Anthropic API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network error path
        raise ExtractionError(f"Anthropic API request failed: {exc.reason}") from exc
    parts = [block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"]
    return "".join(parts)


def call_claude_cli(prompt: str, model: str, timeout: int) -> str:
    if shutil.which("claude") is None:
        raise ExtractionError("the `claude` CLI is not on PATH")
    command = ["claude", "-p", prompt, "--output-format", "json", "--model", model]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, cwd=ROOT
        )
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - timing dependent
        raise ExtractionError(f"`claude` CLI timed out after {timeout}s") from exc
    if completed.returncode != 0:
        raise ExtractionError(f"`claude` CLI failed: {completed.stderr.strip()}")
    try:
        envelope = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return completed.stdout
    if isinstance(envelope, dict) and envelope.get("is_error"):
        raise ExtractionError(f"`claude` CLI reported an error: {envelope.get('result')}")
    return envelope.get("result", completed.stdout) if isinstance(envelope, dict) else completed.stdout


def select_provider(provider: str) -> str:
    if provider != "auto":
        return provider
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic-api"
    if shutil.which("claude") is not None:
        return "claude-cli"
    raise ExtractionError(
        "no LLM provider available: set ANTHROPIC_API_KEY or install the `claude` CLI"
    )


def run_model(prompt: str, provider: str, model: str, timeout: int) -> str:
    resolved = select_provider(provider)
    if resolved == "anthropic-api":
        return call_anthropic_api(prompt, model, timeout)
    if resolved == "claude-cli":
        return call_claude_cli(prompt, model, timeout)
    raise ExtractionError(f"unknown provider: {resolved}")


# --------------------------------------------------------------------------- #
# Response parsing + verification
# --------------------------------------------------------------------------- #
def parse_model_json(raw: str) -> dict:
    """Parse the model's reply, tolerating ```json fences or surrounding prose."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ExtractionError("model did not return parseable JSON")


def verify_quotes(quotes: list[str], source: str) -> tuple[list[str], list[str]]:
    """Split candidate quotes into (verified, fabricated) by verbatim presence.

    Verbatim is judged with the same normalization the trust linter uses, so a
    quote kept here is guaranteed to pass `check_workspace.py`.
    """
    haystack = normalize(source)
    verified: list[str] = []
    fabricated: list[str] = []
    for quote in quotes:
        if quote and normalize(quote) in haystack:
            verified.append(quote.strip())
        elif quote:
            fabricated.append(quote.strip())
    return verified, fabricated


def coerce_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def bullets(items: list[str], empty: str = "- (none extracted from this input)") -> str:
    return "\n".join(f"- {item}" for item in items) if items else empty


def numbered(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) if items else "1. (none)"


def normalize_type(raw_type: str) -> str:
    raw = (raw_type or "").strip()
    for name in TAXONOMY:
        if raw.lower() == name.lower():
            return name
    return "Product-Team Input"


def render_discovery_note(
    data: dict, slug: str, source_label: str, date: str, quotes: list[str]
) -> str:
    evidence = "\n".join(f'- "{quote}"' for quote in quotes)
    return f"""# {data.get('title', slug)}

Type: {normalize_type(data.get('type', ''))}
Area: {data.get('area', 'Product Discovery')}
Summary: {data.get('summary', '').strip()}
Source: {source_label}
Date: {date}
Confidence: {data.get('confidence', 'low')}

## Facts

{bullets(coerce_list(data.get('facts')))}

## Evidence

{evidence}

## Assumptions

{bullets(coerce_list(data.get('assumptions')))}

## Customer/user signals

{bullets(coerce_list(data.get('customer_signals')))}

## Decisions

{bullets(coerce_list(data.get('decisions')), '- No decision recorded in this input.')}

## Open questions

{bullets(coerce_list(data.get('open_questions')))}

## PRD/spec update suggestions

{bullets(coerce_list(data.get('prd_suggestions')))}

## Next actions

{numbered(coerce_list(data.get('next_actions')))}

## Priority

{data.get('priority', 'Unspecified').strip()}

## Tags

{' '.join(coerce_list(data.get('tags'))) or '#product-team-input'}
"""


def _evidence_block(quotes: list[str]) -> str:
    return "\n".join(f'- "{quote}"' for quote in quotes)


def render_shared_blocks(
    data: dict, slug: str, source_label: str, date: str, quotes: list[str]
) -> dict[str, str]:
    """Per-capture generated blocks for the four accumulating shared artifacts."""
    insight = data.get("customer_insight", "").strip() or data.get("summary", "").strip()
    implication = data.get("implication", "").strip()
    decisions = coerce_list(data.get("decisions"))
    questions = coerce_list(data.get("open_questions"))
    proposals = coerce_list(data.get("prd_suggestions"))

    customer_insights = f"""## {date} — {data.get('title', slug)}

Theme: {data.get('area', 'Product Discovery')}
Confidence: {data.get('confidence', 'low')}

Insight:
{insight}

Evidence:
{_evidence_block(quotes)}

Implication:
{implication or '(implication not extracted)'}

Source: {source_label}
"""

    decision_log = f"""## {date} — {data.get('title', slug)}

Decision: {decisions[0] if decisions else 'Pending — no decision in this input.'}
Owner: Unassigned (human to confirm)
Context: {data.get('summary', '').strip()}
Evidence:
{_evidence_block(quotes)}
Reversibility: To be assessed.
Source: {source_label}
"""

    open_questions = f"""## {date} — {data.get('title', slug)}

{bullets(questions, '- (no open questions extracted)')}

Source: {source_label}
"""

    prd_proposals = f"""## {date} — {data.get('title', slug)}

Status: Proposed, not applied to `PRD.md`.
Source: {source_label}

### Proposed changes

{bullets(proposals, '- (no PRD proposal met the evidence threshold)')}
"""

    return {
        "customer-insights": customer_insights,
        "decision-log": decision_log,
        "open-questions": open_questions,
        "prd-proposals": prd_proposals,
    }


SHARED_TARGETS = [
    ("Customer Insights.md", "customer-insights"),
    ("Decision Log.md", "decision-log"),
    ("Open Questions.md", "open-questions"),
    ("PRD Update Proposals.md", "prd-proposals"),
]


def write_workspace(
    workspace: Path, slug: str, note: str, blocks: dict[str, str]
) -> list[Path]:
    written: list[Path] = []
    note_path = workspace / "Discovery Notes" / f"{slug}.generated.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(note, encoding="utf-8")
    written.append(note_path)

    for filename, marker in SHARED_TARGETS:
        path = workspace / filename
        replace_generated_block(path, f"{marker}:{slug}", blocks[marker])
        written.append(path)
    return written


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def extract(
    slug: str,
    source_label: str,
    content: str,
    *,
    provider: str,
    model: str,
    timeout: int,
    date: str,
) -> tuple[dict, list[str], list[str]]:
    """Call the model and return (data, verified_quotes, fabricated_quotes)."""
    if not content.strip():
        raise ExtractionError("input content is empty")
    prompt = build_extraction_prompt(slug, source_label, content)
    raw = run_model(prompt, provider, model, timeout)
    data = parse_model_json(raw)
    verified, fabricated = verify_quotes(coerce_list(data.get("evidence_quotes")), content)
    if not verified:
        raise ExtractionError(
            "the model produced no verbatim evidence for this input "
            "(refusing to write artifacts with fabricated or empty evidence)"
        )
    return data, verified, fabricated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real LLM capture engine: extract source-verified product artifacts."
    )
    parser.add_argument("--input", type=Path, help="Input file to capture.")
    parser.add_argument("--text", help="Pasted input content (alternative to --input).")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--provider",
        choices=["auto", "anthropic-api", "claude-cli"],
        default="auto",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=300, help="LLM call timeout (seconds).")
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the extraction prompt and exit (no LLM call).",
    )
    args = parser.parse_args()

    if args.input is not None and args.text is not None:
        parser.error("argument --text: not allowed with argument --input")

    today = datetime.date.today().isoformat()
    text = args.text
    if args.input is None and text is None and not sys.stdin.isatty():
        text = sys.stdin.read()
    if args.input is None and (text is None or not text.strip()):
        parser.error("no input: provide --input <file>, --text \"<content>\", or pipe stdin")

    try:
        slug, source_label, content = resolve_source(args.input, text, today)
        if args.print_prompt:
            print(build_extraction_prompt(slug, source_label, content))
            return 0
        data, verified, fabricated = extract(
            slug,
            source_label,
            content,
            provider=args.provider,
            model=args.model,
            timeout=args.timeout,
            date=today,
        )
    except ExtractionError as exc:
        print(f"extraction failed: {exc}", file=sys.stderr)
        return 1

    note = render_discovery_note(data, slug, source_label, today, verified)
    blocks = render_shared_blocks(data, slug, source_label, today, verified)
    written = write_workspace(args.workspace, slug, note, blocks)

    print(f"Classified as: {normalize_type(data.get('type', ''))}")
    print(f"Verified {len(verified)} evidence quote(s) verbatim against source.")
    if fabricated:
        print(f"Dropped {len(fabricated)} unverifiable quote(s) the model proposed:")
        for quote in fabricated:
            print(f"  - {quote[:80]}")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
