#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_SOURCE = ROOT / "hermes" / "profile"
SKILL_SOURCE = ROOT / "hermes" / "skills" / "product-team-memory"
SCRIPT_SOURCES = [
    ROOT / "scripts" / "run_agent_capture.py",
    ROOT / "scripts" / "run_weekly_brief.py",
]
DEFAULT_PROFILE_NAME = "product-teams"


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
        default=DEFAULT_PROFILE_NAME,
        help="Hermes profile name to create. Defaults to product-teams.",
    )
    args = parser.parse_args()

    profile_root = install_profile(args.hermes_home, args.workspace, args.profile_name)
    print(f"Installed Hermes Product Teams profile: {profile_root}")
    print(f"Workspace: {args.workspace.resolve()}")
    print(f"Run capture: python3 {profile_root / 'scripts' / 'run_agent_capture.py'} --input /path/to/input.md")
    print(f"Run weekly brief: python3 {profile_root / 'scripts' / 'run_weekly_brief.py'}")
    print(f"Or run: hermes chat --profile {args.profile_name} --skills product-team-memory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
