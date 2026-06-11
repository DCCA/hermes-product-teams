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
    "hermes/skills/product-team-memory/SKILL.md",
    "hermes/prompts/capture.md",
    "hermes/prompts/weekly-brief.md",
    "examples/workspace/Product Brief.md",
    "examples/workspace/Customer Insights.md",
    "examples/workspace/Decision Log.md",
    "examples/workspace/Open Questions.md",
    "examples/workspace/PRD.md",
    "examples/inputs/001-customer-feedback-thread.md",
    "scripts/check_scaffold.py",
    "scripts/run_capture_demo.py",
    "tests/test_prd_direction.py",
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
