from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class PrdDirectionTests(unittest.TestCase):
    def test_prd_names_the_mvp_direction_and_non_goals(self) -> None:
        prd = read("examples/workspace/PRD.md")

        self.assertIn("Product Discovery Memory Agent", prd)
        self.assertIn("product team memory layer", prd)
        self.assertIn("not replace Productboard", prd)
        self.assertIn("not silently modify source-of-truth docs", prd)
        self.assertIn("source-linked evidence", prd)
        self.assertIn("PRD update proposals", prd)

    def test_direction_doc_aligns_with_prd_and_market_validation(self) -> None:
        direction = read("docs/prd-direction.md")
        market = read("docs/market-validation.md")

        required_phrases = [
            "Discovery + Living Docs Agent",
            "memory/discovery/docs layer",
            "permission-aware",
            "human approval",
            "not a roadmap management tool",
            "not a user research platform",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, direction)

        self.assertIn("knowledge/memory/discovery/docs layer", market)
        self.assertIn("memory/discovery/docs layer", direction)

    def test_capture_demo_outputs_remain_prd_direction_aligned(self) -> None:
        subprocess.run(
            [sys.executable, "scripts/run_capture_demo.py"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        proposal = read("examples/workspace/PRD Update Proposals.md")
        brief = read("examples/workspace/Weekly Briefs/weekly-brief-2026-06-10.generated.md")
        discovery = read("examples/workspace/Discovery Notes/001-customer-feedback-thread.generated.md")

        self.assertIn("Status: Proposed, not applied to `PRD.md`.", proposal)
        self.assertIn("Source: `examples/inputs/001-customer-feedback-thread.md`", proposal)
        self.assertIn("advanced analytics", proposal)
        self.assertIn("Sources reviewed", brief)
        self.assertIn("## Evidence", discovery)
        self.assertIn("## Assumptions", discovery)

    def test_interview_capture_demo_generates_interview_specific_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_capture_demo.py",
                    "--input",
                    "examples/inputs/002-user-interview-notes.md",
                    "--workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            discovery = (workspace / "Discovery Notes" / "002-user-interview-notes.generated.md").read_text(
                encoding="utf-8"
            )
            insights = (workspace / "Customer Insights.md").read_text(encoding="utf-8")
            decision_log = (workspace / "Decision Log.md").read_text(encoding="utf-8")
            questions = (workspace / "Open Questions.md").read_text(encoding="utf-8")
            proposal = (workspace / "PRD Update Proposals.md").read_text(encoding="utf-8")
            brief = (workspace / "Weekly Briefs" / "weekly-brief-2026-06-10.generated.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Type: User Interview", discovery)
            self.assertIn("Interviewee role: Head of Customer Success", discovery)
            self.assertIn("Segment: Mid-market customer-facing team lead", discovery)
            self.assertIn("## Goals", discovery)
            self.assertIn("## Assumptions to validate", discovery)
            self.assertIn("## Follow-up questions", discovery)
            self.assertIn("source-linked evidence", proposal)
            self.assertIn("PMs trust AI-generated discovery notes when direct quotes and source links are visible.", insights)
            self.assertIn("Who should approve proposed PRD/spec edits?", questions)
            self.assertIn("proposed PRD/spec edits with sources should be the default trust model", decision_log)
            self.assertIn("Which input source should be validated first", brief)


if __name__ == "__main__":
    unittest.main()
