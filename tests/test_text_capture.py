from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_agent_capture.py"

PASTED_TEXT = (
    "Slack thread from #customer-feedback: exports keep timing out for weekly reports, "
    "two customers asked for retry guidance."
)


def run_capture(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        input=input_text,
    )


class TextCaptureTests(unittest.TestCase):
    def test_text_flag_dry_run_prints_command_with_pasted_content(self) -> None:
        result = run_capture(
            ["--text", PASTED_TEXT, "--workspace", "examples/workspace", "--dry-run"]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hermes chat", result.stdout)
        self.assertIn("--profile product-teams", result.stdout)
        self.assertIn(PASTED_TEXT, result.stdout)
        self.assertIn("Input source: pasted text", result.stdout)
        self.assertIn("BEGIN PASTED INPUT", result.stdout)
        self.assertIn("END PASTED INPUT", result.stdout)
        self.assertIn("examples/workspace", result.stdout)
        self.assertIn("User-pasted text", result.stdout)

    def test_stdin_dry_run_prints_command_with_piped_content(self) -> None:
        result = run_capture(
            ["--workspace", "examples/workspace", "--dry-run"],
            input_text=PASTED_TEXT + "\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hermes chat", result.stdout)
        self.assertIn(PASTED_TEXT, result.stdout)
        self.assertIn("Input source: pasted text", result.stdout)

    def test_stdin_interview_content_is_classified_as_user_interview(self) -> None:
        interview_text = (
            ROOT / "examples" / "inputs" / "002-user-interview-notes.md"
        ).read_text(encoding="utf-8")
        result = run_capture(
            ["--workspace", "examples/workspace", "--dry-run"],
            input_text=interview_text,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Detected input class: User Interview", result.stdout)
        self.assertIn("Interviewee role:", result.stdout)

    def test_input_and_text_together_fail(self) -> None:
        result = run_capture(
            [
                "--input",
                "examples/inputs/001-customer-feedback-thread.md",
                "--text",
                PASTED_TEXT,
                "--dry-run",
            ]
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--text", result.stderr)
        self.assertIn("--input", result.stderr)

    def test_empty_stdin_with_no_other_source_fails(self) -> None:
        result = run_capture(["--dry-run"], input_text="")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
