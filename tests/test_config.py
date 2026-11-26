import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stub import config
from stub.models import Paths, StubError


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_missing_config_defaults_to_home_learnings(self):
        paths = config.load_config(self.root / "missing.toml")
        self.assertEqual(paths.learnings, Path.home() / "Learnings")
        self.assertIsNone(paths.vault)

    def test_save_and_load_round_trip(self):
        target = self.root / "config.toml"
        expected = Paths(learnings=self.root / "Learnings", vault=self.root / "Vault")
        config.save_config(expected, target)
        self.assertEqual(config.load_config(target), expected)

    def test_update_config_changes_only_the_given_key(self):
        target = self.root / "config.toml"
        original = Paths(learnings=self.root / "Learnings", vault=self.root / "Vault")
        config.save_config(original, target)
        new_vault = self.root / "OtherVault"
        with patch.dict(os.environ, {"STUB_CONFIG": str(target)}):
            updated = config.update_config(vault=str(new_vault))
        self.assertEqual(updated.learnings, original.learnings)
        self.assertEqual(updated.vault, new_vault)
        self.assertIn(str(new_vault), target.read_text())

    def test_invalid_toml_raises_stub_error(self):
        bad = self.root / "bad.toml"
        bad.write_text("[paths\n", encoding="utf-8")
        with self.assertRaises(StubError):
            config.load_config(bad)


if __name__ == "__main__":
    unittest.main()
