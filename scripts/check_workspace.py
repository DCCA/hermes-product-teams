#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "examples" / "workspace"
DEFAULT_INPUTS = ROOT / "examples" / "inputs"

# Characters that open or close a quoted span, normalized away before matching.
_OPEN_QUOTES = "“\"‘'"
_CLOSE_QUOTES = "”\"’'"

GENERATED_BLOCK_DOCS = [
    "Customer Insights.md",
    "Decision Log.md",
    "Open Questions.md",
    "PRD Update Proposals.md",
]

# Every generated discovery note must keep evidence (facts, quotes) visibly
# separated from speculation. Verified empirically across all five fixture
# kinds: each note has an `## Evidence` section, plus at least one explicitly
# speculative section. The speculative heading varies by kind (e.g. the
# brainstorm note has `## Assumptions` but no `## Facts`, the decision note
# has `## Risks` but neither `## Facts` nor `## Assumptions`).
SPECULATIVE_HEADINGS = [
    "Assumptions",
    "Assumptions to validate",
    "Hypotheses",
    "Likely root causes",
    "Risks",
]

GENERATED_BLOCK_PATTERN = re.compile(
    r"<!-- generated:(?P<marker>[^>]+?):start -->\n(?P<body>.*?)<!-- generated:(?P=marker):end -->",
    re.DOTALL,
)


def has_line(text: str, prefix: str) -> bool:
    return re.search(rf"^{re.escape(prefix)}:", text, flags=re.MULTILINE) is not None


def heading_names(text: str) -> set[str]:
    return {match.strip() for match in re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)}


def section_bullets(text: str, heading: str) -> list[str]:
    """Return the `- ` bullet contents under a `## heading`, until the next `## `."""
    bullets: list[str] = []
    in_section = False
    for line in text.splitlines():
        if re.match(rf"^##\s+{re.escape(heading)}\s*$", line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("- "):
            bullets.append(line.strip()[2:].strip())
    return bullets


def normalize(text: str) -> str:
    """Normalize quote/dash variants, case, and whitespace for robust matching."""
    text = unicodedata.normalize("NFKC", text)
    for variant, canonical in [("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), ("–", "-"), ("—", "-")]:
        text = text.replace(variant, canonical)
    return re.sub(r"\s+", " ", text).strip().lower()


def quoted_span(bullet: str) -> str | None:
    """If a bullet is a quotation (wrapped in quote marks), return its inner text."""
    if not bullet or bullet[0] not in _OPEN_QUOTES:
        return None
    return bullet.strip().lstrip(_OPEN_QUOTES).rstrip(_CLOSE_QUOTES).strip()


def slug_from_note(note: Path) -> str:
    return note.name[: -len(".generated.md")]


def find_source_input(slug: str, inputs_dir: Path) -> Path | None:
    matches = sorted(inputs_dir.rglob(f"{slug}.md"))
    return matches[0] if matches else None


def check_evidence_traceability(workspace: Path, inputs_dir: Path) -> tuple[list[str], int, bool]:
    """Verify every quoted Evidence bullet appears verbatim in its source input.

    Matching is verbatim (after quote/whitespace/case normalization), not fuzzy:
    a fuzzy match would accept "Frankenstein quotes" stitched from real fragments,
    which is the exact fabrication failure this check exists to catch.

    Returns (violations, verified_quote_count, skipped). Skipped is True when the
    inputs directory is absent, so arbitrary workspaces without co-located inputs
    still pass the structural checks instead of failing outright.
    """
    notes_dir = workspace / "Discovery Notes"
    if not inputs_dir.is_dir() or not notes_dir.is_dir():
        return [], 0, True

    violations: list[str] = []
    verified = 0
    for note in sorted(notes_dir.glob("*.generated.md")):
        quotes = [q for q in (quoted_span(b) for b in section_bullets(note.read_text(encoding="utf-8"), "Evidence")) if q]
        if not quotes:
            continue
        source = find_source_input(slug_from_note(note), inputs_dir)
        if source is None:
            violations.append(f"{note}: has Evidence quotes but no source input found in {inputs_dir} to verify them")
            continue
        haystack = normalize(source.read_text(encoding="utf-8"))
        for quote in quotes:
            if normalize(quote) in haystack:
                verified += 1
            else:
                violations.append(f"{note}: Evidence quote not found in {source.name}: “{quote[:70]}”")
    return violations, verified, False


def check_discovery_notes(workspace: Path) -> list[str]:
    violations: list[str] = []
    notes_dir = workspace / "Discovery Notes"
    if not notes_dir.is_dir():
        return [f"{notes_dir}: missing Discovery Notes directory"]
    for note in sorted(notes_dir.glob("*.generated.md")):
        text = note.read_text(encoding="utf-8")
        if not has_line(text, "Source"):
            violations.append(f"{note}: missing `Source:` line")
        if not has_line(text, "Type"):
            violations.append(f"{note}: missing `Type:` line")
        headings = heading_names(text)
        if "Evidence" not in headings:
            violations.append(f"{note}: missing `## Evidence` section")
        elif not section_bullets(text, "Evidence"):
            violations.append(f"{note}: empty `## Evidence` section (no source-linked evidence)")
        if not headings.intersection(SPECULATIVE_HEADINGS):
            expected = ", ".join(f"`## {name}`" for name in SPECULATIVE_HEADINGS)
            violations.append(
                f"{note}: no speculative section separating assumptions from facts (expected one of {expected})"
            )
    return violations


def check_generated_blocks(workspace: Path) -> tuple[list[str], int]:
    violations: list[str] = []
    block_count = 0
    for name in GENERATED_BLOCK_DOCS:
        doc = workspace / name
        if not doc.is_file():
            violations.append(f"{doc}: missing artifact file")
            continue
        text = doc.read_text(encoding="utf-8")
        for match in GENERATED_BLOCK_PATTERN.finditer(text):
            block_count += 1
            if not has_line(match.group("body"), "Source"):
                violations.append(
                    f"{doc}: generated block `{match.group('marker')}` missing `Source:` line"
                )
    return violations, block_count


def check_weekly_briefs(workspace: Path) -> list[str]:
    violations: list[str] = []
    briefs_dir = workspace / "Weekly Briefs"
    if not briefs_dir.is_dir():
        return [f"{briefs_dir}: missing Weekly Briefs directory"]
    for brief in sorted(briefs_dir.glob("*.generated.md")):
        text = brief.read_text(encoding="utf-8")
        if "Sources reviewed" not in heading_names(text):
            violations.append(f"{brief}: missing `## Sources reviewed` section")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check workspace artifacts for trust-model invariants: "
        "source-linked evidence, facts separated from assumptions."
    )
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument(
        "--inputs",
        type=Path,
        default=DEFAULT_INPUTS,
        help="Directory of source inputs used to verify Evidence quotes (searched recursively).",
    )
    args = parser.parse_args()
    workspace: Path = args.workspace

    if not workspace.is_dir():
        print(f"{workspace}: workspace directory does not exist")
        return 1

    violations: list[str] = []
    violations.extend(check_discovery_notes(workspace))
    block_violations, block_count = check_generated_blocks(workspace)
    violations.extend(block_violations)
    violations.extend(check_weekly_briefs(workspace))
    quote_violations, verified_quotes, quotes_skipped = check_evidence_traceability(workspace, args.inputs)
    violations.extend(quote_violations)

    if violations:
        print("Workspace trust violations:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    note_count = len(list((workspace / "Discovery Notes").glob("*.generated.md")))
    brief_count = len(list((workspace / "Weekly Briefs").glob("*.generated.md")))
    quote_summary = (
        "quote verification skipped (no inputs dir)"
        if quotes_skipped
        else f"{verified_quotes} Evidence quotes verified against source inputs"
    )
    print(
        f"OK: {note_count} discovery notes, {block_count} generated blocks, "
        f"{brief_count} weekly briefs, {quote_summary} in {workspace}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
