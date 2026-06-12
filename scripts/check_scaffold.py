#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "docs/concept.md",
    "docs/market-validation.md",
    "docs/mvp-plan.md",
    "docs/prd-direction.md",
    "docs/use-case-validation.md",
    "docs/user-test-guide.md",
    "hermes/skills/product-team-memory/SKILL.md",
    "hermes/prompts/capture.md",
    "hermes/prompts/weekly-brief.md",
    "hermes/profile/README.md",
    "hermes/profile/SOUL.md",
    "hermes/profile/config.example.yaml",
    "hermes/profile/distribution.yaml",
    "hermes/profile/workspace.example.yaml",
    "hermes/profile/workflows/capture-input.md",
    "hermes/profile/workflows/weekly-brief.md",
    "hermes/profile/workflows/review-prd-proposals.md",
    "examples/workspace/Product Brief.md",
    "examples/workspace/Customer Insights.md",
    "examples/workspace/Decision Log.md",
    "examples/workspace/Open Questions.md",
    "examples/workspace/PRD.md",
    "examples/inputs/001-customer-feedback-thread.md",
    "examples/inputs/002-user-interview-notes.md",
    "scripts/check_scaffold.py",
    "scripts/install_profile.py",
    "scripts/run_agent_capture.py",
    "scripts/run_weekly_brief.py",
    "scripts/run_capture_demo.py",
    "tests/__init__.py",
    "tests/test_agent_profile.py",
    "tests/test_input_classification.py",
    "tests/test_prd_direction.py",
    "tests/test_use_case_validation.py",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        print("Missing required files:")
        for path in missing:
            print(f"- {path}")
        return 1

    skill = (ROOT / "hermes/skills/product-team-memory/SKILL.md").read_text()
    if not skill.startswith("---") or "name: product-team-memory" not in skill:
        print("Skill frontmatter check failed")
        return 1

    print(f"OK: {len(REQUIRED_FILES)} required files present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
