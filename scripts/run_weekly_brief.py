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
    repo_path = ROOT / "hermes" / "profile" / "workflows" / "weekly-brief.md"
    installed_path = ROOT / "workflows" / "weekly-brief.md"
    if repo_path.exists():
        return repo_path
    if installed_path.exists():
        return installed_path
    raise FileNotFoundError("Could not locate weekly-brief.md workflow")


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


def build_prompt(workspace: Path, workflow_path: Path) -> str:
    workflow = workflow_path.read_text(encoding="utf-8")
    target_dir = workspace / "Weekly Briefs"
    return f"""You are running the Hermes Product Teams weekly brief workflow.

Workflow path: {workflow_path}

Workflow instructions:
{workflow}

Workspace path: {workspace}
Target weekly brief directory: {target_dir}

Read the configured workspace artifacts and produce the weekly product brief for that workspace.
When Hermes has file-write access, write the brief into the target weekly brief directory using the workflow's naming convention.
Preserve source-linked evidence, separate facts from assumptions, summarize PRD/spec updates only as proposals, and do not silently edit source-of-truth docs.
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
    parser = argparse.ArgumentParser(
        description="Run Hermes Product Teams weekly brief generation via Hermes."
    )
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

    prompt = build_prompt(args.workspace, args.workflow)
    command = build_command(args.profile, prompt)

    if args.dry_run:
        print(shlex.join(command))
        return 0

    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
