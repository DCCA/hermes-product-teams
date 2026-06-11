from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USE_CASE_DOC = ROOT / "docs/use-case-validation.md"


class UseCaseValidationTests(unittest.TestCase):
    def test_use_case_validation_matrix_exists_with_core_cases(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        required_cases = [
            "Customer feedback thread",
            "User interview notes",
            "Support ticket cluster",
            "Internal product decision discussion",
            "Product brainstorm",
            "Weekly synthesis from multiple inputs",
        ]
        for use_case in required_cases:
            self.assertIn(use_case, content)

    def test_each_core_use_case_has_acceptance_criteria_and_fixture_status(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        required_fields = [
            "Target user:",
            "User job:",
            "Input fixture:",
            "Expected artifacts:",
            "Acceptance criteria:",
            "Current status:",
            "Next gap:",
        ]
        for field in required_fields:
            self.assertGreaterEqual(content.count(field), 6, field)

    def test_use_case_validation_preserves_prd_direction_boundaries(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        required_guardrails = [
            "source-linked evidence",
            "facts from assumptions",
            "PRD update proposals",
            "not silently edit PRD.md",
            "not roadmap management",
            "not user research operations",
        ]
        for guardrail in required_guardrails:
            self.assertIn(guardrail, content)

    def test_user_interview_fixture_exists_with_interview_specific_content(self) -> None:
        fixture = (ROOT / "examples/inputs/002-user-interview-notes.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "# User Interview Notes",
            "Interviewee:",
            "Role:",
            "Direct quotes",
            "Pain points",
            "Current workflow",
            "Follow-up questions",
            "PRD implications",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, fixture)

    def test_user_interview_use_case_is_marked_partially_validated(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "Input fixture: `examples/inputs/002-user-interview-notes.md`", content
        )
        self.assertIn("User interview notes: Partially validated with one fixture.", content)
        self.assertIn("Current status: Partially validated with a realistic input fixture.", content)
        self.assertIn("Next gap: Add interview-specific extraction tests", content)


if __name__ == "__main__":
    unittest.main()
