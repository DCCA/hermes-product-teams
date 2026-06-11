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
            "| User interview notes | Partially validated with one fixture. |", content
        )
        self.assertIn(
            "Input fixture: `examples/inputs/002-user-interview-notes.md`", content
        )
        self.assertIn(
            "Current status: Partially validated with a realistic input fixture plus deterministic interview artifact generation covered by `tests/test_prd_direction.py`.",
            content,
        )
        self.assertIn("Next gap: Add broader acceptance checks for decision-log and weekly-brief quality", content)

    def test_support_ticket_fixture_exists_with_support_specific_content(self) -> None:
        fixture = (ROOT / "examples/inputs/003-support-ticket-cluster.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "# Support Ticket Cluster",
            "Affected segment:",
            "Severity:",
            "Confidence:",
            "Ticket summaries",
            "Repeated issue pattern",
            "Support impact",
            "Product follow-ups",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, fixture)

    def test_support_ticket_use_case_is_marked_partially_validated(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "| Support ticket cluster | Partially validated with one fixture. |", content
        )
        self.assertIn(
            "Input fixture: `examples/inputs/003-support-ticket-cluster.md`", content
        )
        self.assertIn(
            "Current status: Partially validated with a realistic support-cluster fixture plus deterministic artifact generation covered by `tests/test_prd_direction.py`.",
            content,
        )
        self.assertIn("Next gap: Add broader acceptance checks for decision/triage quality", content)

    def test_user_test_guide_exists_with_bounded_script_and_trust_checks(self) -> None:
        guide = (ROOT / "docs/user-test-guide.md").read_text(encoding="utf-8")

        required_sections = [
            "# User Test Guide",
            "## 5–10 minute test script",
            "## Success criteria",
            "## Observer checklist",
        ]
        for section in required_sections:
            self.assertIn(section, guide)

        required_checks = [
            "Discovery + Living Docs Agent",
            "source-linked evidence",
            "facts from assumptions",
            "PRD update proposal",
            "human approval",
            "must not merge, deploy, create issues, send messages, or change external systems",
        ]
        for check in required_checks:
            self.assertIn(check, guide)


if __name__ == "__main__":
    unittest.main()
