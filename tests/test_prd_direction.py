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

    def test_support_ticket_capture_demo_generates_severity_and_confidence_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_capture_demo.py",
                    "--input",
                    "examples/inputs/003-support-ticket-cluster.md",
                    "--workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            discovery = (workspace / "Discovery Notes" / "003-support-ticket-cluster.generated.md").read_text(
                encoding="utf-8"
            )
            insights = (workspace / "Customer Insights.md").read_text(encoding="utf-8")
            decision_log = (workspace / "Decision Log.md").read_text(encoding="utf-8")
            questions = (workspace / "Open Questions.md").read_text(encoding="utf-8")
            proposal = (workspace / "PRD Update Proposals.md").read_text(encoding="utf-8")
            brief = (workspace / "Weekly Briefs" / "weekly-brief-2026-06-11.generated.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Type: Support Ticket Cluster", discovery)
            self.assertIn("Severity: High", discovery)
            self.assertIn("Confidence: Medium", discovery)
            self.assertIn("## Repeated issue pattern", discovery)
            self.assertIn("## Support impact", discovery)
            self.assertIn("same export timeout issue", insights)
            self.assertIn("triage export performance before adding more export formats", decision_log)
            self.assertIn("What percentage of CSV exports time out", questions)
            self.assertIn("Status: Proposed, not applied to `PRD.md`.", proposal)
            self.assertIn("Severity/confidence", brief)

    def test_internal_decision_capture_demo_generates_decision_specific_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_capture_demo.py",
                    "--input",
                    "examples/inputs/004-internal-decision-discussion.md",
                    "--workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            discovery = (workspace / "Discovery Notes" / "004-internal-decision-discussion.generated.md").read_text(
                encoding="utf-8"
            )
            decision_log = (workspace / "Decision Log.md").read_text(encoding="utf-8")
            questions = (workspace / "Open Questions.md").read_text(encoding="utf-8")
            proposal = (workspace / "PRD Update Proposals.md").read_text(encoding="utf-8")
            brief = (workspace / "Weekly Briefs" / "weekly-brief-2026-06-12.generated.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Type: Internal Product Decision Discussion", discovery)
            self.assertIn("Decision status: Proposed", discovery)
            self.assertIn("## Options considered", discovery)
            self.assertIn("## Risks", discovery)
            self.assertIn("## Reversibility", discovery)
            self.assertIn("Decision: Proposed — standardize on PRD proposal review before implementation starts.", decision_log)
            self.assertIn("What evidence threshold should trigger a PRD proposal", questions)
            self.assertIn("Status: Proposed, not applied to `PRD.md`.", proposal)
            self.assertIn("decisions pending", brief.lower())

    def test_product_brainstorm_capture_demo_generates_assumption_and_non_goal_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_capture_demo.py",
                    "--input",
                    "examples/inputs/005-product-brainstorm.md",
                    "--workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            discovery = (workspace / "Discovery Notes" / "005-product-brainstorm.generated.md").read_text(
                encoding="utf-8"
            )
            insights = (workspace / "Customer Insights.md").read_text(encoding="utf-8")
            decision_log = (workspace / "Decision Log.md").read_text(encoding="utf-8")
            questions = (workspace / "Open Questions.md").read_text(encoding="utf-8")
            proposal = (workspace / "PRD Update Proposals.md").read_text(encoding="utf-8")
            brief = (workspace / "Weekly Briefs" / "weekly-brief-2026-06-13.generated.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Type: Product Brainstorm", discovery)
            self.assertIn("## Raw ideas", discovery)
            self.assertIn("## Assumptions", discovery)
            self.assertIn("## Hypotheses", discovery)
            self.assertIn("## Non-goals", discovery)
            self.assertIn("## Risks", discovery)
            self.assertNotIn("## Facts", discovery)
            self.assertIn("structured customer recap", insights)
            self.assertIn("Decision: Pending — validate whether AI-generated customer recap should be the first brainstorm theme to prototype.", decision_log)
            self.assertIn("What evidence would prove founders will reuse a generated customer recap each week?", questions)
            self.assertIn("No PRD proposal generated yet", proposal)
            self.assertIn("evidence threshold", proposal)
            self.assertIn("## Potential product implications", brief)
            self.assertNotIn("## PRD/spec changes proposed", brief)
            self.assertIn("ideas are still hypotheses", brief.lower())


if __name__ == "__main__":
    unittest.main()
