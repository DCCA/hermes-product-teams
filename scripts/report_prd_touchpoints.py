#!/usr/bin/env python3
"""Deterministic cross-reference report between PRD.md and discovery notes.

For each generated discovery note in the workspace, this script reports which
PRD sections share salient terms with the note (so a PM can judge whether new
evidence touches existing requirements) and flags notes with no PRD touchpoint
at all — the first signal that the PRD may be stale relative to discovery.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "examples" / "workspace"
DEFAULT_MIN_OVERLAP = 3

# Words that are too generic to indicate a real PRD touchpoint. The second
# group is repo-specific boilerplate (every artifact mentions "product",
# "PRD", "source", ...) that otherwise matches every section trivially.
STOPWORDS = frozenset(
    """
    a about across after all also an and any are as at be became because
    become becomes been before but by
    can cannot could did do does done down each else few for from get given
    had hard has have her here him his how if in into is it its just least
    may means more most much must near need needed no nor not now of off on
    once one only or other our out over own per put rather same see should so
    some still such than that the their them then there these they this those
    three through to too two under until up upon use used very want wants was
    we well were what when where whether which while who why will with within
    without would yet you your
    """.split()
    + """
    add adopting agent ai area artifact artifacts changed changes clear date
    direct discovery doc docs evidence every example examples generated
    important input inputs item items keep latest like make new next note
    notes pm prd prds priority product products proposal proposals propose
    proposed sample section sections source sources spec specs status summary
    system tags team teams type update updates user users using week work
    workspace
    """.split()
)

WORD_RE = re.compile(r"[a-z][a-z0-9'’-]*")
SALIENT_HEADINGS = (
    "facts",
    "evidence",
    "pain points",
    "repeated issue pattern",
    "context",
    "raw ideas",
    "customer/user signals",
    "prd/spec update suggestions",
    "requirement implications",
)


@dataclass(frozen=True)
class PrdSection:
    title: str
    terms: frozenset[str]


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for match in WORD_RE.finditer(text.lower()):
        for part in match.group(0).split("-"):
            word = part.strip("'’")
            if len(word) >= 3 and word not in STOPWORDS:
                tokens.add(word)
    return tokens


def parse_prd_sections(prd_text: str) -> list[PrdSection]:
    sections: list[PrdSection] = []
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_title is not None:
            body = "\n".join(current_lines)
            sections.append(PrdSection(title=current_title, terms=frozenset(tokenize(body))))

    for line in prd_text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            flush()
            current_title = heading.group(1)
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    flush()
    return sections


def extract_salient_terms(note_text: str) -> set[str]:
    salient_chunks: list[str] = []
    title_match = re.search(r"^#\s+(.+)$", note_text, flags=re.MULTILINE)
    if title_match:
        salient_chunks.append(title_match.group(1))
    summary_match = re.search(r"^Summary:\s*(.+)$", note_text, flags=re.MULTILINE)
    if summary_match:
        salient_chunks.append(summary_match.group(1))
    for heading in SALIENT_HEADINGS:
        pattern = rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
        match = re.search(pattern, note_text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if match:
            salient_chunks.append(match.group("body"))

    if salient_chunks:
        return tokenize("\n".join(salient_chunks))
    return tokenize(note_text)


def render_report(workspace: Path, min_overlap: int) -> tuple[str, int]:
    prd_path = workspace / "PRD.md"
    notes_dir = workspace / "Discovery Notes"
    if not prd_path.exists():
        return f"Error: PRD not found at {prd_path}", 1
    if not notes_dir.is_dir():
        return f"Error: Discovery Notes directory not found at {notes_dir}", 1

    sections = parse_prd_sections(prd_path.read_text(encoding="utf-8"))
    note_paths = sorted(notes_dir.glob("*.md"))

    lines: list[str] = [
        "# PRD touchpoint report",
        "",
        f"Workspace: {workspace}",
        f"PRD sections: {len(sections)} | Discovery notes: {len(note_paths)} | Min shared terms: {min_overlap}",
    ]

    touched = 0
    untouched = 0
    for note_path in note_paths:
        note_terms = extract_salient_terms(note_path.read_text(encoding="utf-8"))
        matches: list[tuple[int, str, list[str]]] = []
        for section in sections:
            shared = sorted(note_terms & section.terms)
            if len(shared) >= min_overlap:
                matches.append((len(shared), section.title, shared))
        matches.sort(key=lambda item: (-item[0], item[1]))

        lines.append("")
        lines.append(f"## {note_path.name}")
        if matches:
            touched += 1
            for overlap, title, shared in matches:
                lines.append(f"- {title} (shared terms: {overlap}): {', '.join(shared)}")
        else:
            untouched += 1
            lines.append("- No PRD touchpoint found (possible staleness/coverage gap)")

    lines.append("")
    lines.append(
        f"Summary: {touched} of {len(note_paths)} discovery notes touch the PRD; "
        f"{untouched} have no PRD touchpoint."
    )
    return "\n".join(lines), 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report which PRD sections each discovery note touches (deterministic, stdlib-only)."
    )
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--min-overlap", type=int, default=DEFAULT_MIN_OVERLAP)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report, exit_code = render_report(args.workspace, args.min_overlap)
    print(report)
    if exit_code == 0 and args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
