from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "examples" / "inputs"


def load_capture_module():
    spec = importlib.util.spec_from_file_location(
        "run_agent_capture", ROOT / "scripts" / "run_agent_capture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPTURE = load_capture_module()


class InputClassificationTests(unittest.TestCase):
    def test_customer_feedback_fixture_is_classified_canonically(self) -> None:
        self.assertEqual(
            CAPTURE.classify_input(INPUTS / "001-customer-feedback-thread.md"),
            "Customer Feedback / Roadmap Signal",
        )

    def test_user_interview_fixture_is_classified_canonically(self) -> None:
        self.assertEqual(
            CAPTURE.classify_input(INPUTS / "002-user-interview-notes.md"),
            "User Interview",
        )

    def test_support_ticket_fixture_is_classified_canonically(self) -> None:
        self.assertEqual(
            CAPTURE.classify_input(INPUTS / "003-support-ticket-cluster.md"),
            "Support Ticket Cluster",
        )

    def test_internal_decision_fixture_is_classified_canonically(self) -> None:
        self.assertEqual(
            CAPTURE.classify_input(INPUTS / "004-internal-decision-discussion.md"),
            "Internal Product Decision Discussion",
        )

    def test_product_brainstorm_fixture_is_classified_canonically(self) -> None:
        self.assertEqual(
            CAPTURE.classify_input(INPUTS / "005-product-brainstorm.md"),
            "Product Brainstorm",
        )

    def test_generic_snippet_falls_back_to_product_team_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            generic = Path(tmpdir) / "random-note.md"
            generic.write_text(
                "# Random note\n\nWe talked about lunch options and office plants.\n",
                encoding="utf-8",
            )
            self.assertEqual(CAPTURE.classify_input(generic), "Product-Team Input")


if __name__ == "__main__":
    unittest.main()
