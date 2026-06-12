#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = "product-teams"
WORKSPACE_PATTERN = re.compile(r'^\s*path:\s*["\']?([^"\']+)["\']?\s*$')


def resolve_workflow_path() -> Path:
    repo_path = ROOT / "hermes" / "profile" / "workflows" / "capture-input.md"
    installed_path = ROOT / "workflows" / "capture-input.md"
    if repo_path.exists():
        return repo_path
    if installed_path.exists():
        return installed_path
    raise FileNotFoundError("Could not locate capture-input.md workflow")


def resolve_default_workspace() -> Path:
    config_path = ROOT / "config.yaml"
    if config_path.exists():
        in_workspace = False
        for line in config_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped == "workspace:":
                in_workspace = True
                continue
            if in_workspace and line and not line.startswith((" ", "\t")):
                break
            if in_workspace:
                match = WORKSPACE_PATTERN.match(line)
                if match:
                    return Path(match.group(1)).expanduser()
    return ROOT / "examples" / "workspace"


def classify_input(input_path: Path) -> str:
    lowered_name = input_path.name.lower()
    try:
        content = input_path.read_text(encoding="utf-8").lower()
    except OSError:
        content = ""

    interview_markers = [
        "interviewee:",
        "interviewer:",
        "role:",
        "segment:",
        "direct quotes",
        "follow-up questions",
        "assumptions to validate",
    ]
    marker_hits = sum(1 for marker in interview_markers if marker in content)
    if "interview" in lowered_name or marker_hits >= 3:
        return "User Interview"
    return "Product-Team Input"


def interview_extraction_guidance() -> str:
    return """
Additional interview-specific instructions:
- Treat this capture as a User Interview unless the file clearly indicates otherwise.
- Preserve the interview context, interviewee role, and segment.
- Extract direct quotes separately from synthesized insights.
- Distinguish current workflow, pain points, goals, assumptions to validate, follow-up questions, and PRD implications.
- In the discovery note, include:
  - Interviewee role:
  - Segment:
  - Goals:
  - Assumptions to validate:
  - Follow-up questions:
- In artifact proposals, prefer durable customer-insight themes and open questions over premature roadmap commitments.
- Do not silently convert interview evidence into final PRD language; keep PRD/spec changes as proposals with sources.
""".strip()


def build_prompt(input_path: Path, workspace: Path, workflow_path: Path) -> str:
    workflow = workflow_path.read_text(encoding="utf-8")
    input_type = classify_input(input_path)
    extra_guidance = ""
    if input_type == "User Interview":
        extra_guidance = "\n\n" + interview_extraction_guidance()
    return f"""You are running the Hermes Product Teams capture workflow.

Workflow instructions:
{workflow}

Input path: {input_path}
Workspace path: {workspace}
Detected input class: {input_type}{extra_guidance}

Read the input path, then create or propose updates to the configured workspace artifacts. Preserve source-linked evidence, separate facts from assumptions, and do not silently edit source-of-truth docs.
"""


def build_command(profile: str, prompt: str) -> list[str]:
    return [
        "hermes",
        "chat",
        "--profile",
        profile,
        "--skills",
        "product-team-memory",
        "-q",
        prompt,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Hermes Product Teams capture via Hermes.")
    parser.add_argument("--input", type=Path, required=True, help="Input file to capture.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=resolve_default_workspace(),
        help="Product workspace path.",
    )
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--workflow", type=Path, default=resolve_workflow_path())
    parser.add_argument("--dry-run", action="store_true", help="Print command without running Hermes.")
    args = parser.parse_args()

    prompt = build_prompt(args.input, args.workspace, args.workflow)
    command = build_command(args.profile, prompt)

    if args.dry_run:
        print(shlex.join(command))
        return 0

    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
