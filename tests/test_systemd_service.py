"""Tests for the local dry-run systemd unit installer."""

import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PROJECT_ROOT / "scripts" / "install_web_service.sh"


class TestWebServiceInstaller(unittest.TestCase):
    def test_dry_run_renders_local_project_paths_without_placeholders(self):
        result = subprocess.run(
            ["bash", str(INSTALLER), "--dry-run"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn(f"WorkingDirectory={PROJECT_ROOT}", result.stdout)
        self.assertIn(f"ExecStart={PROJECT_ROOT}/.venv/bin/auto-zoom-web", result.stdout)
        self.assertIn("ProtectSystem=strict", result.stdout)
        self.assertNotIn("@PROJECT_DIR@", result.stdout)

    def test_help_documents_uninstall(self):
        result = subprocess.run(
            ["bash", str(INSTALLER), "--help"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("--uninstall", result.stdout)


if __name__ == "__main__":
    unittest.main()
