from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SYNTHETIC_PRD = """# PRD

## Activation requirements

Show an activation checklist and onboarding status panel so customers complete
setup after connecting their first datasource.

## Billing

Invoices use quarterly proration with ledger reconciliation.
"""

MATCHING_NOTE = """# Activation feedback

Summary: Customers stall during onboarding because the activation checklist and
status panel do not show setup progress after connecting a datasource.

## Facts

- The activation checklist confuses customers during onboarding setup.
- The status panel hides datasource connection progress.
"""

UNRELATED_NOTE = """# Mobile dark mode request

Summary: Beta testers requested dark mode theming on the mobile app.

## Facts

- Testers dislike bright screens at night.
- Theming toggles were mentioned twice.
"""


def build_synthetic_workspace(base: Path) -> Path:
    workspace = base / "workspace"
    notes_dir = workspace / "Discovery Notes"
    notes_dir.mkdir(parents=True)
    (workspace / "PRD.md").write_text(SYNTHETIC_PRD, encoding="utf-8")
    (notes_dir / "010-activation-feedback.generated.md").write_text(MATCHING_NOTE, encoding="utf-8")
    (notes_dir / "011-dark-mode.generated.md").write_text(UNRELATED_NOTE, encoding="utf-8")
    return workspace


def run_report(*extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/report_prd_touchpoints.py", *extra_args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


class PrdTouchpointReportTests(unittest.TestCase):
    def test_report_runs_against_committed_workspace(self) -> None:
        result = run_report()

        self.assertEqual(result.returncode, 0)
        self.assertIn("# PRD touchpoint report", result.stdout)
        self.assertIn("## 001-customer-feedback-thread.generated.md", result.stdout)
        self.assertIn("shared terms:", result.stdout)
        self.assertIn("Summary:", result.stdout)
        self.assertIn("discovery notes touch the PRD", result.stdout)
        self.assertIn("have no PRD touchpoint", result.stdout)

    def test_synthetic_workspace_reports_match_and_staleness_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = build_synthetic_workspace(Path(tmpdir))
            result = run_report("--workspace", str(workspace))

        lines = result.stdout.splitlines()
        self.assertIn("## 010-activation-feedback.generated.md", lines)
        match_index = lines.index("## 010-activation-feedback.generated.md")
        match_line = lines[match_index + 1]
        self.assertIn("Activation requirements", match_line)
        self.assertIn("shared terms:", match_line)
        for term in ("activation", "checklist", "onboarding"):
            self.assertIn(term, match_line)

        self.assertIn("## 011-dark-mode.generated.md", lines)
        unrelated_index = lines.index("## 011-dark-mode.generated.md")
        self.assertIn("No PRD touchpoint found", lines[unrelated_index + 1])

        self.assertIn(
            "Summary: 1 of 2 discovery notes touch the PRD; 1 have no PRD touchpoint.",
            result.stdout,
        )

    def test_output_flag_writes_report_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "reports" / "prd-touchpoints.md"
            result = run_report("--output", str(output_path))

            self.assertTrue(output_path.exists())
            written = output_path.read_text(encoding="utf-8")

        self.assertIn("# PRD touchpoint report", written)
        self.assertEqual(result.stdout.strip(), written.strip())


if __name__ == "__main__":
    unittest.main()
