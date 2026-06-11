from __future__ import annotations

import subprocess
import sys
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


if __name__ == "__main__":
    unittest.main()
