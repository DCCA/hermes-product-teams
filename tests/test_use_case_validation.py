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

    def test_internal_decision_fixture_exists_with_decision_specific_content(self) -> None:
        fixture = (ROOT / "examples/inputs/004-internal-decision-discussion.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "# Internal Product Decision Discussion",
            "Decision status:",
            "Participants:",
            "Options considered",
            "Rationale",
            "Risks",
            "Reversibility",
            "Requirement implications",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, fixture)

    def test_internal_decision_use_case_is_marked_partially_validated(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "| Internal product decision discussion | Partially validated with one fixture. |", content
        )
        self.assertIn(
            "Input fixture: `examples/inputs/004-internal-decision-discussion.md`", content
        )
        self.assertIn(
            "Current status: Partially validated with a realistic internal-decision fixture plus deterministic artifact generation covered by `tests/test_prd_direction.py`.",
            content,
        )
        self.assertIn("Next gap: Add broader acceptance checks for decision quality", content)

    def test_product_brainstorm_fixture_exists_with_brainstorm_specific_content(self) -> None:
        fixture = (ROOT / "examples/inputs/005-product-brainstorm.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "# Product Brainstorm",
            "Participants:",
            "Raw idea cluster",
            "Assumptions",
            "Hypotheses",
            "Non-goals",
            "Risks",
            "Next actions",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, fixture)

    def test_product_brainstorm_use_case_is_marked_partially_validated(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "| Product brainstorm | Partially validated with one fixture. |", content
        )
        self.assertIn(
            "Input fixture: `examples/inputs/005-product-brainstorm.md`", content
        )
        self.assertIn(
            "Current status: Partially validated with a realistic brainstorm fixture plus deterministic artifact generation covered by `tests/test_prd_direction.py`.",
            content,
        )
        self.assertIn(
            "Next gap: Add broader acceptance checks for idea-quality and evidence thresholds",
            content,
        )

    def test_weekly_synthesis_use_case_is_marked_partially_validated(self) -> None:
        content = USE_CASE_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "| Weekly synthesis from multiple inputs | Partially validated with one deterministic multi-input demo. |",
            content,
        )
        self.assertIn(
            "Input fixture: `examples/inputs/001-customer-feedback-thread.md`, `examples/inputs/002-user-interview-notes.md`, `examples/inputs/003-support-ticket-cluster.md`, `examples/inputs/004-internal-decision-discussion.md`, `examples/inputs/005-product-brainstorm.md`",
            content,
        )
        self.assertIn(
            "Current status: Partially validated with a deterministic multi-input synthesis demo covered by `tests/test_prd_direction.py`.",
            content,
        )
        self.assertIn(
            "Next gap: Generalize the synthesis beyond the current fixtures, add true aggregated shared-artifact updates beyond the weekly brief, and validate quality under conflicting or noisier weekly inputs.",
            content,
        )

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
