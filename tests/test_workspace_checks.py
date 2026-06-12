from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = ROOT / "scripts" / "run_capture_demo.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_workspace.py"
INPUTS = sorted((ROOT / "examples" / "inputs").glob("*.md"))


def run_demo(input_path: Path, workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DEMO_SCRIPT), "--input", str(input_path), "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )


def run_linter(workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--workspace", str(workspace)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class WorkspaceChecksTests(unittest.TestCase):
    def test_generated_workspace_passes_trust_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            for input_path in INPUTS:
                run_demo(input_path, workspace)

            result = run_linter(workspace)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK:", result.stdout)

    def test_stripped_source_lines_fail_with_named_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            run_demo(INPUTS[0], workspace)

            note = workspace / "Discovery Notes" / f"{INPUTS[0].stem}.generated.md"
            stripped = re.sub(r"^Source:.*\n", "", note.read_text(encoding="utf-8"), flags=re.MULTILINE)
            note.write_text(stripped, encoding="utf-8")

            result = run_linter(workspace)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(note.name, result.stdout)
            self.assertIn("Source:", result.stdout)

    def test_committed_workspace_passes_trust_checks(self) -> None:
        result = run_linter(ROOT / "examples" / "workspace")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK:", result.stdout)


if __name__ == "__main__":
    unittest.main()
