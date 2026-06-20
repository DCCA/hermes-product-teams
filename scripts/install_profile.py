#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_SOURCE = ROOT / "hermes" / "profile"
SKILL_SOURCE = ROOT / "hermes" / "skills" / "product-team-memory"
SCRIPT_SOURCES = [
    ROOT / "scripts" / "check_profile_install.py",
    ROOT / "scripts" / "run_agent_capture.py",
    ROOT / "scripts" / "run_weekly_brief.py",
]
DEFAULT_PROFILE_NAME = "product-teams"
# Match Hermes' profile selector (`hermes --profile/-p`): lowercase alphanumeric
# profile IDs, with optional underscores/hyphens, up to 64 characters.
PROFILE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
WORKSPACE_DIRECTORIES = ["Discovery Notes", "Weekly Briefs"]
WORKSPACE_FILES = {
    "Product Brief.md": "# Product Brief\n\nCapture the product context, audience, and durable problem framing here.\n",
    "Customer Insights.md": "# Customer Insights\n\nAppend source-linked customer and user insight themes here.\n",
    "Decision Log.md": "# Decision Log\n\nRecord decisions, options considered, rationale, risks, and reversibility here.\n",
    "Open Questions.md": "# Open Questions\n\nTrack unresolved discovery and product questions here.\n",
    "PRD Update Proposals.md": "# PRD Update Proposals\n\nStatus: Proposed, not applied to `PRD.md`.\n\nAdd source-linked PRD/spec change proposals here for human review.\n",
    "PRD.md": "# PRD\n\nSource-of-truth requirements snapshot. Hermes Product Teams should propose changes before this file is edited.\n",
}


def safe_profile_name(value: str) -> str:
    if not PROFILE_NAME_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "profile name must be a Hermes-compatible profile slug: start with a "
            "lowercase letter or number and use 1-64 lowercase letters, numbers, "
            "underscores, or hyphens"
        )
    return value


def copy_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def render_config(profile_root: Path, workspace: Path, profile_name: str) -> None:
    template = (PROFILE_SOURCE / "config.example.yaml").read_text(encoding="utf-8")
    rendered = template.replace("{{WORKSPACE_PATH}}", str(workspace.resolve()))
    rendered = rendered.replace("{{PROFILE_NAME}}", profile_name)
    (profile_root / "config.yaml").write_text(rendered, encoding="utf-8")


def copy_runtime_script(script_path: Path, scripts_root: Path, profile_name: str) -> None:
    content = script_path.read_text(encoding="utf-8")
    content = content.replace(
        'DEFAULT_PROFILE = "product-teams"', f"DEFAULT_PROFILE = {profile_name!r}"
    )
    destination = scripts_root / script_path.name
    destination.write_text(content, encoding="utf-8")


def initialize_workspace(workspace: Path) -> list[Path]:
    created: list[Path] = []
    workspace.mkdir(parents=True, exist_ok=True)

    for directory in WORKSPACE_DIRECTORIES:
        path = workspace / directory
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
        else:
            path.mkdir(parents=True, exist_ok=True)

    for relative_path, content in WORKSPACE_FILES.items():
        path = workspace / relative_path
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(path)

    return created


def install_profile(hermes_home: Path, workspace: Path, profile_name: str) -> Path:
    profile_root = hermes_home / "profiles" / profile_name
    profile_root.mkdir(parents=True, exist_ok=True)

    for relative_path in ["SOUL.md", "distribution.yaml", "workspace.example.yaml", "README.md"]:
        shutil.copy2(PROFILE_SOURCE / relative_path, profile_root / relative_path)

    copy_tree(PROFILE_SOURCE / "workflows", profile_root / "workflows")
    copy_tree(SKILL_SOURCE, profile_root / "skills" / "product-team-memory")

    scripts_root = profile_root / "scripts"
    scripts_root.mkdir(parents=True, exist_ok=True)
    for script_path in SCRIPT_SOURCES:
        copy_runtime_script(script_path, scripts_root, profile_name)

    render_config(profile_root, workspace, profile_name)
    return profile_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the Hermes Product Teams profile.")
    parser.add_argument(
        "--hermes-home",
        type=Path,
        default=Path.home() / ".hermes",
        help="Hermes home directory. Defaults to ~/.hermes.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=ROOT / "examples" / "workspace",
        help="Product workspace path the profile should use.",
    )
    parser.add_argument(
        "--profile-name",
        type=safe_profile_name,
        default=DEFAULT_PROFILE_NAME,
        help="Hermes profile name to create. Defaults to product-teams.",
    )
    parser.add_argument(
        "--init-workspace",
        action="store_true",
        help="Create the standard Product Teams workspace folders and starter artifact files if missing.",
    )
    args = parser.parse_args()

    profile_root = install_profile(args.hermes_home, args.workspace, args.profile_name)
    created_workspace_paths: list[Path] = []
    if args.init_workspace:
        created_workspace_paths = initialize_workspace(args.workspace)
    print(f"Installed Hermes Product Teams profile: {profile_root}")
    print(f"Workspace: {args.workspace.resolve()}")
    if args.init_workspace:
        print(f"Initialized workspace scaffold: {args.workspace.resolve()}")
        if created_workspace_paths:
            for path in created_workspace_paths:
                print(f"  created: {path.resolve()}")
        else:
            print("  no workspace files changed; scaffold already existed")
    print(f"Run capture: python3 {profile_root / 'scripts' / 'run_agent_capture.py'} --input /path/to/input.md")
    print(f"Run weekly brief: python3 {profile_root / 'scripts' / 'run_weekly_brief.py'}")
    print(f"Or run: hermes chat --profile {args.profile_name} --skills product-team-memory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
