#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_WORKSPACE = ROOT / "examples" / "workspace"
CASES_PATH = ROOT / "examples" / "evals" / "cases.json"
GENERATED_BLOCK_DOCS = [
    "Customer Insights.md",
    "Decision Log.md",
    "Open Questions.md",
    "PRD Update Proposals.md",
]
GENERATED_BLOCK_PATTERN = re.compile(
    r"<!-- generated:(?P<marker>[^>]+?):start -->\n(?P<body>.*?)<!-- generated:(?P=marker):end -->\n?",
    re.DOTALL,
)
SPECULATIVE_HEADINGS = {
    "Assumptions",
    "Assumptions to validate",
    "Hypotheses",
    "Likely root causes",
    "Risks",
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import install_profile  # type: ignore
import run_agent_capture  # type: ignore
import run_weekly_brief  # type: ignore


@dataclass
class CaseSpec:
    id: str
    input: str
    expected_type: str
    required_note_strings: list[str]


@dataclass
class CaseResult:
    case_id: str
    input_path: str
    command_ok: bool
    note_created: bool
    expected_type_found: bool
    source_line_found: bool
    evidence_section_found: bool
    speculative_section_found: bool
    required_note_strings_found: list[str]
    required_note_strings_missing: list[str]
    workspace_docs_touched: list[str]
    score: int
    stdout_tail: str
    stderr_tail: str
    note_path: str | None = None


@dataclass
class HarnessResult:
    profile_name: str
    hermes_home: str
    workspace: str
    model: str | None
    provider: str | None
    prompt_suffix: str | None
    cases_passed: int
    total_cases: int
    weekly_brief_ok: bool
    workspace_check_ok: bool
    overall_score: int
    weekly_brief_path: str | None
    workspace_check_stdout: str
    workspace_check_stderr: str
    cases: list[CaseResult]


def tail(text: str, lines: int = 20) -> str:
    parts = text.strip().splitlines()
    if not parts:
        return ""
    return "\n".join(parts[-lines:])


def load_cases(path: Path) -> list[CaseSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [CaseSpec(**item) for item in raw]


def clone_workspace_template(destination: Path) -> None:
    shutil.copytree(EXAMPLE_WORKSPACE, destination)

    discovery_dir = destination / "Discovery Notes"
    if discovery_dir.exists():
        for note in discovery_dir.glob("*.generated.md"):
            note.unlink()

    briefs_dir = destination / "Weekly Briefs"
    if briefs_dir.exists():
        for brief in briefs_dir.glob("*.generated.md"):
            brief.unlink()

    for name in GENERATED_BLOCK_DOCS:
        doc = destination / name
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        cleaned = GENERATED_BLOCK_PATTERN.sub("", text)
        doc.write_text(cleaned.rstrip() + "\n", encoding="utf-8")


def seed_runtime_config(hermes_home: Path, source_home: Path | None = None) -> None:
    source = source_home or (Path.home() / ".hermes")
    hermes_home.mkdir(parents=True, exist_ok=True)
    for name in ["config.yaml", ".env", "auth.json"]:
        src = source / name
        dst = hermes_home / name
        if src.exists():
            shutil.copy2(src, dst)


def resolve_model_provider_from_home(hermes_home: Path) -> tuple[str | None, str | None]:
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return None, None

    text = config_path.read_text(encoding="utf-8")
    model_match = re.search(r"^model:\n(?:^[ \t].*\n)*?^[ \t]+default:\s*([^\n]+)$", text, flags=re.MULTILINE)
    provider_match = re.search(r"^model:\n(?:^[ \t].*\n)*?^[ \t]+provider:\s*([^\n]+)$", text, flags=re.MULTILINE)
    model = model_match.group(1).strip().strip('"\'') if model_match else None
    provider = provider_match.group(1).strip().strip('"\'') if provider_match else None
    return model or None, provider or None


def build_capture_command(
    input_path: Path,
    workspace: Path,
    profile_name: str,
    model: str | None,
    provider: str | None,
    prompt_suffix: str | None,
) -> list[str]:
    workflow_path = run_agent_capture.resolve_workflow_path()
    prompt = run_agent_capture.build_prompt(input_path, workspace, workflow_path)
    if prompt_suffix:
        prompt = f"{prompt}\n\nAdditional eval instruction:\n{prompt_suffix.strip()}"

    command = ["hermes", "chat", "-Q", "--profile", profile_name]
    if provider:
        command.extend(["--provider", provider])
    if model:
        command.extend(["--model", model])
    command.extend(["--skills", "product-team-memory", "-q", prompt])
    return command


def build_weekly_brief_command(
    workspace: Path,
    profile_name: str,
    model: str | None,
    provider: str | None,
    prompt_suffix: str | None,
) -> list[str]:
    workflow_path = run_weekly_brief.resolve_workflow_path()
    prompt = run_weekly_brief.build_prompt(workspace, workflow_path)
    if prompt_suffix:
        prompt = f"{prompt}\n\nAdditional eval instruction:\n{prompt_suffix.strip()}"

    command = ["hermes", "chat", "-Q", "--profile", profile_name]
    if provider:
        command.extend(["--provider", provider])
    if model:
        command.extend(["--model", model])
    command.extend(["--skills", "product-team-memory", "-q", prompt])
    return command


def run_subprocess(command: list[str], hermes_home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home)
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def note_has_expected_structure(note_text: str, expected_type: str) -> tuple[bool, bool, bool, bool]:
    expected_type_found = f"Type: {expected_type}" in note_text
    source_line_found = bool(re.search(r"^Source:\s*.+$", note_text, flags=re.MULTILINE))
    evidence_section_found = bool(
        re.search(r"^(##\s+Evidence\s*$|Evidence:\s*.+$)", note_text, flags=re.MULTILINE)
    )
    headings = set(re.findall(r"^##\s+(.+?)\s*$", note_text, flags=re.MULTILINE))
    speculative_field_found = bool(
        re.search(
            r"^(Assumptions:|Assumptions to validate:|Hypotheses:|Likely root causes:|Risks:)",
            note_text,
            flags=re.MULTILINE,
        )
    )
    speculative_section_found = bool(headings.intersection(SPECULATIVE_HEADINGS) or speculative_field_found)
    return expected_type_found, source_line_found, evidence_section_found, speculative_section_found


def touched_workspace_docs(workspace: Path, source_stem: str) -> list[str]:
    touched: list[str] = []
    for name in GENERATED_BLOCK_DOCS:
        doc = workspace / name
        if doc.exists() and source_stem in doc.read_text(encoding="utf-8"):
            touched.append(name)
    return touched


def score_case(result: CaseResult) -> int:
    checks = [
        result.command_ok,
        result.note_created,
        result.expected_type_found,
        result.source_line_found,
        result.evidence_section_found,
        result.speculative_section_found,
        len(result.workspace_docs_touched) >= 2,
        not result.required_note_strings_missing,
    ]
    return round(100 * (sum(1 for item in checks if item) / len(checks)))


def evaluate_case(
    case: CaseSpec,
    workspace: Path,
    hermes_home: Path,
    profile_name: str,
    model: str | None,
    provider: str | None,
    prompt_suffix: str | None,
) -> CaseResult:
    input_path = ROOT / case.input
    before_notes = set((workspace / "Discovery Notes").glob("*.md"))
    command = build_capture_command(input_path, workspace, profile_name, model, provider, prompt_suffix)
    completed = run_subprocess(command, hermes_home)
    after_notes = set((workspace / "Discovery Notes").glob("*.md"))
    new_notes = sorted(after_notes - before_notes)

    note_path = new_notes[0] if new_notes else None
    note_text = note_path.read_text(encoding="utf-8") if note_path else ""
    expected_type_found, source_line_found, evidence_section_found, speculative_section_found = (
        note_has_expected_structure(note_text, case.expected_type) if note_text else (False, False, False, False)
    )

    found_strings = [s for s in case.required_note_strings if s in note_text]
    missing_strings = [s for s in case.required_note_strings if s not in note_text]
    touched_docs = touched_workspace_docs(workspace, input_path.stem)

    result = CaseResult(
        case_id=case.id,
        input_path=str(input_path),
        command_ok=completed.returncode == 0,
        note_created=note_path is not None,
        expected_type_found=expected_type_found,
        source_line_found=source_line_found,
        evidence_section_found=evidence_section_found,
        speculative_section_found=speculative_section_found,
        required_note_strings_found=found_strings,
        required_note_strings_missing=missing_strings,
        workspace_docs_touched=touched_docs,
        stdout_tail=tail(completed.stdout),
        stderr_tail=tail(completed.stderr),
        note_path=str(note_path) if note_path else None,
        score=0,
    )
    result.score = score_case(result)
    return result


def run_weekly_brief_eval(
    workspace: Path,
    hermes_home: Path,
    profile_name: str,
    model: str | None,
    provider: str | None,
    prompt_suffix: str | None,
) -> tuple[bool, str | None, subprocess.CompletedProcess[str]]:
    before = set((workspace / "Weekly Briefs").glob("*.md"))
    command = build_weekly_brief_command(workspace, profile_name, model, provider, prompt_suffix)
    completed = run_subprocess(command, hermes_home)
    after = set((workspace / "Weekly Briefs").glob("*.md"))
    new_files = sorted(after - before)
    return completed.returncode == 0 and bool(new_files), str(new_files[0]) if new_files else None, completed


def run_workspace_check(workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_workspace.py"), "--workspace", str(workspace)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def install_eval_profile(hermes_home: Path, workspace: Path, profile_name: str) -> Path:
    return install_profile.install_profile(hermes_home, workspace, profile_name)


def format_markdown_report(result: HarnessResult) -> str:
    lines = [
        "# Hermes Product Teams Eval Harness Report",
        "",
        f"- Profile: `{result.profile_name}`",
        f"- Hermes home: `{result.hermes_home}`",
        f"- Workspace: `{result.workspace}`",
        f"- Model override: `{result.model or 'profile default'}`",
        f"- Provider override: `{result.provider or 'profile default'}`",
        f"- Cases passed: **{result.cases_passed}/{result.total_cases}**",
        f"- Overall score: **{result.overall_score}**",
        f"- Weekly brief: {'PASS' if result.weekly_brief_ok else 'FAIL'}",
        f"- Workspace trust checks: {'PASS' if result.workspace_check_ok else 'FAIL'}",
        "",
        "## Case results",
        "",
    ]
    for case in result.cases:
        lines.extend(
            [
                f"### {case.case_id}",
                f"- Score: **{case.score}**",
                f"- Command: {'PASS' if case.command_ok else 'FAIL'}",
                f"- Note created: {'PASS' if case.note_created else 'FAIL'}",
                f"- Expected type: {'PASS' if case.expected_type_found else 'FAIL'}",
                f"- Source line: {'PASS' if case.source_line_found else 'FAIL'}",
                f"- Evidence section: {'PASS' if case.evidence_section_found else 'FAIL'}",
                f"- Speculative section: {'PASS' if case.speculative_section_found else 'FAIL'}",
                f"- Workspace docs touched: {', '.join(case.workspace_docs_touched) if case.workspace_docs_touched else 'none'}",
                f"- Missing required strings: {', '.join(case.required_note_strings_missing) if case.required_note_strings_missing else 'none'}",
                f"- Note path: `{case.note_path or 'none'}`",
            ]
        )
        if not case.command_ok:
            if case.stdout_tail.strip():
                lines.extend([
                    "- Command stdout tail:",
                    "",
                    "```text",
                    case.stdout_tail.strip(),
                    "```",
                ])
            if case.stderr_tail.strip():
                lines.extend([
                    "- Command stderr tail:",
                    "",
                    "```text",
                    case.stderr_tail.strip(),
                    "```",
                ])
        lines.append("")
    lines.extend(
        [
            "## Workspace check stdout",
            "",
            "```text",
            result.workspace_check_stdout.strip(),
            "```",
        ]
    )
    if result.workspace_check_stderr.strip():
        lines.extend([
            "",
            "## Workspace check stderr",
            "",
            "```text",
            result.workspace_check_stderr.strip(),
            "```",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a simple Hermes Product Teams AI eval harness.")
    parser.add_argument("--cases", type=Path, default=CASES_PATH, help="Path to eval case JSON.")
    parser.add_argument("--profile-name", default="product-teams-eval", help="Temporary Hermes profile name.")
    parser.add_argument("--model", help="Optional Hermes model override.")
    parser.add_argument("--provider", help="Optional Hermes provider override.")
    parser.add_argument(
        "--prompt-suffix",
        help="Optional extra instruction appended to every eval prompt, useful for prompt experiments.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save a Markdown report.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary Hermes home and workspace instead of deleting them.",
    )
    parser.add_argument(
        "--isolated-hermes-home",
        action="store_true",
        help="Use a temporary Hermes home copied from ~/.hermes instead of the live Hermes home.",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)

    tmpdir_obj = tempfile.TemporaryDirectory(prefix="hpt-eval-")
    tmpdir = Path(tmpdir_obj.name)
    workspace = tmpdir / "workspace"
    hermes_home = (tmpdir / "hermes-home") if args.isolated_hermes_home else (Path.home() / ".hermes")

    try:
        clone_workspace_template(workspace)
        if args.isolated_hermes_home:
            seed_runtime_config(hermes_home)
        install_eval_profile(hermes_home, workspace, args.profile_name)
        default_model, default_provider = resolve_model_provider_from_home(hermes_home)
        effective_model = args.model or default_model
        effective_provider = args.provider or default_provider

        results: list[CaseResult] = []
        for case in cases:
            results.append(
                evaluate_case(
                    case=case,
                    workspace=workspace,
                    hermes_home=hermes_home,
                    profile_name=args.profile_name,
                    model=effective_model,
                    provider=effective_provider,
                    prompt_suffix=args.prompt_suffix,
                )
            )

        weekly_ok, weekly_path, weekly_completed = run_weekly_brief_eval(
            workspace=workspace,
            hermes_home=hermes_home,
            profile_name=args.profile_name,
            model=effective_model,
            provider=effective_provider,
            prompt_suffix=args.prompt_suffix,
        )
        workspace_check = run_workspace_check(workspace)
        workspace_check_ok = workspace_check.returncode == 0

        case_scores = [case.score for case in results]
        overall_score = round(
            (
                sum(case_scores)
                + (100 if weekly_ok else 0)
                + (100 if workspace_check_ok else 0)
            )
            / (len(case_scores) + 2)
        )
        passed = sum(1 for case in results if case.score == 100)

        harness_result = HarnessResult(
            profile_name=args.profile_name,
            hermes_home=str(hermes_home),
            workspace=str(workspace),
            model=effective_model,
            provider=effective_provider,
            prompt_suffix=args.prompt_suffix,
            cases_passed=passed,
            total_cases=len(results),
            weekly_brief_ok=weekly_ok,
            workspace_check_ok=workspace_check_ok,
            overall_score=overall_score,
            weekly_brief_path=weekly_path,
            workspace_check_stdout=workspace_check.stdout,
            workspace_check_stderr=workspace_check.stderr,
            cases=results,
        )

        print(json.dumps(asdict(harness_result), indent=2))
        if weekly_completed.stdout.strip():
            print("\n# weekly-brief stdout\n")
            print(weekly_completed.stdout.strip())
        if weekly_completed.stderr.strip():
            print("\n# weekly-brief stderr\n", file=sys.stderr)
            print(weekly_completed.stderr.strip(), file=sys.stderr)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(format_markdown_report(harness_result), encoding="utf-8")
            print(f"\nSaved report: {args.output}")

        if args.keep_temp:
            print(f"\nKept temp workspace at: {workspace}")
            print(f"Kept temp Hermes home at: {hermes_home}")
            tmpdir_obj.cleanup = lambda: None  # type: ignore[attr-defined]
        return 0 if workspace_check_ok and weekly_ok and passed == len(results) else 1
    finally:
        if args.keep_temp:
            pass
        else:
            tmpdir_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
