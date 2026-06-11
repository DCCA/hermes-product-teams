from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "hermes" / "profile"


class AgentProfileTests(unittest.TestCase):
    def test_profile_package_contains_required_runtime_files(self) -> None:
        required_files = [
            "distribution.yaml",
            "README.md",
            "SOUL.md",
            "config.example.yaml",
            "workflows/capture-input.md",
            "workflows/weekly-brief.md",
            "workflows/review-prd-proposals.md",
            "workspace.example.yaml",
        ]
        for relative_path in required_files:
            self.assertTrue((PROFILE / relative_path).exists(), relative_path)

    def test_profile_soul_defines_actual_agent_behavior(self) -> None:
        soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")

        required_phrases = [
            "Hermes Product Teams",
            "Discovery + Living Docs Agent",
            "source-linked evidence",
            "facts from assumptions",
            "PRD update proposals",
            "human approval",
            "never silently edit source-of-truth docs",
            "do not create tickets, send stakeholder messages, or change external systems",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, soul)

    def test_profile_install_script_copies_profile_and_skill_without_credentials(self) -> None:
        script = ROOT / "scripts" / "install_profile.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir) / "hermes-home"
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--hermes-home",
                    str(hermes_home),
                    "--workspace",
                    str(ROOT / "examples" / "workspace"),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            profile_root = hermes_home / "profiles" / "product-teams"
            self.assertTrue((profile_root / "config.yaml").exists())
            self.assertTrue((profile_root / "SOUL.md").exists())
            self.assertTrue((profile_root / "distribution.yaml").exists())
            self.assertFalse((profile_root / "system.md").exists())
            self.assertTrue((profile_root / "workflows" / "capture-input.md").exists())
            self.assertTrue(
                (profile_root / "skills" / "product-team-memory" / "SKILL.md").exists()
            )

            config = (profile_root / "config.yaml").read_text(encoding="utf-8")
            self.assertIn(str(ROOT / "examples" / "workspace"), config)
            self.assertNotIn("API_KEY", config)
            self.assertNotIn("token:", config.lower())

    def test_capture_command_builder_outputs_real_hermes_command(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_agent_capture.py",
                "--input",
                "examples/inputs/001-customer-feedback-thread.md",
                "--workspace",
                "examples/workspace",
                "--dry-run",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("hermes chat", result.stdout)
        self.assertIn("--profile product-teams", result.stdout)
        self.assertIn("product-team-memory", result.stdout)
        self.assertIn("examples/inputs/001-customer-feedback-thread.md", result.stdout)
        self.assertIn("examples/workspace", result.stdout)

    def test_weekly_brief_command_builder_outputs_real_hermes_command(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_weekly_brief.py",
                "--workspace",
                "examples/workspace",
                "--dry-run",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("hermes chat", result.stdout)
        self.assertIn("--profile product-teams", result.stdout)
        self.assertIn("product-team-memory", result.stdout)
        self.assertIn("examples/workspace", result.stdout)
        self.assertIn("weekly-brief.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
