#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = "product-teams"
DEFAULT_WORKFLOW = ROOT / "hermes" / "profile" / "workflows" / "capture-input.md"


def build_prompt(input_path: Path, workspace: Path, workflow_path: Path) -> str:
    workflow = workflow_path.read_text(encoding="utf-8")
    return f"""You are running the Hermes Product Teams capture workflow.

Workflow instructions:
{workflow}

Input path: {input_path}
Workspace path: {workspace}

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
        default=ROOT / "examples" / "workspace",
        help="Product workspace path.",
    )
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
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
