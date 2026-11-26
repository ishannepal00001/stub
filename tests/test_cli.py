import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from stub.cli import main
from stub.templates import BUNDLED_TEMPLATES


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "cwd").mkdir()
        (self.root / "Learnings").mkdir()
        (self.root / "Vault").mkdir()
        self.config = self.root / "config.toml"
        self.write_config(self.root / "Learnings", self.root / "Vault")

        env = patch.dict(
            os.environ,
            {
                "STUB_CONFIG": str(self.config),
                "STUB_TEMPLATES_DIR": str(BUNDLED_TEMPLATES),
            },
        )
        env.start()
        self.addCleanup(env.stop)

        self.previous_cwd = Path.cwd()
        os.chdir(self.root / "cwd")
        self.addCleanup(os.chdir, self.previous_cwd)

    def write_config(self, learnings, vault):
        self.config.write_text(
            f'[paths]\nlearnings = "{learnings}"\nvault = "{vault}"\n', encoding="utf-8"
        )

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_generate_with_learnings_and_symlink(self):
        code, _, error = self.run_cli(
            "generate", "template", "cpp", "-l", "-s", "-m", "Extra message"
        )
        self.assertEqual(code, 0, error)
        note = self.root / "Learnings" / "2026-11-26_cpp.md"
        code_file = self.root / "Learnings" / "2026-11-26_cpp.cpp"
        self.assertTrue(code_file.is_file())
        self.assertTrue(note.is_file())
        self.assertIn("// Extra message", code_file.read_text())
        self.assertIn("_Extra message_", note.read_text())
        link = self.root / "Vault" / "2026-11-26_cpp.md"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), note)

    def test_without_learnings_requires_name_and_skips_markdown(self):
        code, _, error = self.run_cli("generate", "template", "cpp")
        self.assertEqual(code, 1)
        self.assertIn("-n NAME", error)

        code, _, error = self.run_cli(
            "generate", "template", "cpp", "-n", "myname", "-m", "Extra message"
        )
        self.assertEqual(code, 0, error)
        self.assertTrue((self.root / "cwd" / "myname.cpp").is_file())
        self.assertEqual(list((self.root / "cwd").glob("*.md")), [])

    def test_symlink_requires_learnings(self):
        code, _, error = self.run_cli("generate", "template", "cpp", "-s")
        self.assertEqual(code, 1)
        self.assertIn("-s requires -l", error)

    def test_existing_file_is_not_overwritten(self):
        argv = ("generate", "template", "cpp", "-n", "myname")
        self.assertEqual(self.run_cli(*argv)[0], 0)
        code, _, error = self.run_cli(*argv)
        self.assertEqual(code, 1)
        self.assertIn("refusing to overwrite", error)

    def test_config_updates_only_the_given_key(self):
        new_vault = self.root / "OtherVault"
        code, _, error = self.run_cli("config", "--vault", str(new_vault))
        self.assertEqual(code, 0, error)
        saved = self.config.read_text()
        self.assertIn(str(new_vault), saved)
        self.assertIn(str(self.root / "Learnings"), saved)


if __name__ == "__main__":
    unittest.main()
