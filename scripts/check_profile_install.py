#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_PROFILE_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PROFILE_FILES = [
    "config.yaml",
    "SOUL.md",
    "distribution.yaml",
    "README.md",
    "workspace.example.yaml",
    "workflows/capture-input.md",
    "workflows/weekly-brief.md",
    "workflows/review-prd-proposals.md",
    "skills/product-team-memory/SKILL.md",
    "scripts/check_profile_install.py",
    "scripts/run_agent_capture.py",
    "scripts/run_weekly_brief.py",
]
REQUIRED_WORKSPACE_PATHS = [
    "Product Brief.md",
    "Discovery Notes",
    "Customer Insights.md",
    "Decision Log.md",
    "Open Questions.md",
    "PRD Update Proposals.md",
    "PRD.md",
    "Weekly Briefs",
]


def read_config_workspace(config_path: Path) -> Path | None:
    in_workspace = False
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "workspace:":
            in_workspace = True
            continue
        if in_workspace and line and not line.startswith((" ", "\t")):
            break
        if in_workspace and stripped.startswith("path:"):
            value = stripped.removeprefix("path:").strip().strip('"\'')
            if value:
                return Path(value).expanduser()
    return None


def check_required_files(profile_root: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_PROFILE_FILES:
        if not (profile_root / relative_path).exists():
            missing.append(relative_path)
    return missing


def check_workspace(workspace: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_WORKSPACE_PATHS:
        if not (workspace / relative_path).exists():
            missing.append(relative_path)
    return missing


def run_dry_run(command: list[str], profile_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=profile_root,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an installed Hermes Product Teams profile without calling Hermes."
    )
    parser.add_argument(
        "--profile-root",
        type=Path,
        default=DEFAULT_PROFILE_ROOT,
        help="Installed profile directory to validate. Defaults to this script's containing profile.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Expected workspace path. Defaults to the workspace.path in config.yaml.",
    )
    parser.add_argument(
        "--sample-input",
        type=Path,
        help="Input file to use for the capture dry-run. Defaults to README.md inside the profile.",
    )
    args = parser.parse_args()

    profile_root = args.profile_root.expanduser().resolve()
    errors: list[str] = []

    if not profile_root.exists():
        print(f"Profile root does not exist: {profile_root}")
        return 1

    missing_files = check_required_files(profile_root)
    if missing_files:
        errors.append("Missing installed profile files: " + ", ".join(missing_files))

    config_path = profile_root / "config.yaml"
    configured_workspace = None
    if config_path.exists():
        configured_workspace = read_config_workspace(config_path)
        if configured_workspace is None:
            errors.append("config.yaml does not define workspace.path")

    workspace = args.workspace.expanduser() if args.workspace else configured_workspace
    if workspace is None:
        errors.append("No workspace path available; pass --workspace or fix config.yaml")
    else:
        workspace = workspace.resolve()
        if not workspace.exists():
            errors.append(f"Workspace does not exist: {workspace}")
        else:
            missing_workspace_paths = check_workspace(workspace)
            if missing_workspace_paths:
                errors.append(
                    "Workspace is missing required artifacts: "
                    + ", ".join(missing_workspace_paths)
                    + " (run install_profile.py --init-workspace to create non-overwriting starters)"
                )

    sample_input = args.sample_input.expanduser().resolve() if args.sample_input else profile_root / "README.md"
    if not sample_input.exists():
        errors.append(f"Sample input does not exist: {sample_input}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    capture = run_dry_run(
        [
            sys.executable,
            str(profile_root / "scripts" / "run_agent_capture.py"),
            "--input",
            str(sample_input),
            "--dry-run",
        ],
        profile_root,
    )
    if capture.returncode != 0:
        print("ERROR: capture runner dry-run failed")
        print(capture.stderr or capture.stdout)
        return capture.returncode
    if "hermes chat" not in capture.stdout or "product-team-memory" not in capture.stdout:
        print("ERROR: capture runner dry-run did not render a Hermes product-team-memory command")
        return 1

    weekly = run_dry_run(
        [sys.executable, str(profile_root / "scripts" / "run_weekly_brief.py"), "--dry-run"],
        profile_root,
    )
    if weekly.returncode != 0:
        print("ERROR: weekly brief runner dry-run failed")
        print(weekly.stderr or weekly.stdout)
        return weekly.returncode
    if "hermes chat" not in weekly.stdout or "Weekly Briefs" not in weekly.stdout:
        print("ERROR: weekly brief dry-run did not render the expected Hermes command")
        return 1

    print(f"OK: installed profile is runnable: {profile_root}")
    print(f"OK: workspace scaffold present: {workspace}")
    print("OK: capture and weekly brief runners render Hermes commands without calling Hermes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
