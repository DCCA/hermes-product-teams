#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "examples" / "workspace"

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

    if violations:
        print("Workspace trust violations:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    note_count = len(list((workspace / "Discovery Notes").glob("*.generated.md")))
    brief_count = len(list((workspace / "Weekly Briefs").glob("*.generated.md")))
    print(
        f"OK: {note_count} discovery notes, {block_count} generated blocks, "
        f"{brief_count} weekly briefs pass trust checks in {workspace}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
